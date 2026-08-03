"""Conector piloto DANE (población) - fuente de la fase 2 del plan.

Acceso real verificado (auditoría 2026-08-02): DANE distribuye la serie
nacional de proyecciones de población como archivo Excel en dane.gov.co
(DCD-area-proypoblacion-Mun-2020-2035-ActPostCOVID-19.xlsx). No existe un
dataset Socrata nacional con ese shape (verificado en el catálogo en dos
rondas de auditoría), por eso la rama legacy DANE_POBLACION_DATASET se
eliminó en la ronda 2026-08-02: el único acceso soportado es el Excel.
La transformación normaliza a la serie estándar y valida con Pandera antes
de cargar a curated.
"""

from __future__ import annotations

import os

import pandas as pd

from etl.common.cargar import insertar_serie, periodo_anual, slugificar, upsert_fuente, upsert_indicador
from etl.common.db import transaccion
from etl.common.lineage import Lineage
from etl.common.pipeline import PipelineETL
from etl.common.validation import EsquemaSerieNormalizada, encontrar_columna, validar

ALIASES = {
    "codigo": [
        "mpio", "codigo_municipio", "cod_municipio", "cod_divipola",
        "codigomunicipio", "codigo_mun", "codigo_dane", "codigo_municipio2",
    ],
    "anio": ["anio", "ano", "año", "year", "año_1", "vigencia"],
    "valor": ["poblacion", "poblacion_total", "total_poblacion", "proyeccion_poblacion", "habitantes"],
    "area": ["area_geografica", "area", "zona", "ambito_geografico", "geografica"],
}

VALOR_AREA_TOTAL = "total"


def _normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns=slugificar)


def _detectar_fila_encabezado(raw: pd.DataFrame) -> int | None:
    """Busca la fila de encabezados real dentro de las primeras 20 filas.

    El Excel oficial de DANE trae filas de título/metadata antes de la fila de
    columnas (verificado en auditoría: encabezado en la fila 9, con MPIO y
    Población). La detección protege contra cambios de layout de DANE.
    """
    aliases_esperados = set(ALIASES["codigo"] + ALIASES["anio"] + ALIASES["valor"])
    for i in range(min(20, len(raw))):
        celdas = {slugificar(c) for c in raw.iloc[i].tolist()}
        if celdas & aliases_esperados and "poblacion" in celdas:
            return i
    return None


def _leer_excel_dane(url: str, hoja: str | None) -> pd.DataFrame:
    """Lee el Excel con una sola descarga y encabezado detectado.

    sheet_name=None en pandas significa "todas las hojas" (devuelve un dict,
    no un DataFrame), por eso se usa `hoja or 0` para la primera hoja.

    El archivo oficial de DANE trae filas de pie de página después de los datos
    (nota sobre Barrancominas, cita de fuente, fecha de actualización — hallazgo
    de auditoría 2026-08-02). Se recortan las filas donde todas las columnas de
    datos (código/año/población) están vacías: ni la nota tiene valor de dato.
    """
    raw = pd.read_excel(url, sheet_name=hoja or 0, header=None, engine="openpyxl", dtype=str)
    indice = _detectar_fila_encabezado(raw)
    if indice is None:
        raise ValueError(
            "No se encontró la fila de encabezados del Excel de DANE "
            "(se esperan columnas MPIO/AÑO/Población en las primeras 20 filas). "
            "Revisar docs/fuentes/dane.md"
        )
    df = raw.iloc[indice + 1 :].copy()
    df.columns = [str(c) for c in raw.iloc[indice]]
    columnas_datos = {
        c for c in df.columns if slugificar(c) in set(ALIASES["codigo"] + ALIASES["anio"] + ALIASES["valor"])
    }
    df = df.dropna(how="all", subset=list(columnas_datos)) if columnas_datos else df.dropna(how="all")
    return df.reset_index(drop=True)


class DANE_Poblacion(PipelineETL):
    pipeline_id = "dane_poblacion"
    tabla_raw = "dane_poblacion"

    def extraer(self) -> tuple[pd.DataFrame, Lineage]:
        url_xlsx = os.getenv("DANE_POBLACION_XLSX_URL", "")
        if not url_xlsx:
            raise ValueError(
                "Configurar DANE_POBLACION_XLSX_URL con la URL del Excel oficial "
                "de proyecciones de población (ver docs/fuentes/dane.md). El "
                "legacy DANE_POBLACION_DATASET se eliminó: no existe dataset "
                "Socrata nacional con el shape municipio x año x población."
            )
        hoja = os.getenv("DANE_POBLACION_HOJA", None)
        url = url_xlsx
        df = _leer_excel_dane(url, hoja)
        lineage = Lineage.ahora(
            fuente="DANE",
            url_origen=url,
            fecha_corte_dato=None,
            licencia="CC BY 4.0 (Datos Abiertos Colombia, verificar en ficha)",
        )
        return df, lineage

    def transformar(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        df = _normalizar_columnas(df)
        col_codigo = encontrar_columna(df, ALIASES["codigo"], "código DIVIPOLA", "docs/fuentes/dane.md")
        col_anio = encontrar_columna(df, ALIASES["anio"], "año", "docs/fuentes/dane.md")
        col_valor = encontrar_columna(df, ALIASES["valor"], "población", "docs/fuentes/dane.md")

        # El Excel de DANE repite cada municipio/año 3 veces (Cabecera /
        # Centros Poblados y Rural Disperso / Total): solo se conserva el Total
        # (verificado en auditoría: Medellín 2020 = 2.519.592). Si la fuente no
        # trae la columna de área (legacy Socrata), se conservan todas las filas.
        col_area = next((a for a in ALIASES["area"] if a in df.columns), None)
        if col_area:
            df = df[df[col_area].map(slugificar) == VALOR_AREA_TOTAL]

        filas_antes = len(df)
        normalizado = pd.DataFrame(
            {
                "codigo_divipola": df[col_codigo].astype(str).str.zfill(5),
                "anio": pd.to_numeric(df[col_anio], errors="coerce"),
                "valor": pd.to_numeric(df[col_valor], errors="coerce"),
            }
        ).dropna(subset=["anio", "valor"])
        self._rechazados = filas_antes - len(normalizado)

        periodo = normalizado["anio"].apply(periodo_anual)
        normalizado["periodo_inicio"] = periodo.apply(lambda p: p[0])
        normalizado["periodo_fin"] = periodo.apply(lambda p: p[1])
        normalizado = normalizado.drop(columns=["anio"])
        return normalizado.drop_duplicates(subset=["codigo_divipola", "periodo_inicio", "valor"])

    def cargar_curated(self, df: pd.DataFrame) -> None:
        if df.empty:
            return
        df = validar(df, EsquemaSerieNormalizada)[0]
        with transaccion(self.conn):
            fuente_id = upsert_fuente(
                self.conn,
                nombre="DANE",
                entidad="Departamento Administrativo Nacional de Estadística",
                tipo="nacional",
                descripcion="Población, pobreza, empleo, educación (sección 5 del plan)",
                url_base="https://www.dane.gov.co/",
                metodo_acceso="descarga",
                periodicidad="anual",
                formato="XLSX",
                licencia=self.lineage.licencia,
                ficha_doc="docs/fuentes/dane.md",
            )
            indicador_id = upsert_indicador(
                self.conn,
                codigo="poblacion",
                nombre="Población",
                descripcion="Proyecciones de población por municipio",
                unidad="personas",
                granularidad_min="municipio",
                periodicidad="anual",
                metodologia_doc="docs/metodologia/indicadores.md",
            )
            df = df.assign(indicador_id=indicador_id)
            insertadas = insertar_serie(
                self.conn, df, fuente_id, self.lineage.url_origen, self.lineage.fecha_extraccion
            )
            print(f"[dane] filas cargadas a serie_historica: {insertadas}")


if __name__ == "__main__":
    DANE_Poblacion().ejecutar()
