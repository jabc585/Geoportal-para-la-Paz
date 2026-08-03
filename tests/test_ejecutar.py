"""Tests de PipelineETL.ejecutar(): los 6 caminos donde se introdujeron
los bugs de métricas (plan.md §F2.2, auditoría §4.1)."""

from __future__ import annotations

import pandas as pd
import pytest

from etl.common.lineage import Lineage
from etl.common.pipeline import PipelineETL


class CursorFake:
    def __init__(self, fetchone_result=None, rowcount=0):
        self.ejecutadas: list[str] = []
        self._fetchone_result = fetchone_result
        self.rowcount = rowcount

    def execute(self, sql, params=None):
        self.ejecutadas.append(sql)
        return self

    def executemany(self, sql, params):
        self.ejecutadas.append(sql)
        return self

    def fetchone(self):
        return self._fetchone_result

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class ConexionFake:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0
        self.cerrada = False
        self.cursors: list[CursorFake] = []

    def cursor(self):
        c = CursorFake()
        self.cursors.append(c)
        return c

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.cerrada = True


LINEAGE = Lineage.ahora(
    fuente="test", url_origen="test://", fecha_corte_dato=None, licencia="test"
)


class FakePipeline(PipelineETL):
    """Pipeline sintético con parámetros inyectables para cada camino."""

    pipeline_id = "test_fake"
    tabla_raw = "test_fake"

    def __init__(self, filas_extraer=10, fallo_extraer=False,
                 rechazados_override=None, leidos_override=None,
                 filas_validas=None):
        super().__init__()
        self._fallo_extraer = fallo_extraer
        self._filas_extraer = filas_extraer
        self._rechazados_val = rechazados_override
        self._leidos_val = leidos_override
        self._filas_validas = filas_validas if filas_validas is not None else filas_extraer

    def extraer(self):
        if self._fallo_extraer:
            raise RuntimeError("fuente caída")
        df = pd.DataFrame({"x": range(self._filas_extraer)})
        return df, LINEAGE

    def transformar(self, df):
        if self._rechazados_val is not None:
            self._rechazados = self._rechazados_val
        if self._leidos_val is not None:
            self._leidos = self._leidos_val
        if self._filas_validas > len(df):
            return pd.DataFrame({"x": range(self._filas_validas)})
        return df.head(self._filas_validas)

    def cargar_curated(self, df):
        pass


def _mock_conexion(monkeypatch, conn):
    monkeypatch.setattr("etl.common.pipeline.conectar", lambda: conn)
    monkeypatch.setattr("etl.common.pipeline.insertar_raw", lambda c, t, filas: len(filas))


# ── Camino 1: éxito simple ────────────────────────────────────────────────

def test_ejecutar_exito_simple(monkeypatch):
    conn = ConexionFake()
    _mock_conexion(monkeypatch, conn)
    FakePipeline(filas_extraer=10).ejecutar()
    assert conn.commits >= 2
    assert conn.cerrada


# ── Camino 2: fallo en extraer() ───────────────────────────────────────────

def test_ejecutar_fallo_extraer_estado_fallido(monkeypatch):
    conn = ConexionFake()
    _mock_conexion(monkeypatch, conn)
    with pytest.raises(RuntimeError, match="fuente caída"):
        FakePipeline(filas_extraer=10, fallo_extraer=True).ejecutar()
    assert conn.commits == 1  # solo métricas (datos en rollback)
    assert conn.cerrada


# ── Camino 3: canal lateral con _leidos correcto ───────────────────────────

def test_ejecutar_canal_lateral_con_leidos(monkeypatch):
    conn = ConexionFake()
    _mock_conexion(monkeypatch, conn)
    # extraer() → 1 fila, transformar() → 100 filas, _leidos=100
    FakePipeline(filas_extraer=1, filas_validas=100,
                 leidos_override=100, rechazados_override=0).ejecutar()
    assert conn.commits >= 2
    assert conn.cerrada


# ── Camino 4: canal lateral sin _leidos → aviso F0.3 ───────────────────────

def test_ejecutar_sin_leidos_avisa(caplog, monkeypatch):
    import logging

    conn = ConexionFake()
    _mock_conexion(monkeypatch, conn)
    caplog.set_level(logging.WARNING, logger="etl.test_fake")
    FakePipeline(filas_extraer=1, filas_validas=100).ejecutar()
    assert "métricas incoherentes" in caplog.text
    assert conn.commits >= 2  # carga de datos sí commiteó
    assert conn.cerrada


# ── Camino 5: umbral de parcial (>20% rechazo) ─────────────────────────────

def test_ejecutar_umbral_parcial(monkeypatch):
    conn = ConexionFake()
    _mock_conexion(monkeypatch, conn)
    FakePipeline(filas_extraer=10, filas_validas=5,
                 rechazados_override=5).ejecutar()
    assert conn.commits >= 2
    assert conn.cerrada


# ── Camino 6: fallo de registrar_metricas no invalida carga ─────────────────

def test_ejecutar_metricas_fallan_no_invalida(caplog, monkeypatch):
    import logging

    conn = ConexionFake()
    _mock_conexion(monkeypatch, conn)

    def _metricas_rotas(*a, **kw):
        raise RuntimeError("métricas rotas")

    monkeypatch.setattr("etl.common.pipeline.registrar_metricas", _metricas_rotas)
    caplog.set_level(logging.WARNING, logger="etl.test_fake")

    FakePipeline(filas_extraer=10).ejecutar()  # no lanza
    assert "no se registraron métricas" in caplog.text
    assert conn.commits >= 1
    assert conn.cerrada
