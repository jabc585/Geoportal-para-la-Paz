"""Pruebas de los conectores internacionales (secciones 5.2, 7.6; plan2.md Fase B)."""

import pandas as pd

from etl.internacional.unhcr import Internacional_UNHCR, TIPOS_POBLACION
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



UNHCR_ITEM_REAL = {
    "year": 2023,
    "coo": "COL",
    "coa": "-",
    "refugees": 115513,
    "asylum_seekers": 301824,
    "returned_refugees": 5,
    "idps": 6918373,
    "returned_idps": "0",
    "stateless": "0",
    "ooc": 532962,
    "oip": "-",
}


def test_unhcr_extraer_shape_real(monkeypatch):
    """Replica el shape real de la API (verificado en vivo 2026-08-02)."""
    import requests

    def fake_get(url, params=None, timeout=60):
        assert params == {"coo": "COL"}

        class Resp:
            def raise_for_status(self):
                pass

            def json(self):
                return {"items": [UNHCR_ITEM_REAL]}

        return Resp()

    monkeypatch.setattr(requests, "get", fake_get)
    df, lineage = Internacional_UNHCR().extraer()
    assert len(df) == len(TIPOS_POBLACION)
    assert df["valor"].tolist() == [115513, 301824, 5, 6918373, "0", "0", 532962, "-"]
    assert lineage.fuente == "UNHCR"
    assert "population/" in lineage.url_origen


def test_unhcr_transformar_limpia_no_datos():
    df = pd.DataFrame(
        {
            "indicador": ["Población refugiada colombiana"] * 4,
            "anio": ["2023", "2024", "2025", None],
            "valor": ["115513", "0", "-", "300"],
        }
    )
    resultado = Internacional_UNHCR().transformar(df)
    assert len(resultado) == 2  # "0" se conserva (es un dato válido), "-" y sin año se descartan
    assert resultado["valor"].iloc[0] == 115513.0


def test_unhcr_tipos_poblacion_completos():
    """Los 8 tipos que expone la API real deben estar mapeados."""
    assert set(TIPOS_POBLACION) == {
        "refugees",
        "asylum_seekers",
        "returned_refugees",
        "idps",
        "returned_idps",
        "stateless",
        "ooc",
        "oip",
    }
