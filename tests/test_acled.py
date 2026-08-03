"""Tests del conector ACLED (agregados país-año y departamento-año)."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from etl.common.cargar import slugificar
from etl.common.config import settings
from etl.internacional.acled import ARCHIVO_ADMIN1, ARCHIVOS, Internacional_ACLED


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
    # La fecha de corte se deriva de los datos, no es un literal: el año máximo
    # del fixture es 2025 (antes estaba escrita a mano y envejecía sola).
    assert lineage.fecha_corte_dato == date(2025, 12, 31)


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


# ── Capa departamental (admin1 → DIVIPOLA) ────────────────────────────────

def _df_admin1():
    return pd.DataFrame(
        {
            "COUNTRY": ["Colombia", "Colombia", "Colombia", "Venezuela", "Colombia"],
            "ADMIN1": ["Bogota, D.C.", "Antioquia", "Narino", "Caracas", "Bogota, D.C."],
            "WEEK": ["2025-01-04", "2025-01-04", "2025-01-04", "2025-01-04", "2025-03-01"],
            "EVENTS": [3, 1, 2, 99, 4],
            "FATALITIES": [0, 5, 1, 999, 2],
            "archivo": ARCHIVO_ADMIN1,
        }
    )


def test_slugificar_empareja_tildes_y_puntos():
    assert slugificar("Nariño") == slugificar("Narino")
    assert slugificar("Bogotá, D.C.") == slugificar("Bogota, D.C.") == "bogota_d_c"
    assert slugificar("SAN ANDRÉS Y PROVIDENCIA") == "san_andres_y_providencia"


def test_transformar_admin1_mapea_y_agrega(monkeypatch):
    pipeline = Internacional_ACLED()
    monkeypatch.setattr(
        pipeline,
        "_mapeo_admin1",
        lambda: {"bogota_d_c": "11", "antioquia": "05", "narino": "52"},
    )
    out = pipeline.transformar_admin1(_df_admin1())
    bogota_ev = out[(out["codigo_divipola"] == "11") & (out["indicador_codigo"] == "acled_eventos_departamento")]
    assert bogota_ev["valor"].iloc[0] == 7  # 3 + 4 (dos semanas del mismo año)
    assert bogota_ev["anio"].iloc[0] == 2025
    assert out[out["codigo_divipola"] == "05"]["valor"].iloc[0] == 1
    assert out[out["indicador_codigo"] == "acled_fatalidades_departamento"]["valor"].sum() == 8
    # Venezuela y los admin1 sin mapeo no aparecen
    assert not out[out["codigo_divipola"].isin(["caracas", "99"])].any(axis=None)


def test_transformar_admin1_sin_archivo_devuelve_vacio():
    pipeline = Internacional_ACLED()
    df = pd.DataFrame({"COUNTRY": ["Colombia"], "archivo": ["otro.xlsx"]})
    assert pipeline.transformar_admin1(df).empty


def test_extraer_incluye_admin1_si_existe(tmp_path, monkeypatch):
    for nombre in ARCHIVOS:
        pd.DataFrame([{"COUNTRY": "Colombia", "YEAR": 2025, "EVENTS": 1}]).to_excel(
            tmp_path / nombre, index=False
        )
    filas = [
        {"COUNTRY": "Colombia", "ADMIN1": "Antioquia", "WEEK": "2025-01-04", "EVENTS": 1, "FATALITIES": 0},
        {"COUNTRY": "Peru", "ADMIN1": "Lima", "WEEK": "2025-01-04", "EVENTS": 1, "FATALITIES": 0},
    ]
    pd.DataFrame(filas).to_excel(tmp_path / ARCHIVO_ADMIN1, index=False)
    monkeypatch.setattr(settings, "acled_data_dir", str(tmp_path))
    df, _ = Internacional_ACLED().extraer()
    assert (df["archivo"] == ARCHIVO_ADMIN1).any()
    # solo Colombia del admin1 llega a raw
    admin1 = df[df["archivo"] == ARCHIVO_ADMIN1]
    assert len(admin1) == 1
    assert admin1.iloc[0]["ADMIN1"] == "Antioquia"
