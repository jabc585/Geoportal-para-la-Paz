"""Conector piloto ART/PDET - fuente de la fase 2 del plan.

Acceso: datos abiertos de la Agencia de Renovación del Territorio (sección 5).
El endpoint de proyectos PDET se configura con la variable PDET_URL.
"""

from __future__ import annotations

import os

import pandas as pd
import requests

from etl.common.lineage import Lineage
from etl.common.pipeline import PipelineETL


class ART_PDET(PipelineETL):
    pipeline_id = "art_pdet"
    tabla_raw = "art_pdet"

    def extraer(self) -> tuple[pd.DataFrame, Lineage]:
        url = os.getenv("PDET_URL", "")
        if not url:
            raise ValueError("Variable PDET_URL no configurada (ver docs/fuentes/art.md)")
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
        return df

    def cargar_curated(self, df: pd.DataFrame) -> None:
        # TODO fase 2: mapear a tabla de proyectos PDET (avance, inversión) con linaje
        pass


if __name__ == "__main__":
    ART_PDET().ejecutar()
