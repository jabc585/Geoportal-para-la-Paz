"""Validación de datos con contratos (sección 4.1 y 12).

Los pipelines validan antes de promover datos de staging a curated y
registran los resultados en data_quality_metrics (sección 7.4).
"""

from __future__ import annotations

import pandas as pd
import pandera as pa


class EsquemaBase(pa.DataFrameModel):
    """Contrato mínimo para toda serie: territorio, periodo y valor numérico.

    Nota: la coherencia entre periodo_inicio y periodo_fin se garantiza al
    construir los periodos (etl/common/cargar.periodo_anual) y se verifica en
    la validación con un filtro previo en validar(); los checks por columna
    aquí permiten atribuir filas rechazadas por índice.
    """

    periodo_inicio: pa.typing.Series[pd.Timestamp] = pa.Field(coerce=True)
    periodo_fin: pa.typing.Series[pd.Timestamp] = pa.Field(coerce=True)
    valor: pa.typing.Series[float] = pa.Field(ge=0, coerce=True)

    class Config:
        strict = False


class EsquemaSerieNormalizada(EsquemaBase):
    """Formato normalizado que consume insertar_serie (etl/common/cargar.py).

    Es el contrato de salida de transformar() y la garantía de que solo
    llegan a curated filas con linaje completo y periodos coherentes.
    """

    codigo_divipola: pa.typing.Series[str] = pa.Field(
        str_length={"min_value": 2, "max_value": 5}, str_matches=r"^\d+$"
    )
    indicador_id: pa.typing.Series[int] = pa.Field(ge=1, coerce=True)


def validar(df: pd.DataFrame, contrato: type[pa.DataFrameModel]) -> tuple[pd.DataFrame, int]:
    """Valida un DataFrame contra el contrato y devuelve (datos válidos, rechazados).

    Descarta primero filas con periodo incoherente (periodo_fin < periodo_inicio)
    y luego aplica los checks por columna del contrato, atribuyendo rechazos
    por índice de fila.
    """
    df = df.copy()
    rechazados_incoherentes = 0
    if not df.empty and "periodo_inicio" in df.columns and "periodo_fin" in df.columns:
        coherentes = df["periodo_fin"] >= df["periodo_inicio"]
        rechazados_incoherentes = int((~coherentes).sum())
        df = df[coherentes]
    if df.empty:
        return df, rechazados_incoherentes
    try:
        validos = contrato.validate(df, lazy=True)
        return validos, rechazados_incoherentes
    except pa.errors.SchemaErrors as err:
        indices = pd.to_numeric(err.failure_cases["index"], errors="coerce").dropna().astype(int).unique()
        rechazados = df.loc[df.index.isin(indices)]
        validos = df.drop(rechazados.index)
        return validos, rechazados_incoherentes + len(rechazados)
