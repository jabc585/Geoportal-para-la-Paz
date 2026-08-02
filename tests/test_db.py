"""Pruebas del saneo NaN→None en la frontera jsonb (hallazgo de auditoría 2026-08-02)."""

import math

import numpy as np
import pandas as pd
import pytest

from etl.common.db import sanear_json


def test_nan_float_escala_a_none():
    assert sanear_json(float("nan")) is None
    assert math.isnan(sanear_json(1.5)) is False
    assert sanear_json(1.5) == 1.5


def test_numpy_nan_a_none():
    assert sanear_json(np.float64("nan")) is None
    assert sanear_json(np.float64(3.0)) == 3.0


def test_pandas_na_y_nat_a_none():
    assert sanear_json(pd.NA) is None
    assert sanear_json(pd.NaT) is None


def test_dict_anidado_sanea_recursivamente():
    valor = {"a": float("nan"), "b": {"c": np.float64("nan"), "d": "texto"}, "e": [pd.NA, 1]}
    limpio = sanear_json(valor)
    assert limpio["a"] is None
    assert limpio["b"]["c"] is None
    assert limpio["b"]["d"] == "texto"
    assert limpio["e"] == [None, 1]


def test_valores_validos_intactos():
    assert sanear_json("MPIO") == "MPIO"
    assert sanear_json(42) == 42
    assert sanear_json(0) == 0
    assert sanear_json(None) is None
    assert sanear_json(True) is True


def test_fecha_se_conserva():
    assert sanear_json(pd.Timestamp("2020-01-01")) is not None
