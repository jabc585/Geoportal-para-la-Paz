"""Tests de la siembra DIVIPOLA (plan.md §F2.4)."""

from __future__ import annotations

from etl.common.divipola import ANMS_FALTANTES, DEFAULT_DEPT_DATASET, DEFAULT_MUN_DATASET


def test_anms_faltantes_bien_formadas():
    for codigo, nombre, depto in ANMS_FALTANTES:
        assert len(codigo) == 5, f"código {codigo} no tiene 5 dígitos"
        assert codigo.isdigit(), f"código {codigo} no es numérico"
        assert len(nombre) > 0, f"nombre vacío para {codigo}"
        assert len(depto) == 2, f"depto {depto} no tiene 2 dígitos"
        assert depto.isdigit(), f"depto {depto} no es numérico"


def test_datasets_default_son_ids_socrata_validos():
    assert len(DEFAULT_DEPT_DATASET) == 9  # formato xxxx-xxxx
    assert len(DEFAULT_MUN_DATASET) == 9
    assert DEFAULT_DEPT_DATASET[4] == "-"


def test_descargar_usa_url_socrata_correcta(monkeypatch):
    """Verifica que _descargar construye la URL correcta."""
    from etl.common.divipola import _descargar, URL_SOCRATA

    llamadas = []

    def fake_paginado(url, **kwargs):
        llamadas.append(url)
        return []

    monkeypatch.setattr("etl.common.divipola.descargar_socrata_paginado", fake_paginado)
    _descargar("test-id")
    assert len(llamadas) == 1
    assert llamadas[0] == f"{URL_SOCRATA}/test-id.json"
