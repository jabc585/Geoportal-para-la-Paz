"""Pruebas de la validación de frescura y del sellado de fuentes (migración 0015).

No tocan la BD: verifican la lógica pura de clasificación y resumen, y que
`marcar_fuente_actualizada` emita el UPDATE esperado con un cursor simulado.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

import pandas as pd
import pytest

from etl.common.cargar import marcar_fuente_actualizada, periodo_maximo
from etl.common.frescura import ESTADOS, resumen


class _CursorFalso:
    def __init__(self):
        self.ejecutados = []

    def execute(self, sql, params=None):
        self.ejecutados.append((sql, params))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class _ConexionFalsa:
    def __init__(self):
        self.cur = _CursorFalso()

    def cursor(self, *args, **kwargs):
        return self.cur


# ── periodo_maximo ────────────────────────────────────────────────────────────

def test_periodo_maximo_toma_la_fecha_mas_reciente():
    df = pd.DataFrame({"periodo_fin": ["2020-12-31", "2025-12-31", "2023-12-31"]})
    assert periodo_maximo(df) == date(2025, 12, 31)


def test_periodo_maximo_ignora_fechas_invalidas():
    df = pd.DataFrame({"periodo_fin": ["no-es-fecha", "2024-06-30"]})
    assert periodo_maximo(df) == date(2024, 6, 30)


def test_periodo_maximo_sin_columna_o_vacio_devuelve_none():
    assert periodo_maximo(pd.DataFrame()) is None
    assert periodo_maximo(pd.DataFrame({"otra": [1]})) is None
    assert periodo_maximo(pd.DataFrame({"periodo_fin": [None, None]})) is None


# ── marcar_fuente_actualizada ─────────────────────────────────────────────────

def test_marcar_fuente_actualizada_emite_update_con_greatest():
    conn = _ConexionFalsa()
    ahora = datetime(2026, 8, 3, tzinfo=timezone.utc)
    marcar_fuente_actualizada(conn, fuente_id=7, fecha_extraccion=ahora,
                              fecha_corte_dato=date(2025, 12, 31))

    sql, params = conn.cur.ejecutados[0]
    assert "UPDATE curated.fuentes" in sql
    # GREATEST evita que una recarga de datos viejos retroceda el sello.
    assert "GREATEST" in sql
    assert params["fuente_id"] == 7
    assert params["extraccion"] == ahora
    assert params["corte"] == date(2025, 12, 31)


def test_marcar_fuente_actualizada_acepta_corte_nulo():
    conn = _ConexionFalsa()
    marcar_fuente_actualizada(conn, 1, datetime(2026, 1, 1, tzinfo=timezone.utc))
    _, params = conn.cur.ejecutados[0]
    assert params["corte"] is None


# ── resumen de frescura ───────────────────────────────────────────────────────

def test_resumen_cuenta_cada_estado():
    filas = [
        {"frescura": "al_dia"},
        {"frescura": "al_dia"},
        {"frescura": "obsoleta"},
        {"frescura": "retrasada"},
    ]
    assert resumen(filas) == {
        "al_dia": 2,
        "retrasada": 1,
        "obsoleta": 1,
        "sin_datos": 0,
    }


def test_resumen_incluye_todos_los_estados_aunque_valgan_cero():
    assert set(resumen([])) == set(ESTADOS)
    assert all(v == 0 for v in resumen([]).values())


def test_resumen_trata_frescura_nula_como_sin_datos():
    assert resumen([{"frescura": None}])["sin_datos"] == 1


# ── clasificación (misma aritmética que la vista SQL) ─────────────────────────

def clasificar(dias: int | None, periodicidad_dias: int) -> str:
    """Réplica en Python de curated.vw_frescura_fuentes, para fijar el contrato."""
    if dias is None:
        return "sin_datos"
    if dias <= periodicidad_dias:
        return "al_dia"
    if dias <= periodicidad_dias * 2:
        return "retrasada"
    return "obsoleta"


@pytest.mark.parametrize(
    "dias,periodo,esperado",
    [
        (0, 30, "al_dia"),
        (30, 30, "al_dia"),      # el límite exacto sigue siendo al día
        (31, 30, "retrasada"),
        (60, 30, "retrasada"),   # el doble exacto todavía es retraso
        (61, 30, "obsoleta"),
        (400, 365, "retrasada"),
        (800, 365, "obsoleta"),
        (None, 30, "sin_datos"),
    ],
)
def test_umbrales_de_frescura(dias, periodo, esperado):
    assert clasificar(dias, periodo) == esperado
