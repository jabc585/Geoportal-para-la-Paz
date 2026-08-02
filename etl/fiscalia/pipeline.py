"""Conector Fiscalía General de la Nación (esqueleto - sección 21, paso 11).

Fuente: estadísticas judiciales (sección 5). El método de acceso concreto se
documenta en docs/fuentes/fiscalia.md; hasta que se confirme el endpoint, el
conector se ejecuta en modo esqueleto (extracción deshabilitada).
"""

from __future__ import annotations

import pandas as pd

from etl.common.lineage import Lineage
from etl.common.pipeline import PipelineETL


class Fiscalia_Estadisticas(PipelineETL):
    pipeline_id = "fiscalia_estadisticas"
    tabla_raw = "fiscalia_estadisticas"

    def extraer(self) -> tuple[pd.DataFrame, Lineage]:
        raise NotImplementedError(
            "Endpoint de la Fiscalía pendiente de confirmación (docs/fuentes/fiscalia.md)"
        )

    def transformar(self, df: pd.DataFrame) -> pd.DataFrame:
        return df

    def cargar_curated(self, df: pd.DataFrame) -> None:
        pass


if __name__ == "__main__":
    Fiscalia_Estadisticas().ejecutar()
