"""Conexión a base de datos y registro de métricas de calidad (secciones 7.3 y 7.4)."""

from __future__ import annotations

import math
import os
from contextlib import contextmanager

import psycopg

URL_DEFAULT = "postgresql://observatorio:observatorio_dev@localhost:5432/observatorio"


def conectar(autocommit: bool = False) -> psycopg.Connection:
    """Abre una conexión con semántica transaccional real (auditoría 2026-08-02).

    autocommit=False por defecto: cada `executemany`/`execute` se acumula en una
    transacción que solo se confirma con commit() explícito (rollback en error).
    La API (solo lectura) pasa autocommit=True para evitar transacciones ociosas.
    """
    url = os.getenv("DATABASE_URL", URL_DEFAULT)
    return psycopg.connect(url, autocommit=autocommit)


@contextmanager
def transaccion(conn: psycopg.Connection):
    """Contexto transaccional: commit al salir sin error, rollback con error.

    A diferencia de `with conn:` (psycopg3), NO cierra la conexión al salir:
    la conexión la gestiona PipelineETL.ejecutar() para toda la corrida
    (hallazgo de auditoría 2026-08-02: el contexto nativo cerraba la conexión
    y registrar_metricas reabría una huérfana).
    """
    try:
        yield conn
    except BaseException:
        conn.rollback()
        raise
    else:
        conn.commit()


def sanear_json(valor):
    """Convierte NaN/NaT/NA a None recursivamente (hallazgo de auditoría 2026-08-02).

    Python serializa NaN como el token `NaN`, que Postgres jsonb rechaza
    ("Token NaN is invalid"). El saneo en la frontera de serialización evita
    que cualquier pipeline con celdas vacías legítimas rompa raw.*.
    """
    if valor is None:
        return None
    if isinstance(valor, dict):
        return {k: sanear_json(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [sanear_json(v) for v in valor]
    if isinstance(valor, float) and math.isnan(valor):
        return None
    if hasattr(valor, "item") and not isinstance(valor, (str, bytes)):
        # numpy/pandas escalares: se evaluan con pd.isna y se devuelve el
        # escalar Python nativo en vez del wrapper numpy (serializable JSON)
        try:
            import numpy as np  # noqa: F401 — detecta tipos numpy para .item()

            escalar = valor.item()
            if isinstance(escalar, float) and math.isnan(escalar):
                return None
            return escalar
        except (ValueError, ImportError):
            pass
    try:
        import pandas as pd

        resultado = pd.isna(valor)
        if isinstance(resultado, bool) and resultado:
            return None
    except (TypeError, ValueError):
        pass
    return valor


def insertar_raw(conn: psycopg.Connection, tabla: str, filas: list[dict]) -> int:
    """Inserta filas en raw.<tabla> conservando linaje (sección 7.3)."""
    if not filas:
        return 0
    columnas = ["archivo", "contenido", "url_origen", "fecha_extraccion", "hash_fila"]
    with conn.cursor() as cur:
        cur.executemany(
            f"INSERT INTO raw.{tabla} ({', '.join(columnas)}) "
            f"VALUES ({', '.join(['%s'] * len(columnas))})",
            [
                (
                    f["archivo"],
                    psycopg.types.json.Jsonb(sanear_json(f["contenido"])),
                    f["url_origen"],
                    f["fecha_extraccion"],
                    f["hash_fila"],
                )
                for f in filas
            ],
        )
    return len(filas)


def registrar_metricas(
    conn: psycopg.Connection,
    pipeline_id: str,
    registros_leidos: int,
    registros_validos: int,
    registros_rechazados: int,
    nulos: dict,
    duracion_segundos: float,
    estado: str,
    mensaje_error: str | None = None,
) -> None:
    """Registra métricas de calidad de la corrida (sección 7.4)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO curated.data_quality_metrics
                (pipeline_id, timestamp_ejecucion, registros_leidos, registros_validos,
                 registros_rechazados, nulos_por_columna_critica, duracion_segundos,
                 estado, mensaje_error)
            VALUES (%s, now(), %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                pipeline_id,
                registros_leidos,
                registros_validos,
                registros_rechazados,
                psycopg.types.json.Jsonb(nulos),
                duracion_segundos,
                estado,
                mensaje_error,
            ),
        )
