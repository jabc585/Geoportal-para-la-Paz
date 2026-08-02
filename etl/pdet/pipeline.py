"""Conector piloto ART/PDET - fuente de la fase 2 del plan.

Acceso: datos abiertos de la Agencia de Renovación del Territorio (sección 5).
El endpoint de proyectos PDET se configura con PDET_URL. Carga proyectos en
curated.pdet_proyectos y la inversión agregada en serie_historica (indicador
pdet_inversion), ambas con linaje completo.
"""

from __future__ import annotations

import os

import pandas as pd

from etl.common.cargar import insertar_serie, periodo_anual, resolver_territorio, upsert_fuente, upsert_indicador
from etl.common.lineage import Lineage, hash_registro
from etl.common.pipeline import PipelineETL
from etl.common.validation import EsquemaSerieNormalizada, validar

ALIASES = {
    "codigo": ["codigo_municipio", "cod_municipio", "cod_divipola", "codigomunicipio", "codigo_mun"],
    "nombre": ["nombre_proyecto", "proyecto", "nombre", "titulo_proyecto"],
    "estado": ["estado", "estado_proyecto", "fase"],
    "avance": ["avance", "avance_pct", "porcentaje_avance", "avance_fisico"],
    "inversion": ["valor_inversion", "valor", "inversion", "valor_total", "presupuesto"],
    "anio": ["anio", "vigencia", "ano", "año", "year"],
}


def _columna(df: pd.DataFrame, aliases: list[str], etiqueta: str) -> str:
    for alias in aliases:
        if alias in df.columns:
            return alias
    raise ValueError(f"No se encontró columna para {etiqueta} (buscadas: {aliases}). Revisar ficha docs/fuentes/art.md")


class ART_PDET(PipelineETL):
    pipeline_id = "art_pdet"
    tabla_raw = "art_pdet"

    def extraer(self) -> tuple[pd.DataFrame, Lineage]:
        url = os.getenv("PDET_URL", "")
        if not url:
            raise ValueError("Variable PDET_URL no configurada (ver docs/fuentes/art.md)")
        import requests

        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        df = pd.DataFrame(resp.json())
        lineage = Lineage.ahora(
            fuente="Agencia de Renovación del Territorio",
            url_origen=url,
            fecha_corte_dato=None,
            licencia="Verificar en ficha (sección 3, punto 5)",
        )
        return df, lineage

    def transformar(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        df = df.rename(columns={c: c.lower() for c in df.columns})
        col_codigo = _columna(df, ALIASES["codigo"], "código DIVIPOLA")
        col_nombre = _columna(df, ALIASES["nombre"], "nombre del proyecto")
        col_estado = _columna(df, ALIASES["estado"], "estado")
        col_avance = _columna(df, ALIASES["avance"], "avance")
        col_inversion = _columna(df, ALIASES["inversion"], "inversión")
        col_anio = _columna(df, ALIASES["anio"], "año")

        return pd.DataFrame(
            {
                "codigo_divipola": df[col_codigo].astype(str).str.zfill(5),
                "nombre": df[col_nombre].astype(str),
                "estado": df[col_estado].astype(str),
                "avance_pct": pd.to_numeric(df[col_avance], errors="coerce"),
                "valor_inversion": pd.to_numeric(df[col_inversion], errors="coerce"),
                "anio": pd.to_numeric(df[col_anio], errors="coerce"),
            }
        ).dropna(subset=["anio", "valor_inversion"])

    def cargar_curated(self, df: pd.DataFrame) -> None:
        if df.empty:
            return
        with self.conn:
            fuente_id = upsert_fuente(
                self.conn,
                nombre="Agencia de Renovación del Territorio",
                entidad="ART",
                tipo="nacional",
                descripcion="PDET, obras, proyectos (sección 5)",
                url_base="https://www.renovacionterritorio.gov.co/",
                metodo_acceso="descarga",
                periodicidad="mensual",
                formato="JSON/CSV",
                licencia=self.lineage.licencia,
                ficha_doc="docs/fuentes/art.md",
            )
            insertadas = self._cargar_proyectos(df, fuente_id)
            insertadas += self._cargar_inversion(df, fuente_id)
            print(f"[pdet] filas cargadas: {insertadas} (proyectos + serie inversión)")

    def _cargar_proyectos(self, df: pd.DataFrame, fuente_id: int) -> int:
        insertadas = 0
        sin_territorio = 0
        with self.conn.cursor() as cur:
            for fila in df.to_dict("records"):
                municipio_id, departamento_id = resolver_territorio(self.conn, fila["codigo_divipola"])
                if municipio_id is None and departamento_id is None:
                    sin_territorio += 1
                    continue
                cur.execute(
                    """
                    INSERT INTO curated.pdet_proyectos
                        (municipio_id, departamento_id, nombre, estado, avance_pct,
                         valor_inversion, anio, fuente_id, url_origen, fecha_extraccion,
                         fecha_corte_dato, hash_registro)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (
                        municipio_id,
                        departamento_id,
                        fila["nombre"],
                        fila["estado"],
                        fila["avance_pct"],
                        fila["valor_inversion"],
                        int(fila["anio"]),
                        fuente_id,
                        self.lineage.url_origen,
                        self.lineage.fecha_extraccion,
                        self.lineage.fecha_corte_dato,
                        hash_registro(fila),
                    ),
                )
                insertadas += cur.rowcount > 0
        if sin_territorio:
            print(
                f"[pdet] AVISO: {sin_territorio} proyectos descartados por territorio no resuelto "
                f"(¿catálogo DIVIPOLA sembrado? python -m etl.common.divipola)"
            )
        return insertadas

    def _cargar_inversion(self, df: pd.DataFrame, fuente_id: int) -> int:
        indicador_id = upsert_indicador(
            self.conn,
            codigo="pdet_inversion",
            nombre="Inversión PDET",
            descripcion="Inversión en proyectos PDET por municipio/año",
            unidad="COP",
            granularidad_min="municipio",
            periodicidad="mensual",
            metodologia_doc="docs/metodologia/indicadores.md",
        )
        agregado = (
            df.groupby(["codigo_divipola", "anio"], as_index=False)["valor_inversion"].sum()
        )
        periodo = agregado["anio"].apply(periodo_anual)
        serie = pd.DataFrame(
            {
                "codigo_divipola": agregado["codigo_divipola"],
                "periodo_inicio": periodo.apply(lambda p: p[0]),
                "periodo_fin": periodo.apply(lambda p: p[1]),
                "valor": agregado["valor_inversion"],
                "indicador_id": indicador_id,
            }
        )
        serie = validar(serie, EsquemaSerieNormalizada)[0]
        return insertar_serie(self.conn, serie, fuente_id, self.lineage.url_origen, self.lineage.fecha_extraccion)


if __name__ == "__main__":
    ART_PDET().ejecutar()
