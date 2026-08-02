"""Pruebas del conector internacional World Bank (sección 5.2 y 7.6)."""

import pandas as pd

from etl.internacional.world_bank import Internacional_WorldBank


def test_transformar_limpia_valores():
    df = pd.DataFrame(
        {
            "indicador_codigo": ["NY.GDP.PCAP.PP.CD"] * 3,
            "indicador_nombre": ["PIB per cápita (PPA)"] * 3,
            "anio": ["2020", "2021", None],
            "valor": ["10000.5", None, "12000"],
        }
    )
    resultado = Internacional_WorldBank().transformar(df)
    assert len(resultado) == 1
    assert float(resultado["valor"].iloc[0]) == 10000.5
    assert int(resultado["anio"].iloc[0]) == 2020


def test_esqueleto_nacional_pendiente():
    from etl.fiscalia.pipeline import Fiscalia_Estadisticas

    assert Fiscalia_Estadisticas().pipeline_id == "fiscalia_estadisticas"
