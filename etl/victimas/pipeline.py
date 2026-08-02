"""Conector Unidad de Víctimas (UARIV) - fuente de la fase 2 del plan.

Hallazgo (feb 2026): el CSV de datos abiertos de Datos Paz
(https://datospaz.unidadvictimas.gov.co/archivos/datosabiertos/hechosvictimizantes.csv)
devuelve 404 desde hace meses; Datos Paz hoy publica los reportes como Power BI
embebido, sin descarga CSV. La UARIV publica los mismos agregados en el portal
oficial de datos abiertos de Colombia (datos.gov.co): el dataset municipal
"Cifras de Víctimas por Hechos Municipal" (resource 9qih-4vkc), corte por corte,
cuyo total coincide con la cifra oficial de personas incluidas en el RUV
(9.572.942 a 31/12/2025). El conector usa ese resource y, si VICTIMAS_URL
alguna vez vuelve a responder, prefiere el CSV configurado.

Columna clave: per_sa = sujetos de atención (personas incluidas en el RUV,
acumulado a corte). La suma municipal del corte equivale al total nacional.
"""

from __future__ import annotations

import os
from datetime import datetime

import pandas as pd
import requests

from etl.common.cargar import insertar_serie, periodo_anual, slugificar, upsert_fuente, upsert_indicador
from etl.common.lineage import Lineage, hash_registro
from etl.common.pipeline import PipelineETL
from etl.common.validation import EsquemaSerieNormalizada, validar

# Resource Socrata oficial de la UARIV (datos.gov.co), verificado en vivo:
# corte 31/12/2025 -> sum(per_sa) = 9.572.942, que coincide con la cifra
# oficial de personas incluidas en el RUV (~9,5 millones).
SOCRATA_MUNICIPAL = "9qih-4vkc"
SOCRATA_BASE = "https://www.datos.gov.co/resource"

# Marcador de nivel nacional para la fila "SIN DEFINIR" del dataset municipal:
# personas incluidas en el RUV sin municipio de reporte definido (~1,04M a
# 31/12/2025). No existe en DIVIPOLA; se inserta con municipio_id NULL.
CODIGO_NACIONAL = "00000"

ALIASES = {
    "codigo": ["codigo_municipio", "cod_municipio", "cod_divipola", "codigomunicipio", "codigo_mun"],
    "anio": ["anio", "ano", "año", "year", "periodo"],
    "hecho": ["hecho", "tipo_hecho", "hecho_victimizante", "tipo", "modalidad"],
    "valor": ["casos", "victimas", "personas", "numero_casos", "cantidad"],
}


def _columna(df: pd.DataFrame, aliases: list[str], etiqueta: str) -> str:
    for alias in aliases:
        if alias in df.columns:
            return alias
    raise ValueError(f"No se encontró columna para {etiqueta} (buscadas: {aliases}). Revisar ficha docs/fuentes/victimas.md")


def _parsear_corte(valor) -> datetime:
    """Fecha de corte en formatos mixtos del dataset: '31/12/2025', '30/09/24',
    '2024/08/31' o '31/07/2024 00:00'."""
    texto = str(valor).strip().split()[0]
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y/%m/%d"):
        try:
            return datetime.strptime(texto, fmt)
        except ValueError:
            continue
    raise ValueError(f"Fecha de corte no reconocida: {valor}")


def _cortes_por_anio(resource_id: str) -> list[datetime]:
    """Último corte disponible de cada año (serie anual de acumulados RUV)."""
    url = f"{SOCRATA_BASE}/{resource_id}.json?$select=fecha_corte&$group=fecha_corte"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    por_anio: dict[int, datetime] = {}
    for fila in resp.json():
        corte = _parsear_corte(fila.get("fecha_corte"))
        por_anio[corte.year] = max(por_anio.get(corte.year, corte), corte)
    return [corte for _, corte in sorted(por_anio.items())]


class Victimas_Hechos(PipelineETL):
    pipeline_id = "victimas_hechos"
    tabla_raw = "victimas_hechos"

    def _descargar_csv(self, url_base: str) -> pd.DataFrame | None:
        url = f"{url_base.rstrip('/')}/hechos_victimizantes"
        resp = requests.get(url, timeout=60)
        if not resp.ok:
            return None
        return pd.DataFrame(resp.json())

    def _descargar_socrata(self, resource_id: str) -> tuple[pd.DataFrame, list[str], datetime]:
        """Agrega sujetos de atención (per_sa) por municipio y año de corte."""
        cortes = _cortes_por_anio(resource_id)
        if not cortes:
            raise RuntimeError(f"Sin cortes disponibles en resource {resource_id}")
        url_origen = f"{SOCRATA_BASE}/{resource_id}.json"
        frames = []
        for corte in cortes:
            fecha = corte.strftime("%d/%m/%Y")
            url = (
                f"{url_origen}?$select=cod_estado_depto,cod_ciudad_muni,sum(per_sa) as per_sa"
                f'&$group=cod_estado_depto,cod_ciudad_muni&$where=fecha_corte="{fecha}"'
                "&$limit=50000"
            )
            resp = requests.get(url, timeout=300)
            resp.raise_for_status()
            for fila in resp.json():
                if str(fila.get("cod_ciudad_muni", "0")) == "0":
                    # Fila "SIN DEFINIR": personas sin municipio de reporte.
                    # Se conserva como fila nacional (no se descarta) para que
                    # el KPI cuadre con la cifra oficial del RUV.
                    frames.append(
                        {
                            "codigo_divipola": CODIGO_NACIONAL,
                            "anio": corte.year,
                            "valor": float(fila.get("per_sa", 0) or 0),
                            "url": url_origen,
                            "filas": 1,
                        }
                    )
                    continue
                frames.append(
                    {
                        "codigo_divipola": str(fila["cod_ciudad_muni"]).zfill(5),
                        "anio": corte.year,
                        "valor": float(fila.get("per_sa", 0) or 0),
                        "url": url_origen,
                        "filas": 1,
                    }
                )
        return pd.DataFrame(frames), [url_origen], cortes[-1]

    def extraer(self) -> tuple[pd.DataFrame, Lineage]:
        # Sin default hardcodeado para el CSV: si el dominio cambiara de dueño,
        # un valor por defecto podría consumir contenido no controlado
        # (auditoría, sección 3, punto 3). La URL real se configura explícitamente.
        url_base = os.getenv("VICTIMAS_URL", "")
        df_csv = self._descargar_csv(url_base) if url_base else None
        if df_csv is not None and not df_csv.empty:
            url_origen = f"{url_base.rstrip('/')}/hechos_victimizantes"
            licencia = "Verificar en ficha (sección 3, punto 5)"
        else:
            if url_base:
                print("[victimas] aviso: VICTIMAS_URL no responde; usando dataset Socrata municipal de la UARIV")
            df, urls, corte_final = self._descargar_socrata(SOCRATA_MUNICIPAL)
            url_origen = urls[0]
            licencia = "Datos abiertos Colombia (datos.gov.co), publicados por la UARIV"
            return df, Lineage.ahora(
                fuente="Unidad para las Víctimas",
                url_origen=url_origen,
                fecha_corte_dato=corte_final.date(),
                licencia=licencia,
            )

        lineage = Lineage.ahora(
            fuente="Unidad para las Víctimas",
            url_origen=url_origen,
            fecha_corte_dato=None,
            licencia=licencia,
        )
        return df_csv, lineage

    def transformar(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        df = df.rename(columns={c: c.lower() for c in df.columns})
        if "codigo_divipola" in df.columns:
            # Rama Socrata: ya viene agregada por municipio/año.
            agregado = (
                df[["codigo_divipola", "anio", "valor"]]
                .groupby(["codigo_divipola", "anio"], as_index=False)["valor"]
                .sum()
            )
        else:
            col_codigo = _columna(df, ALIASES["codigo"], "código DIVIPOLA")
            col_anio = _columna(df, ALIASES["anio"], "año")
            col_hecho = _columna(df, ALIASES["hecho"], "tipo de hecho")
            col_valor = _columna(df, ALIASES["valor"], "casos")
            agregado = (
                df.assign(
                    codigo_divipola=df[col_codigo].astype(str).str.zfill(5),
                    anio=pd.to_numeric(df[col_anio], errors="coerce"),
                    hecho=df[col_hecho].astype(str).str.strip(),
                    valor=pd.to_numeric(df[col_valor], errors="coerce"),
                )
                .dropna(subset=["anio", "valor"])
                .groupby(["codigo_divipola", "anio"], as_index=False)["valor"]
                .sum()
            )

        periodo = agregado["anio"].apply(periodo_anual)
        agregado["periodo_inicio"] = periodo.apply(lambda p: p[0])
        agregado["periodo_fin"] = periodo.apply(lambda p: p[1])
        return agregado.drop(columns=["anio"])

    def cargar_curated(self, df: pd.DataFrame) -> None:
        if df.empty:
            return
        with self.conn:
            fuente_id = upsert_fuente(
                self.conn,
                nombre="Unidad para las Víctimas",
                entidad="Unidad Administrativa Especial para la Atención y Reparación a las Víctimas",
                tipo="nacional",
                descripcion="Víctimas, desplazamiento, retornos, reparación (sección 5)",
                url_base="https://datospaz.unidadvictimas.gov.co/",
                metodo_acceso="api",
                periodicidad="mensual",
                formato="JSON",
                licencia=self.lineage.licencia,
                ficha_doc="docs/fuentes/victimas.md",
            )
            indicador_id = upsert_indicador(
                self.conn,
                codigo="victimas_ruv",
                nombre="Personas incluidas en el Registro Único de Víctimas (RUV)",
                descripcion=(
                    "Sujetos de atención (per_sa): personas incluidas en el RUV, "
                    "acumulado a corte, agregadas por municipio/año. Fuente: UARIV "
                    "vía datos.gov.co (dataset municipal de hechos victimizantes)."
                ),
                unidad="personas",
                granularidad_min="municipio",
                periodicidad="anual",
                metodologia_doc="docs/metodologia/indicadores.md",
            )
            df = df.assign(indicador_id=indicador_id)
            df = validar(df, EsquemaSerieNormalizada)[0]
            nacional = df[df["codigo_divipola"] == CODIGO_NACIONAL]
            municipal = df[df["codigo_divipola"] != CODIGO_NACIONAL]
            insertadas = 0
            if not municipal.empty:
                insertadas += insertar_serie(
                    self.conn, municipal, fuente_id, self.lineage.url_origen, self.lineage.fecha_extraccion
                )
            insertadas += self._insertar_nacional(nacional, fuente_id, indicador_id)
            print(f"[victimas] filas cargadas a serie_historica: {insertadas}")

    def _insertar_nacional(self, df: pd.DataFrame, fuente_id: int, indicador_id: int) -> int:
        """Fila "SIN DEFINIR" del RUV a nivel nacional (municipio_id NULL).

        Postgres no trata NULLs como iguales en UNIQUE, así que el ON CONFLICT
        de insertar_serie no deduplicaría; se deduplica por hash_registro.
        """
        if df.empty:
            return 0
        insertadas = 0
        with self.conn.cursor() as cur:
            for fila in df.to_dict("records"):
                hash_fila = hash_registro(
                    {
                        "indicador_id": fila["indicador_id"],
                        "codigo_divipola": CODIGO_NACIONAL,
                        "periodo_inicio": str(fila["periodo_inicio"]),
                        "periodo_fin": str(fila["periodo_fin"]),
                        "valor": str(fila["valor"]),
                    }
                )
                cur.execute(
                    "SELECT 1 FROM curated.serie_historica WHERE hash_registro = %s",
                    (hash_fila,),
                )
                if cur.fetchone():
                    continue
                cur.execute(
                    """
                    INSERT INTO curated.serie_historica
                        (indicador_id, municipio_id, departamento_id, periodo_inicio, periodo_fin,
                         valor, fuente_id, url_origen, fecha_extraccion, fecha_corte_dato, hash_registro)
                    VALUES (%(indicador_id)s, NULL, NULL, %(periodo_inicio)s,
                            %(periodo_fin)s, %(valor)s, %(fuente_id)s, %(url_origen)s,
                            %(fecha_extraccion)s, %(fecha_corte_dato)s, %(hash_registro)s)
                    """,
                    {
                        "indicador_id": indicador_id,
                        "periodo_inicio": fila["periodo_inicio"],
                        "periodo_fin": fila["periodo_fin"],
                        "valor": fila["valor"],
                        "fuente_id": fuente_id,
                        "url_origen": self.lineage.url_origen,
                        "fecha_extraccion": self.lineage.fecha_extraccion,
                        "fecha_corte_dato": self.lineage.fecha_corte_dato,
                        "hash_registro": hash_fila,
                    },
                )
                insertadas += cur.rowcount > 0
        return insertadas


if __name__ == "__main__":
    Victimas_Hechos().ejecutar()
