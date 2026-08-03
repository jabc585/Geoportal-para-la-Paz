"""Pruebas del conector CNMH SIEVCAC (plan2.md Fase B, fuente 2).

DataFrames que replican los shapes reales verificados en vivo (2026-08-02):
- caso (atentados/reclutamiento): fila = caso, id_caso único.
- víctima (minas/desaparición/bienes/acciones): fila = persona, id_persona.
"""

import pandas as pd
import pytest

from etl.memoria.pipeline import HECHOS, CNMH_Memoria


def _df_casos():
    return pd.DataFrame(
        {
            "a_o": ["2020", "2020", "2021", "0", None],
            "c_digo_dane_de_municipio": ["5001", "5001", "5002", "5003", "5004"],
            "id_caso": ["c1", "c2", "c3", "c4", "c5"],
            "municipio": ["MEDELLIN", "MEDELLIN", "ABEJORRAL", "X", "Y"],
        }
    )


def _df_victimas():
    return pd.DataFrame(
        {
            "a_o": ["2020", "2020", "2020", "2021", "0"],
            "c_digo_dane_de_municipio": [5001, 5001, 5001, 5002, 5003],
            "id_caso": ["c1", "c1", "c2", "c3", "c4"],
            "id_persona": ["p1", "p1", "p2", "p3", "p4"],
            "sexo": ["F", "F", "M", "F", "M"],
        }
    )


def test_hechos_registrados_cubren_los_6_datasets_reales():
    assert set(HECHOS) == {
        "minas",
        "atentados",
        "desaparicion",
        "bienes",
        "reclutamiento",
        "acciones",
    }
    for cfg in HECHOS.values():
        assert cfg["variable"].startswith("CNMH_")
        assert "-" in cfg["resource_id"]  # formato Socrata real (p. ej. 52eu-ic7d)
        assert cfg["tipo"] in ("casos", "victimas")


def test_hecho_desconocido_rechazado():
    with pytest.raises(ValueError, match="Hecho CNMH desconocido"):
        CNMH_Memoria("homicidios")


def test_pipeline_id_por_hecho():
    assert CNMH_Memoria("minas").pipeline_id == "cnmh_minas"
    assert CNMH_Memoria("atentados").tabla_raw == "cnmh_atentados"


def test_transformar_casos_shape_real():
    resultado = CNMH_Memoria("atentados").transformar(_df_casos())
    filas = resultado.sort_values("codigo_divipola").to_dict("records")
    # 05001: 2 casos en 2020; 05002: 1 caso en 2021; a_o=0 y None descartados
    assert [f["valor"] for f in filas] == [2, 1]
    assert filas[0]["codigo_divipola"] == "05001"
    assert filas[0]["periodo_inicio"].year == 2020
    assert filas[0]["periodo_fin"].month == 12


def test_transformar_victimas_deduplica_personas():
    resultado = CNMH_Memoria("minas").transformar(_df_victimas())
    # p1 aparece dos veces en 05001/2020 → cuenta una sola; p2 segunda; p3 en 05002
    filas = resultado.sort_values("codigo_divipola").to_dict("records")
    assert [f["valor"] for f in filas] == [2, 1]


def test_transformar_vacio():
    assert CNMH_Memoria("acciones").transformar(pd.DataFrame()).empty


def test_extraer_paginacion_real(monkeypatch):
    """La paginación $limit/$offset debe cubrir datasets > 50.000 filas
    (desaparición tiene 82.486)."""

    def fake_get(url, params=None, headers=None, timeout=120):
        offset = params["$offset"]
        limite = params["$limit"]
        batch = [{"a_o": str(2020 + offset), "c_digo_dane_de_municipio": "05001"}]
        if offset == 0:
            batch = batch * limite  # primera página llena → fuerza segunda
        return _Resp(batch)

    monkeypatch.setattr("etl.common.descargas.requests.get", fake_get)
    monkeypatch.setattr(
        "etl.memoria.pipeline.get_source_url", lambda variable, ayuda="": "https://datos.gov.co/resource/c59y-p4sz.json"
    )
    df, lineage = CNMH_Memoria("desaparicion").extraer()
    assert len(df) == 50001  # 50000 + 1 de la segunda página
    assert "c59y-p4sz" in lineage.url_origen  # la URL viene de la variable configurada


class _Resp:
    def __init__(self, datos):
        self._datos = datos

    def raise_for_status(self):
        pass

    def json(self):
        return self._datos
