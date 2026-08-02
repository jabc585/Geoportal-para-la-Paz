"""Conector piloto DANE (población) - fuente de la fase 2 del plan.

Acceso: API Socrata de datos.gov.co (sección 5). El identificador del dataset
se configura con DANE_POBLACION_DATASET. La transformación normaliza a la
serie estándar y valida con Pandera antes de cargar a curated (secciones 7.4 y 12).
"""

from __future__ import annotations

import os

import pandas as pd

from etl.common.cargar import insertar_serie, periodo_anual, resolver_territorio, upsert_fuente, upsert_indicador
from etl.common.lineage import Lineage
from etl.common.pipeline import PipelineETL
from etl.common.validation import EsquemaSerieNormalizada, validar

URL_SOCRATA = "https://www.datos.gov.co/resource"

ALIASES = {
    "codigo": ["codigo_municipio", "cod_municipio", "cod_divipola", "codigomunicipio", "codigo_mun", "codigo_dane"],
    "anio": ["anio", "ano", "año", "year", "año_1", "vigencia"],
    "valor": ["poblacion", "poblacion_total", "total_poblacion", "proyeccion_poblacion", "habitantes"],
}


def _columna(df: pd.DataFrame, aliases: list[str], etiqueta: str) -> str:
    for alias in aliases:
        if alias in df.columns:
            return alias
    raise ValueError(f"No se encontró columna para {etiqueta} (buscadas: {aliases}). Revisar ficha docs/fuentes/dane.md")


class DANE_Poblacion(PipelineETL):
    pipeline_id = "dane_poblacion"
    tabla_raw = "dane_poblacion"

    def extraer(self) -> tuple[pd.DataFrame, Lineage]:
        dataset = os.getenv("DANE_POBLACION_DATASET", "")
        if not dataset:
            raise ValueError("Variable DANE_POBLACION_DATASET no configurada (ver docs/fuentes/dane.md)")
        url = f"{URL_SOCRATA}/{dataset}.json"
        import requests

        resp = requests.get(url, params={"$limit": 50000}, timeout=60)
        resp.raise_for_status()
        df = pd.DataFrame(resp.json())
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
        df = df.rename(columns={c: c.lower() for c in df.columns})
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
