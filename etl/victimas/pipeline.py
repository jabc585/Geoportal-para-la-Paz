"""Conector piloto Unidad de Víctimas (Datos Paz) - fuente de la fase 2 del plan.

Acceso: API de Datos Paz (sección 5). Los hechos victimizantes se publican
agregados (municipio/periodo/tipo de hecho), nunca a nivel individual
(sección 3, punto 2: principio de no daño).
"""

from __future__ import annotations

import os

import pandas as pd
import requests

from etl.common.lineage import Lineage
from etl.common.pipeline import PipelineETL

URL_DATOSPAZ = os.getenv("VICTIMAS_URL", "https://datospaz.unidadvictimas.gov.co/api/v1/")


class Victimas_Hechos(PipelineETL):
    pipeline_id = "victimas_hechos"
    tabla_raw = "victimas_hechos"

    def extraer(self) -> tuple[pd.DataFrame, Lineage]:
        url = f"{URL_DATOSPAZ}hechos_victimizantes"
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        df = pd.DataFrame(resp.json())
        lineage = Lineage.ahora(
            fuente="Unidad para las Víctimas",
            url_origen=url,
            fecha_corte_dato=None,
            licencia="Verificar en ficha (sección 3, punto 5)",
        )
        return df, lineage

    def transformar(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        df = df.rename(columns={c: c.lower() for c in df.columns})
        return df

    def cargar_curated(self, df: pd.DataFrame) -> None:
        # TODO fase 2: mapear a curated.serie_historica con agregación mínima
        # municipio/año + checklist de privacidad (sección 3.1) antes de habilitar
        pass


if __name__ == "__main__":
    Victimas_Hechos().ejecutar()
