"""Pool de conexiones para la API (plan3.md, Fase 1.8).

Las funciones de servicio en consultas.py y health.py abrían una conexión
nueva por cada request. Con el pool se reutilizan conexiones ya establecidas,
evitando el costo de handshake TCP+auth de PostgreSQL en cada request.
"""

from __future__ import annotations

import os
from contextlib import contextmanager

import psycopg
from psycopg_pool import ConnectionPool

_pool: ConnectionPool | None = None


def _get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        url = os.getenv("DATABASE_URL", "postgresql://observatorio:observatorio_dev@localhost:5432/observatorio")
        _pool = ConnectionPool(url, open=False)
        _pool.open()
    return _pool


@contextmanager
def obtener_conexion() -> psycopg.Connection:
    """Devuelve una conexión del pool (ya con autocommit=True para solo lectura)."""
    pool = _get_pool()
    with pool.connection() as conn:
        conn.autocommit = True
        yield conn
