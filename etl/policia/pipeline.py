"""Conector de delitos: Policía Nacional (plan2.md Fase B, fuente 5).

Datasets reales en datos.gov.co (verificados en vivo 2026-08-02), por tipo de
delito: hurto `d4fr-sbn2` (44.169 filas, 3 tipos), violencia intrafamiliar
`vuyt-mqpw` (682.558 filas), delitos sexuales `fpe5-yrmw` (392.576 filas,
23 delitos). Cada fila tiene `cantidad` por segmento demográfico; el pipeline
suma `cantidad` por municipio/año (y tipo de delito cuando el dataset lo
tiene). `codigo_dane` viene como DIVIPOLA de 5 dígitos + "000": se recorta.

Homicidios intencionales (verificado en vivo 2026-08-02): no hay dataset
Socrata, pero la Policía publica el Excel oficial SIEDCO por año en
policia.gov.co/estadistica-delictiva/homicidios (p. ej. "Homicidio Intencional2025.xlsx",
507 KB, 13.738 filas con DEPARTAMENTO, MUNICIPIO, FECHA HECHO, CODIGO DANE y
CANTIDAD — mismo shape que los datasets Socrata). Disponible para 2025 y 2024.
`Policia_Homicidios` lo descarga (variable `POLICIA_HOMICIDIOS_URL` o patrón
por año) y carga el indicador `homicidios` bajo la fuente `policia`, el que
alimenta `curated.vw_homicidios_reconciliado` (sección 7.5).
"""

from __future__ import annotations

import io

import pandas as pd
import requests

from etl.common.cargar import insertar_serie, periodo_anual, slugificar, upsert_fuente, upsert_indicador
from etl.common.config import get_source_url, settings
from etl.common.lineage import Lineage
from etl.common.pipeline import PipelineETL
from etl.common.validation import EsquemaSerieNormalizada, validar

TAMANO_PAGINA = 50000
ANIO_MINIMO = 1980
ANIO_MAXIMO = 2027

# Excel oficial SIEDCO publicado por la Policía (delitos-impacto), por año.
HOMICIDIOS_URL_PATRON = (
    "https://www.policia.gov.co/sites/default/files/delitos-impacto/"
    "Homicidio%20Intencional{anio}.xlsx"
)
# Años que se intentan cuando la variable no está configurada. Verificado en
# vivo (2026-08-02): "Homicidio Intencional2024.xlsx" es parcial (solo 2024-12 +
# ene-abr 2025) y contaminaría el total anual, así que el default es solo el
# último año completo; el resto se puede configurar explícitamente.
HOMICIDIOS_ANIOS_DEFAULT = [2025]

DELITOS = {
    "hurto": {
        "variable": "POLICIA_HURTO_URL",
        "resource_id": "d4fr-sbn2",
        "col_dim": "tipo_de_hurto",
        "prefijo_indicador": "Hurto (Policía Nacional)",
        "unidad": "delitos",
        "descripcion": "Hurtos por municipio/año y tipo (Policía Nacional)",
    },
    "violencia": {
        "variable": "POLICIA_VIOLENCIA_URL",
        "resource_id": "vuyt-mqpw",
        "col_dim": None,  # sin dimensión en la fuente
        "prefijo_indicador": "Violencia intrafamiliar (Policía Nacional)",
        "unidad": "delitos",
        "descripcion": "Violencia intrafamiliar por municipio/año (Policía Nacional)",
    },
    "sexuales": {
        "variable": "POLICIA_SEXUALES_URL",
        "resource_id": "fpe5-yrmw",
        "col_dim": "delito",
        "prefijo_indicador": "Delitos sexuales (Policía Nacional)",
        "unidad": "delitos",
        "descripcion": "Delitos sexuales por municipio/año y tipo (Policía Nacional)",
    },
}


def _descargar(url: str) -> list[dict]:
    """Descarga paginada de Socrata ($limit/$offset, sin token)."""
    filas: list[dict] = []
    offset = 0
    while True:
        resp = requests.get(
            url, params={"$limit": TAMANO_PAGINA, "$offset": offset}, timeout=300
        )
        resp.raise_for_status()
        batch = resp.json()
        filas.extend(batch)
        if len(batch) < TAMANO_PAGINA:
            return filas
        offset += len(batch)


class Policia_Delitos(PipelineETL):
    pipeline_id = "policia_delitos"
    tabla_raw = "policia_delitos"

    def __init__(self, delito: str = "hurto") -> None:
        super().__init__()
        if delito not in DELITOS:
            raise ValueError(f"Delito Policía desconocido: {delito} (opciones: {', '.join(DELITOS)})")
        self._delito = delito
        self._cfg = DELITOS[delito]
        self.pipeline_id = f"policia_{delito}"
        self.tabla_raw = f"policia_{delito}"

    def extraer(self) -> tuple[pd.DataFrame, Lineage]:
        url = get_source_url(
            self._cfg["variable"],
            ayuda=f"Dataset Socrata de {self._cfg['prefijo_indicador'].lower()} (resource {self._cfg['resource_id']})",
        )
        df = pd.DataFrame(_descargar(url))
        lineage = Lineage.ahora(
            fuente="Policía Nacional",
            url_origen=url,
            fecha_corte_dato=None,
            licencia="Policía Nacional de Colombia - verificar en ficha (sección 3, punto 5)",
        )
        return df, lineage

    def transformar(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        anio = pd.to_datetime(df["fecha_hecho"], dayfirst=True, errors="coerce").dt.year
        df = df.assign(
            # codigo_dane llega como DIVIPOLA de 5 dígitos + "000" (p. ej. 44420000)
            codigo_divipola=df["codigo_dane"].astype(str).str[:5],
            anio=pd.to_numeric(anio, errors="coerce"),
            valor=pd.to_numeric(df["cantidad"], errors="coerce"),
        )
        df = df[df["anio"].between(ANIO_MINIMO, ANIO_MAXIMO)].dropna(subset=["valor"])

        if self._cfg["col_dim"]:
            df = df.assign(dimension=df[self._cfg["col_dim"]].fillna("Sin información").astype(str).str.strip())
            agrupado = (
                df.groupby(["codigo_divipola", "anio", "dimension"], as_index=False)["valor"].sum()
            )
        else:
            agrupado = df.groupby(["codigo_divipola", "anio"], as_index=False)["valor"].sum()
            agrupado["dimension"] = "violencia_intrafamiliar"

        periodo = agrupado["anio"].apply(periodo_anual)
        agrupado["periodo_inicio"] = periodo.apply(lambda p: p[0])
        agrupado["periodo_fin"] = periodo.apply(lambda p: p[1])
        return agrupado.drop(columns=["anio"])

    def cargar_curated(self, df: pd.DataFrame) -> None:
        if df.empty:
            return
        with self.conn:
            fuente_id = upsert_fuente(
                self.conn,
                nombre="Policía Nacional",
                entidad="Policía Nacional de Colombia",
                tipo="nacional",
                descripcion="Delitos por municipio: hurto, violencia intrafamiliar, delitos sexuales (sección 5)",
                url_base="https://www.policia.gov.co/",
                metodo_acceso="api",
                periodicidad="mensual",
                formato="JSON",
                licencia=self.lineage.licencia,
                ficha_doc="docs/fuentes/policia.md",
            )
            insertadas = 0
            for dimension, grupo in df.groupby("dimension"):
                indicador_id = upsert_indicador(
                    self.conn,
                    codigo=f"policia_{self._delito}_{slugificar(dimension)}",
                    nombre=f"{self._cfg['prefijo_indicador']}: {dimension}",
                    descripcion=self._cfg["descripcion"],
                    unidad=self._cfg["unidad"],
                    granularidad_min="municipio",
                    periodicidad="mensual",
                    metodologia_doc="docs/metodologia/indicadores.md",
                )
                grupo = grupo.assign(indicador_id=indicador_id)
                grupo = validar(grupo, EsquemaSerieNormalizada)[0]
                insertadas += insertar_serie(
                    self.conn, grupo, fuente_id, self.lineage.url_origen, self.lineage.fecha_extraccion
                )
            print(f"[policia/{self._delito}] filas cargadas a serie_historica: {insertadas}")


class Policia_Homicidios(PipelineETL):
    """Homicidios intencionales: Excel oficial SIEDCO de policia.gov.co.

    El Excel trae la fila individual por segmento (género/edad/arma); el
    pipeline agrega a municipio-año y solo eso llega a curated (sin PII).
    El indicador se llama `homicidios` y la fuente queda con codigo `policia`
    para alimentar `vw_homicidios_reconciliado` (sección 7.5).
    """

    pipeline_id = "policia_homicidios"
    tabla_raw = "policia_homicidios"

    def __init__(self) -> None:
        super().__init__()
        self._urls: list[str] = []
        self._datos: pd.DataFrame | None = None

    # ── extraer ───────────────────────────────────────────────────────────

    def _urls_a_descargar(self) -> list[str]:
        """Variable configurada (URLs separadas por coma) o patrón por año."""
        if settings.policia_homicidios_url:
            return [u.strip() for u in settings.policia_homicidios_url.split(",") if u.strip()]
        return [HOMICIDIOS_URL_PATRON.format(anio=a) for a in HOMICIDIOS_ANIOS_DEFAULT]

    def _descargar_excel(self, url: str) -> pd.DataFrame | None:
        resp = requests.get(url, timeout=120)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        # La fila de cabecera varía por año (2025 → fila 10, 2024 → fila 9):
        # se localiza buscando la columna CODIGO DANE en los primeros renglones.
        raw = pd.read_excel(io.BytesIO(resp.content), header=None, dtype=str)
        fila_header = next(
            i
            for i in range(min(30, len(raw)))
            if raw.iloc[i].astype(str).str.upper().str.contains("CODIGO DANE").any()
        )
        df = raw.iloc[fila_header + 1 :].copy().reset_index(drop=True)
        df.columns = raw.iloc[fila_header].astype(str).str.strip().tolist()
        return df

    def extraer(self) -> tuple[pd.DataFrame, Lineage]:
        self._urls = self._urls_a_descargar()
        frames, metadatos = [], []
        for url in self._urls:
            df = self._descargar_excel(url)
            if df is None:
                continue
            frames.append(df)
            metadatos.append({"url": url, "filas": len(df), "columnas": list(df.columns)})
        if not frames:
            raise RuntimeError(
                "Ningún Excel de homicidios disponible (¿cambió el patrón de policia.gov.co?)"
            )
        self._datos = pd.concat(frames, ignore_index=True)
        self.lineage = Lineage.ahora(
            fuente="Policía Nacional",
            url_origen=", ".join(self._urls),
            fecha_corte_dato=None,
            licencia="Policía Nacional de Colombia - verificar en ficha (sección 3, punto 5)",
        )
        # raw guarda metadatos por archivo (el Excel completo no se duplica en la BD)
        df_raw = pd.DataFrame(metadatos)
        return df_raw, self.lineage

    # ── transformar ───────────────────────────────────────────────────────

    def transformar(self, df: pd.DataFrame) -> pd.DataFrame:
        datos = self._datos if self._datos is not None else df
        if datos.empty:
            return datos
        anio = pd.to_datetime(datos["FECHA HECHO"], dayfirst=True, errors="coerce").dt.year
        codigo = datos["CODIGO DANE"].astype(str).str.extract(r"(\d+)")[0].str.zfill(8)
        normalizado = pd.DataFrame(
            {
                "codigo_divipola": codigo.str[:5],
                "anio": pd.to_numeric(anio, errors="coerce"),
                "valor": pd.to_numeric(datos["CANTIDAD"], errors="coerce"),
            }
        )
        normalizado = normalizado[
            normalizado["anio"].between(ANIO_MINIMO, ANIO_MAXIMO)
        ].dropna(subset=["valor"])
        if normalizado.empty:
            return normalizado
        agrupado = normalizado.groupby(["codigo_divipola", "anio"], as_index=False)["valor"].sum()
        agrupado["dimension"] = "homicidio"
        periodo = agrupado["anio"].apply(periodo_anual)
        agrupado["periodo_inicio"] = periodo.apply(lambda p: p[0])
        agrupado["periodo_fin"] = periodo.apply(lambda p: p[1])
        return agrupado.drop(columns=["anio"])

    # ── cargar ────────────────────────────────────────────────────────────

    def cargar_curated(self, df: pd.DataFrame) -> None:
        if df.empty:
            return
        with self.conn:
            fuente_id = upsert_fuente(
                self.conn,
                nombre="Policía Nacional",
                entidad="Policía Nacional de Colombia",
                tipo="nacional",
                descripcion="Delitos por municipio: hurto, violencia intrafamiliar, delitos sexuales, homicidios (sección 5)",
                url_base="https://www.policia.gov.co/",
                metodo_acceso="descarga",
                periodicidad="anual",
                formato="Excel",
                licencia=self.lineage.licencia,
                ficha_doc="docs/fuentes/policia.md",
            )
            # upsert_fuente no actualiza el codigo por diseño; la vista de
            # reconciliación espera f.codigo = 'policia'.
            with self.conn.cursor() as cur:
                cur.execute("UPDATE curated.fuentes SET codigo = 'policia' WHERE fuente_id = %s", (fuente_id,))
            indicador_id = upsert_indicador(
                self.conn,
                codigo="homicidios",
                nombre="Homicidios (Policía Nacional)",
                descripcion="Homicidios intencionales por municipio/año (SIEDCO, Policía Nacional)",
                unidad="delitos",
                granularidad_min="municipio",
                periodicidad="anual",
                metodologia_doc="docs/metodologia/indicadores.md",
            )
            a_cargar = df.assign(indicador_id=indicador_id)
            a_cargar = validar(a_cargar, EsquemaSerieNormalizada)[0]
            insertadas = insertar_serie(
                self.conn, a_cargar, fuente_id, self.lineage.url_origen, self.lineage.fecha_extraccion
            )
            print(f"[policia/homicidios] filas cargadas a serie_historica: {insertadas}")


if __name__ == "__main__":
    import sys

    delito = sys.argv[1] if len(sys.argv) > 1 else "hurto"
    if delito == "homicidios":
        Policia_Homicidios().ejecutar()
    else:
        Policia_Delitos(delito).ejecutar()
