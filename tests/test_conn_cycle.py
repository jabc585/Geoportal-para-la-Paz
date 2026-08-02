"""Tests del ciclo de vida de conexión y carga con cursor simulado
(auditoría 2026-08-02, hallazgo 8: cobertura donde más se necesita).

El fake de psycopg registra ejecuciones y NO toca PostgreSQL.
"""

from datetime import date

import pandas as pd
import pytest

from etl.common.cargar import insertar_serie
from etl.common.db import insertar_raw, registrar_metricas, transaccion


class CursorFake:
    def __init__(self, fetchone_result=None, rowcount=0):
        self.ejecutadas: list[str] = []
        self._fetchone_result = fetchone_result
        self.rowcount = rowcount
        self.ejecutemany_params: list[tuple] | None = None
        self.sql_ejecutemany: str | None = None

    def execute(self, sql, params=None):
        self.ejecutadas.append(sql)
        return self

    def executemany(self, sql, params):
        self.sql_ejecutemany = sql
        self.ejecutemany_params = params
        return self

    def fetchone(self):
        return self._fetchone_result

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class ConexionFake:
    def __init__(self, fetchone_result=None, rowcount=0):
        self.cerrada = False
        self.commits = 0
        self.rollbacks = 0
        self._fetchone_result = fetchone_result
        self._rowcount = rowcount
        self.cursors: list[CursorFake] = []

    def cursor(self):
        c = CursorFake(self._fetchone_result, self._rowcount)
        self.cursors.append(c)
        return c

    @property
    def cur(self) -> CursorFake:
        return self.cursors[-1]

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.cerrada = True


def test_transaccion_commitea_y_no_cierra_la_conexion():
    """El contrato de transaccion(): commit al salir, sin close (hallazgo 3)."""
    conn = ConexionFake()
    with transaccion(conn) as c:
        assert c is conn
    assert conn.commits == 1
    assert conn.cerrada is False


def test_transaccion_hace_rollback_con_error():
    conn = ConexionFake()
    with pytest.raises(RuntimeError):
        with transaccion(conn):
            raise RuntimeError("boom")
    assert conn.rollbacks == 1
    assert conn.commits == 0
    assert conn.cerrada is False


def test_insertar_raw_envia_todas_las_filas_en_un_executemany():
    conn = ConexionFake()
    n = insertar_raw(
        conn,
        "victimas",
        [
            {"archivo": "a.json", "contenido": {"x": 1}, "url_origen": "u", "fecha_extraccion": date(2026, 1, 1), "hash_fila": "h1"},
            {"archivo": "b.json", "contenido": {"x": 2}, "url_origen": "u", "fecha_extraccion": date(2026, 1, 1), "hash_fila": "h2"},
        ],
    )
    assert n == 2
    assert len(conn.cur.ejecutemany_params) == 2
    assert "INSERT INTO raw.victimas" in conn.cur.sql_ejecutemany


def test_insertar_raw_vacio_no_consulta():
    conn = ConexionFake()
    assert insertar_raw(conn, "x", []) == 0
    assert conn.cursors == []


def test_registrar_metricas_inserta_con_nulos_jsonb():
    conn = ConexionFake()
    registrar_metricas(
        conn,
        "dane",
        10,
        8,
        2,
        {"valor": 1},
        1.5,
        "exitoso",
    )
    sql = conn.cur.ejecutadas[0]
    assert "INSERT INTO curated.data_quality_metrics" in sql


def test_insertar_serie_resuelve_territorio_una_vez_por_codigo():
    """Batch: el SELECT de territorio se hace 2 veces (2 códigos) y el INSERT
    una sola vez con todas las filas (anti N+1, hallazgo 5)."""
    conn = ConexionFake(fetchone_result=(7, 25), rowcount=3)
    df = pd.DataFrame(
        {
            "indicador_id": [1, 1, 2],
            "codigo_divipola": ["05001", "05001", "11001"],
            "periodo_inicio": [date(2025, 1, 1)] * 3,
            "periodo_fin": [date(2025, 12, 31)] * 3,
            "valor": [1.0, 2.0, 3.0],
        }
    )
    n = insertar_serie(conn, df, fuente_id=3, url_origen="u", fecha_extraccion=date(2026, 1, 1))
    selects = sum(
        1 for c in conn.cursors for s in c.ejecutadas if s.startswith("SELECT")
    )
    assert selects == 2  # memoizado por código único; sin memo serían 3
    assert len(conn.cur.ejecutemany_params) == 3
    assert n == 3


def test_insertar_serie_descarta_sin_territorio_y_avisa(capsys):
    conn = ConexionFake(fetchone_result=None, rowcount=0)
    df = pd.DataFrame(
        {
            "indicador_id": [1],
            "codigo_divipola": ["99999"],
            "periodo_inicio": [date(2025, 1, 1)],
            "periodo_fin": [date(2025, 12, 31)],
            "valor": [1.0],
        }
    )
    assert insertar_serie(conn, df, fuente_id=3, url_origen="u", fecha_extraccion=date(2026, 1, 1)) == 0
    assert "descartadas por territorio" in capsys.readouterr().out
