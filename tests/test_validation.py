"""Pruebas de la validación con Pandera (secciones 7.4 y 12)."""

import pandas as pd
import pytest

from etl.common.validation import EsquemaSerieNormalizada, validar


def _df_valido():
    return pd.DataFrame(
        {
            "codigo_divipola": ["05001", "05002"],
            "periodo_inicio": pd.to_datetime(["2020-01-01", "2020-01-01"]),
            "periodo_fin": pd.to_datetime(["2020-12-31", "2020-12-31"]),
            "valor": [100.0, 50.0],
            "indicador_id": [1, 1],
        }
    )


def test_validar_acepta_serie_correcta():
    validos, rechazados = validar(_df_valido(), EsquemaSerieNormalizada)
    assert rechazados == 0
    assert len(validos) == 2


def test_validar_rechaza_valor_negativo():
    df = _df_valido()
    df.loc[0, "valor"] = -5
    validos, rechazados = validar(df, EsquemaSerieNormalizada)
    assert rechazados == 1
    assert len(validos) == 1


def test_validar_rechaza_periodo_incoherente():
    df = _df_valido()
    df.loc[1, "periodo_fin"] = pd.Timestamp("2019-12-31")
    validos, rechazados = validar(df, EsquemaSerieNormalizada)
    assert rechazados == 1
    assert len(validos) == 1


def test_validar_rechaza_codigo_divipola_invalido():
    df = _df_valido()
    df.loc[0, "codigo_divipola"] = "ABC"
    validos, rechazados = validar(df, EsquemaSerieNormalizada)
    assert rechazados == 1
    assert len(validos) == 1


def test_validar_datos_vacios_no_falla():
    df = _df_valido().iloc[0:0]
    validos, rechazados = validar(df, EsquemaSerieNormalizada)
    assert len(validos) == 0
    assert rechazados == 0


@pytest.mark.parametrize("codigo", ["05", "05001", "99999", "00001"])
def test_validar_codigos_digitos_ok(codigo):
    df = _df_valido()
    df["codigo_divipola"] = codigo
    _validos, rechazados = validar(df, EsquemaSerieNormalizada)
    assert rechazados == 0
