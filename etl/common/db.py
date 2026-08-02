"""Conexión a base de datos y registro de métricas de calidad (secciones 7.3 y 7.4)."""

from __future__ import annotations

import os

import psycopg


def conectar() -> psycopg.Connection:
    url = os.getenv("DATABASE_URL", "postgresql://observatorio:observatorio_dev@localhost:5432/observatorio")
    return psycopg.connect(url, autocommit=True)


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
                    psycopg.types.json.Jsonb(f["contenido"]),
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
