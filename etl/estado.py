"""Alerta operativa: estado de la última corrida de cada pipeline
(plan.md §F6.2). Devuelve exit 0 si todo OK, exit 1 si hay fallidos
o parciales.

Uso: python -m etl.estado   (apto para cron / workflow schedule)
"""

from __future__ import annotations

import sys

from psycopg.rows import dict_row

from etl.common.db import conectar


def estado() -> int:
    with conectar(autocommit=True) as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT pipeline_id, estado, registros_rechazados,
                   timestamp_ejecucion, mensaje_error
            FROM curated.data_quality_metrics
            WHERE (pipeline_id, timestamp_ejecucion) IN (
                SELECT pipeline_id, MAX(timestamp_ejecucion)
                FROM curated.data_quality_metrics
                GROUP BY pipeline_id
            )
            ORDER BY estado DESC, pipeline_id
            """
        )
        filas = cur.fetchall()

    if not filas:
        print("[estado] sin datos de calidad — ¿se ha ejecutado run_all?")
        return 0

    fallidos = [f for f in filas if f["estado"] == "fallido"]
    parciales = [f for f in filas if f["estado"] == "parcial"]
    exitos = [f for f in filas if f["estado"] == "exitoso"]

    print(f"[estado] {len(filas)} pipelines: {len(exitos)} ok, "
          f"{len(parciales)} parciales, {len(fallidos)} fallidos")

    for f in fallidos:
        print(f"  [FALLO] {f['pipeline_id']}: {f['mensaje_error'] or 'sin mensaje'}")
    for f in parciales:
        print(f"  [PARCIAL] {f['pipeline_id']}: rechazadas {f['registros_rechazados']} filas")

    return 1 if fallidos else 0


if __name__ == "__main__":
    sys.exit(estado())
