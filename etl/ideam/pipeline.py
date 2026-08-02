"""Conector IDEAM (esqueleto - sección 21, paso 11).

Fuente: variables ambientales (sección 5). Los datos ambientales alimentan el
módulo de MedioAmbiente (deforestación, cultivos ilícitos).
"""

from __future__ import annotations

import pandas as pd

from etl.common.lineage import Lineage
from etl.common.pipeline import PipelineETL


class IDEAM_Ambiental(PipelineETL):
    pipeline_id = "ideam_ambiental"
    tabla_raw = "ideam_ambiental"

    def extraer(self) -> tuple[pd.DataFrame, Lineage]:
        raise NotImplementedError(
            "Endpoint del IDEAM pendiente de confirmación (docs/fuentes/ideam.md)"
        )

    def transformar(self, df: pd.DataFrame) -> pd.DataFrame:
        return df

    def cargar_curated(self, df: pd.DataFrame) -> None:
        pass


if __name__ == "__main__":
    IDEAM_Ambiental().ejecutar()
