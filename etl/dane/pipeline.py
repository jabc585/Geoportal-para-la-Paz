"""Conector piloto DANE (población) - fuente de la fase 2 del plan.

Acceso real verificado (auditoría 2026-08-02): DANE distribuye la serie
nacional de proyecciones de población como archivo Excel en dane.gov.co
(DCD-area-proypoblacion-Mun-2020-2035-ActPostCOVID-19.xlsx); no existe un
dataset Socrata nacional con ese shape. El conector lee el Excel con
DANE_POBLACION_XLSX_URL (recomendado) o la API Socrata con
DANE_POBLACION_DATASET (legacy, solo datasets locales). La transformación
normaliza a la serie estándar y valida con Pandera antes de cargar a curated.
"""

from __future__ import annotations

import os
import unicodedata

import pandas as pd

from etl.common.cargar import insertar_serie, periodo_anual, upsert_fuente, upsert_indicador
from etl.common.lineage import Lineage
from etl.common.pipeline import PipelineETL
from etl.common.validation import EsquemaSerieNormalizada, validar

URL_SOCRATA = "https://www.datos.gov.co/resource"

ALIASES = {
    "codigo": ["codigo_municipio", "cod_municipio", "cod_divipola", "codigomunicipio", "codigo_mun", "codigo_dane", "codigo_municipio2"],
    "anio": ["anio", "ano", "año", "year", "año_1", "vigencia"],
    "valor": ["poblacion", "poblacion_total", "total_poblacion", "proyeccion_poblacion", "habitantes"],
}


def _normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Minúsculas y sin acentos para que los aliases matcheen (p. ej. 'Código municipio')."""
    def limpiar(texto: str) -> str:
        texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
        return texto.replace(" ", "_")

    return df.rename(columns={c: limpiar(str(c)) for c in df.columns})


def _columna(df: pd.DataFrame, aliases: list[str], etiqueta: str) -> str:
    for alias in aliases:
        if alias in df.columns:
            return alias
    raise ValueError(f"No se encontró columna para {etiqueta} (buscadas: {aliases}). Revisar ficha docs/fuentes/dane.md")


class DANE_Poblacion(PipelineETL):
    pipeline_id = "dane_poblacion"
    tabla_raw = "dane_poblacion"

    def extraer(self) -> tuple[pd.DataFrame, Lineage]:
        url_xlsx = os.getenv("DANE_POBLACION_XLSX_URL", "")
        dataset = os.getenv("DANE_POBLACION_DATASET", "")
        if url_xlsx:
            hoja = os.getenv("DANE_POBLACION_HOJA", None)
            url = url_xlsx
            df = pd.read_excel(url, sheet_name=hoja, engine="openpyxl", dtype=str)
        elif dataset:
            url = f"{URL_SOCRATA}/{dataset}.json"
            import requests

            resp = requests.get(url, params={"$limit": 50000}, timeout=60)
            resp.raise_for_status()
            df = pd.DataFrame(resp.json())
        else:
            raise ValueError(
                "Configurar DANE_POBLACION_XLSX_URL (Excel oficial de proyecciones, "
                "ver docs/fuentes/dane.md) o DANE_POBLACION_DATASET (Socrata, legacy)"
            )
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
        col_codigo = _columna(df, ALIASES["codigo"], "código DIVIPOLA")
        col_anio = _columna(df, ALIASES["anio"], "año")
        col_valor = _columna(df, ALIASES["valor"], "población")

        normalizado = pd.DataFrame(
            {
                "codigo_divipola": df[col_codigo].astype(str).str.zfill(5),
                "anio": pd.to_numeric(df[col_anio], errors="coerce"),
                "valor": pd.to_numeric(df[col_valor], errors="coerce"),
            }
        ).dropna(subset=["anio", "valor"])

        periodo = normalizado["anio"].apply(periodo_anual)
        normalizado["periodo_inicio"] = periodo.apply(lambda p: p[0])
        normalizado["periodo_fin"] = periodo.apply(lambda p: p[1])
        normalizado = normalizado.drop(columns=["anio"])
        return normalizado.drop_duplicates(subset=["codigo_divipola", "periodo_inicio", "valor"])

    def cargar_curated(self, df: pd.DataFrame) -> None:
        if df.empty:
            return
        df = validar(df, EsquemaSerieNormalizada)[0]
        with self.conn:
            fuente_id = upsert_fuente(
                self.conn,
                nombre="DANE",
                entidad="Departamento Administrativo Nacional de Estadística",
                tipo="nacional",
                descripcion="Población, pobreza, empleo, educación (sección 5 del plan)",
                url_base="https://www.dane.gov.co/",
                metodo_acceso="api",
                periodicidad="anual",
                formato="JSON/CSV",
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
