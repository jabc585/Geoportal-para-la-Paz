"""Validación de datos con contratos (sección 4.1 y 12).

Los pipelines validan antes de promover datos de staging a curated y
registran los resultados en data_quality_metrics (sección 7.4).
"""

from __future__ import annotations

import pandas as pd
import pandera as pa


class EsquemaBase(pa.DataFrameModel):
    """Contrato mínimo para toda serie: territorio, periodo y valor numérico."""

    periodo_inicio: pa.typing.Series[pd.Timestamp] = pa.Field(coerce=True)
    periodo_fin: pa.typing.Series[pd.Timestamp] = pa.Field(coerce=True)
    valor: pa.typing.Series[float] = pa.Field(ge=0, coerce=True)

    @pa.check("periodo_fin")
    def periodo_coherente(cls, serie: pd.Series) -> pd.Series:
        return serie >= cls.periodo_inicio

    class Config:
        strict = False


def validar(df: pd.DataFrame, contrato: type[pa.DataFrameModel]) -> tuple[pd.DataFrame, int]:
    """Valida un DataFrame contra el contrato y devuelve (datos válidos, rechazados)."""
    try:
        validos = contrato.validate(df, lazy=True)
        return validos, len(df) - len(validos)
    except pa.errors.SchemaErrors as err:
        indices = err.failure_cases["index"].dropna().unique()
        rechazados = df.loc[df.index.isin(indices)]
        return df.drop(rechazados.index), len(rechazados)
