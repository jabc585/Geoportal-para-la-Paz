"""Tests del conector ACLED (agregados país-año en archivos locales)."""

from __future__ import annotations

import pandas as pd
import pytest

from etl.common.config import settings
from etl.internacional.acled import ARCHIVOS, Internacional_ACLED


@pytest.fixture()
def archivos_acled(tmp_path, monkeypatch):
    """Genera un XLSX mínimo por archivo esperado en un directorio temporal."""
    for nombre in ARCHIVOS:
        filas = [
            {"COUNTRY": "Colombia", "YEAR": 2024, "EVENTS": 100},
            {"COUNTRY": "Colombia", "YEAR": 2025, "EVENTS": 150},
            {"COUNTRY": "Venezuela", "YEAR": 2025, "EVENTS": 999},
            {"COUNTRY": "Colombia", "YEAR": "desconocido", "EVENTS": None},
        ]
        pd.DataFrame(filas).to_excel(tmp_path / nombre, index=False)
    monkeypatch.setattr(settings, "acled_data_dir", str(tmp_path))
    return tmp_path


def test_extraer_todos_los_archivos(archivos_acled):
    pipeline = Internacional_ACLED()
    df, lineage = pipeline.extraer()
    assert len(df) == 4 * len(ARCHIVOS)
    assert df["archivo"].nunique() == len(ARCHIVOS)
    assert lineage.fuente == "ACLED"
    assert lineage.licencia.startswith("ACLED")
    assert lineage.fecha_corte_dato == "2026-07-24"


def test_transformar_solo_colombia(archivos_acled):
    pipeline = Internacional_ACLED()
    df, _ = pipeline.extraer()
    out = pipeline.transformar(df)
    assert set(out.columns) == {"anio", "valor", "indicador", "unidad"}
    assert set(out["indicador"]) == {v[0] for v in ARCHIVOS.values()}
    assert out["valor"].notna().all()
    assert out["anio"].notna().all()
    assert out.loc[out["anio"] == 2024, "valor"].iloc[0] == 100


def test_transformar_descarta_fuera_de_colombia_y_nulos(archivos_acled):
    pipeline = Internacional_ACLED()
    df, _ = pipeline.extraer()
    out = pipeline.transformar(df)
    assert len(out) == 2 * len(ARCHIVOS)


def test_falta_archivo_lanza_file_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "acled_data_dir", str(tmp_path))
    pipeline = Internacional_ACLED()
    with pytest.raises(FileNotFoundError):
        pipeline.extraer()


def test_directorio_relativo_a_repo(monkeypatch):
    monkeypatch.setattr(settings, "acled_data_dir", "data/external")
    pipeline = Internacional_ACLED()
    assert pipeline._directorio().name == "external"
