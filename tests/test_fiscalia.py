"""Pruebas del conector Fiscalía V3 (plan2.md Fase B, fuente 3).

El pipeline usa la agregación server-side de SoQL ($select/$group) por el
volumen real de los datasets (23M procesos, 17.5M víctimas). Estos tests
replican el shape del resultado agregado verificado en vivo (2026-08-02):
{anio, codigo, dimension, n}.
"""

import pandas as pd
import pytest

from etl.fiscalia.pipeline import DATASETS, Fiscalia_Estadisticas


def _df_agregado():
    return pd.DataFrame(
        {
            "codigo": ["05001", "05001", "05002", "05003"],
            "anio": ["2020", "2020", "2021", "0"],
            "dimension": [
                "Delitos Contra La Familia",
                "Delitos Contra La Familia",
                "Delitos Contra La Vida",
                "Delitos Contra La Familia",
            ],
            "n": ["2", "7", "3", "9"],
        }
    )


def test_datasets_cubren_los_dos_shapes_reales():
    assert set(DATASETS) == {"procesos", "victimas"}
    assert DATASETS["procesos"]["resource_id"] == "dbdv-iihs"
    assert DATASETS["victimas"]["resource_id"] == "hr73-zqjf"


def test_dataset_desconocido_rechazado():
    with pytest.raises(ValueError, match="Dataset Fiscalía desconocido"):
        Fiscalia_Estadisticas("procesados")


def test_pipeline_id_por_dataset():
    assert Fiscalia_Estadisticas("procesos").pipeline_id == "fiscalia_procesos"
    assert Fiscalia_Estadisticas("victimas").tabla_raw == "fiscalia_victimas"


def test_transformar_shape_agregado():
    resultado = Fiscalia_Estadisticas("procesos").transformar(_df_agregado())
    filas = resultado.sort_values("valor").to_dict("records")
    assert len(filas) == 3  # a_o=0 descartado
    assert filas[0]["valor"] == 2
    assert filas[0]["codigo_divipola"] == "05001"
    assert filas[0]["dimension"] == "Delitos Contra La Familia"
    assert filas[2]["codigo_divipola"] == "05001"
    assert filas[2]["valor"] == 7
    assert filas[1]["codigo_divipola"] == "05002"
    assert filas[1]["periodo_inicio"].year == 2021


def test_transformar_sin_dimension_usa_sin_informacion():
    df = pd.DataFrame(
        {
            "codigo": ["05001"],
            "anio": ["2020"],
            "dimension": [None],
            "n": ["1"],
        }
    )
    resultado = Fiscalia_Estadisticas("procesos").transformar(df)
    assert resultado["dimension"].iloc[0] == "Sin información"


def test_transformar_nulos_en_valor():
    df = pd.DataFrame(
        {
            "codigo": ["05001"],
            "anio": ["2020"],
            "dimension": ["X"],
            "n": [None],
        }
    )
    assert Fiscalia_Estadisticas("procesos").transformar(df).empty


def test_extraer_usa_agregacion_soql(monkeypatch):
    """Debe pedir count(*) + $group, no filas individuales (diseño por volumen)."""

    def fake_get(url, params=None, timeout=600):
        assert "count(*)" in params["$select"]
        assert "$group" in params
        return _Resp([{"codigo": "05001", "anio": "2020", "dimension": "X", "n": "1"}])

    from etl.common.config import settings

    monkeypatch.setattr(settings, "fiscalia_procesos_url", "https://www.datos.gov.co/resource/dbdv-iihs.json")
    monkeypatch.setattr("etl.fiscalia.pipeline.requests.get", fake_get)
    df, lineage = Fiscalia_Estadisticas("procesos").extraer()
    assert len(df) == 1
    assert "dbdv-iihs" in lineage.url_origen


def test_transformar_vacio():
    assert Fiscalia_Estadisticas("procesos").transformar(pd.DataFrame()).empty


class _Resp:
    def __init__(self, datos):
        self._datos = datos

    def raise_for_status(self):
        pass

    def json(self):
        return self._datos
