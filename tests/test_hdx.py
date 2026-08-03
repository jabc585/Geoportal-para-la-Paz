"""Pruebas del conector HDX HAPI (plan2.md Fase B, fuente 4).

Replica el shape real del recurso Conflict Events de hdx-hapi-col verificado
en vivo (2026-08-02): filas mensuales por municipio con admin2_code estilo
"CO76890" (DIVIPOLA con prefijo CO), event_type, events y fatalities.
"""


import pandas as pd

from etl.internacional.hdx import INDICADORES, Internacional_HDX


def _df_conflictos():
    return pd.DataFrame(
        {
            "admin2_code": ["CO76890", "CO76890", "CO05040", "CO05040"],
            "admin2_name": ["Yotoco", "Yotoco", "Anorí", "Anorí"],
            "event_type": ["civilian_targeting", "civilian_targeting", "demonstration", "demonstration"],
            "events": [0, 2, 1, 3],
            "fatalities": [0.0, 5.0, 1.0, 0.0],
            "reference_period_start": ["2025-01-01", "2025-02-01", "2024-11-01", "2024-11-01"],
            "reference_period_end": ["2025-01-31", "2025-02-28", "2024-11-30", "2024-11-30"],
        }
    )


def test_indicadores_dos_metricas():
    assert [i["codigo"] for i in INDICADORES] == ["hdx_conflicto_eventos", "hdx_conflicto_fatalidades"]


def test_transformar_agrega_por_municipio_anio():
    resultado = Internacional_HDX().transformar(_df_conflictos())
    eventos = resultado[resultado["indicador"] == "hdx_conflicto_eventos"].sort_values("valor").to_dict("records")
    fatalidades = resultado[resultado["indicador"] == "hdx_conflicto_fatalidades"].to_dict("records")
    # Las filas mensuales colapsan por (municipio, año):
    # Yotoco 2025 = 0+2 eventos, Anorí 2024 = 1+3 eventos.
    assert len(eventos) == 2
    assert eventos[0]["codigo_divipola"] == "76890"
    assert eventos[0]["valor"] == 2
    assert eventos[0]["periodo_inicio"].year == 2025
    assert eventos[1]["codigo_divipola"] == "05040"
    assert eventos[1]["valor"] == 4
    assert fatalidades[0]["codigo_divipola"] == "05040"
    assert fatalidades[0]["valor"] == 1.0
    assert fatalidades[1]["valor"] == 5.0


def test_transformar_prefijo_co_se_descarta():
    df = _df_conflictos().head(1)
    resultado = Internacional_HDX().transformar(df)
    assert resultado["codigo_divipola"].iloc[0] == "76890"  # sin "CO"


def test_transformar_vacio():
    assert Internacional_HDX().transformar(pd.DataFrame()).empty


def test_url_firmada_via_resource_show(monkeypatch):
    """Debe resolver la URL de descarga (S3 firmada) con resource_show."""

    def fake_get(url, params=None, timeout=600, **kwargs):
        if "resource_show" in url:
            assert params == {"id": "bbdfa1bf-0dd3-4235-b20c-1bd6c0de365e"}
            return _Resp({"result": {"url": "https://s3.example/conflict.csv"}}, "json")
        return _Resp(b"admin2_code,admin2_name,event_type,events,fatalities,reference_period_start,reference_period_end\nCO76890,Yotoco,civilian_targeting,1,2.0,2025-01-01,2025-01-31\n", "content")

    monkeypatch.setattr("etl.internacional.hdx.requests.get", fake_get)
    monkeypatch.setattr(
        "etl.internacional.hdx.get_source_url",
        lambda variable, ayuda="": (
            "https://data.humdata.org/api/3"
            if variable == "HDX_BASE_URL"
            else "bbdfa1bf-0dd3-4235-b20c-1bd6c0de365e"
        ),
    )
    df, lineage = Internacional_HDX().extraer()
    assert len(df) == 1
    assert df["admin2_code"].iloc[0] == "CO76890"
    assert "s3.example" in lineage.url_origen


class _Resp:
    def __init__(self, datos, tipo):
        self._datos = datos
        self._tipo = tipo

    def raise_for_status(self):
        pass

    def json(self):
        return self._datos

    @property
    def content(self):
        return self._datos

    def iter_content(self, chunk_size=1024 * 1024):
        yield self._datos

    def close(self):
        pass
