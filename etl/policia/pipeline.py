"""Conector Policía Nacional (esqueleto - sección 21, paso 11).

Fuente: delitos (sección 5). Los datos de homicidios se reconcilian con
Medicina Legal en curated.vw_homicidios_reconciliado (sección 7.5).
"""

from __future__ import annotations

import pandas as pd

from etl.common.lineage import Lineage
from etl.common.pipeline import PipelineETL


class Policia_Delitos(PipelineETL):
    pipeline_id = "policia_delitos"
    tabla_raw = "policia_delitos"

    def extraer(self) -> tuple[pd.DataFrame, Lineage]:
        raise NotImplementedError(
            "Endpoint de la Policía pendiente de confirmación (docs/fuentes/policia.md)"
        )

    def transformar(self, df: pd.DataFrame) -> pd.DataFrame:
        return df

    def cargar_curated(self, df: pd.DataFrame) -> None:
        pass


if __name__ == "__main__":
    Policia_Delitos().ejecutar()
