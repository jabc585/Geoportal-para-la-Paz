"""Tests del conector de víctimas (UARIV vía Socrata municipal, dataset 9qih-4vkc).

El CSV de Datos Paz (VICTIMAS_URL) devuelve 404 desde hace meses; el conector
cae al resource Socrata municipal oficial de la UARIV, cuyo total por corte
coincide con la cifra oficial de personas incluidas en el RUV.
"""

from datetime import date

from etl.victimas.pipeline import SOCRATA_MUNICIPAL, Victimas_Hechos, _parsear_corte


class _RespJson:
    def __init__(self, contenido, ok=True):
        self._c = contenido
        self.ok = ok

    def raise_for_status(self):
        if not self.ok:
            raise AssertionError("error")

    def json(self):
        return self._c


def _fake_get_socrata(monkeypatch):
    cortes = [
        {"fecha_corte": "30/06/2026"},
        {"fecha_corte": "31/12/2025"},
        {"fecha_corte": "31/12/2024"},
        {"fecha_corte": "30/09/24"},
        {"fecha_corte": "31/07/2024 00:00"},
    ]
    agregados = [
        {"cod_estado_depto": "5", "cod_ciudad_muni": "5001", "per_sa": "1000"},
        {"cod_estado_depto": "5", "cod_ciudad_muni": "5002", "per_sa": "500"},
        {"cod_estado_depto": "0", "cod_ciudad_muni": "0", "per_sa": "42"},
    ]

    def fake_get(url, timeout=120):
        if "hechos_victimizantes" in url:
            return _RespJson([], ok=False)  # CSV de Datos Paz: 404 hoy
        if "$group=fecha_corte" in url:
            return _RespJson(cortes)
        return _RespJson(agregados)

    monkeypatch.setattr("etl.victimas.pipeline.requests.get", fake_get)
    return fake_get


def test_parsear_corte_formatos_mixtos():
    assert _parsear_corte("31/12/2025").year == 2025
    assert _parsear_corte("30/09/24").year == 2024
    assert _parsear_corte("31/07/2024 00:00").month == 7


def test_extraer_socrata_conserva_sin_definir_como_nacional(monkeypatch):
    _fake_get_socrata(monkeypatch)
    p = Victimas_Hechos()
    df, lineage = p.extraer()
    assert lineage.fuente == "Unidad para las Víctimas"
    assert "9qih" in lineage.url_origen
    # Dos cortes por año (2024, 2025, 2026) -> 3 años x (2 municipios + 1 nacional) = 9 filas
    assert len(df) == 9
    assert set(df["anio"]) == {2024, 2025, 2026}
    assert set(df["codigo_divipola"]) == {"05001", "05002", "00000"}
    assert df["codigo_divipola"].str.len().eq(5).all()
    nacional = df[df["codigo_divipola"] == "00000"]
    assert len(nacional) == 3
    assert nacional["valor"].eq(42).all()


def test_transformar_agrupa_por_municipio_anio(monkeypatch):
    _fake_get_socrata(monkeypatch)
    p = Victimas_Hechos()
    df, _ = p.extraer()
    out = p.transformar(df)
    assert set(out.columns) >= {"codigo_divipola", "periodo_inicio", "periodo_fin", "valor"}
    fila_2025 = out[(out["codigo_divipola"] == "05001") & (out["periodo_fin"] == date(2025, 12, 31))]
    assert len(fila_2025) == 1
    assert fila_2025.iloc[0]["valor"] == 1000


def test_extraer_cae_a_socrata_cuando_victimas_url_no_responde(monkeypatch):
    fake_get = _fake_get_socrata(monkeypatch)
    real_get = fake_get

    def get_con_404(url, timeout=120):
        if "hechos_victimizantes" in url:
            return _RespJson([], ok=False)
        return real_get(url, timeout)

    monkeypatch.setattr("etl.victimas.pipeline.requests.get", get_con_404)
    monkeypatch.setenv("VICTIMAS_URL", "https://datospaz.unidadvictimas.gov.co/archivos/datosabiertos")
    p = Victimas_Hechos()
    df, lineage = p.extraer()
    assert not df.empty
    assert SOCRATA_MUNICIPAL in lineage.url_origen
