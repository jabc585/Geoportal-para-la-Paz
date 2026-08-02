"""Conector memoria histórica CNMH (esqueleto - sección 21, paso 11).

Fuente: Centro Nacional de Memoria Histórica (sección 5). Datos documentales
del conflicto; la publicación de hechos agregados pasa por el checklist de
privacidad (sección 3.1) antes de habilitarse en la API.
"""

from __future__ import annotations

import pandas as pd

from etl.common.lineage import Lineage
from etl.common.pipeline import PipelineETL


class Memoria_Historica(PipelineETL):
    pipeline_id = "memoria_historica"
    tabla_raw = "memoria_historica"

    def extraer(self) -> tuple[pd.DataFrame, Lineage]:
        raise NotImplementedError(
            "Endpoint del CNMH pendiente de confirmación (docs/fuentes/memoria.md)"
        )

    def transformar(self, df: pd.DataFrame) -> pd.DataFrame:
        return df

    def cargar_curated(self, df: pd.DataFrame) -> None:
        pass


if __name__ == "__main__":
    Memoria_Historica().ejecutar()
