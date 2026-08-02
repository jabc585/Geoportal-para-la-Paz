"""Conector piloto DANE (población) - fuente de la fase 2 del plan.

Acceso: API Socrata de datos.gov.co (sección 5).
El identificador del dataset se configura con la variable de entorno
DANE_POBLACION_DATASET (p. ej. el identificador de las proyecciones de población).
"""

from __future__ import annotations

import os

import pandas as pd
import requests

from etl.common.lineage import Lineage
from etl.common.pipeline import PipelineETL

URL_SOCRATA = "https://www.datos.gov.co/resource"


class DANE_Poblacion(PipelineETL):
    pipeline_id = "dane_poblacion"
    tabla_raw = "dane_poblacion"

    def extraer(self) -> tuple[pd.DataFrame, Lineage]:
        dataset = os.getenv("DANE_POBLACION_DATASET", "")
        if not dataset:
            raise ValueError("Variable DANE_POBLACION_DATASET no configurada (ver docs/fuentes/dane.md)")
        url = f"{URL_SOCRATA}/{dataset}.json"
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
        return df

    def cargar_curated(self, df: pd.DataFrame) -> None:
        # TODO fase 2: mapear a curated.serie_historica con indicador 'poblacion' (sección 7.4)
        pass


if __name__ == "__main__":
    DANE_Poblacion().ejecutar()
