"""Validación de frescura: ¿los datos publicados siguen vigentes?

Un observatorio que muestra cifras de hace tres años sin decirlo no es un
observatorio, es un archivo. Este módulo compara, por fuente, cuándo se extrajo
por última vez contra la periodicidad que la propia fuente declara, y clasifica
el resultado (migración 0015).

Se apoya en `curated.vw_frescura_fuentes`, que hace la aritmética en SQL.

Uso:
    python -m etl.common.frescura        # exit 0 si todo al día, 1 si hay obsoletas
"""

from __future__ import annotations

import sys

from psycopg.rows import dict_row

from etl.common.db import conectar
from etl.common.logs import obtener_logger_etl

log = obtener_logger_etl("frescura")

# Orden de severidad, de mejor a peor.
ESTADOS = ("al_dia", "retrasada", "obsoleta", "sin_datos")

_SIMBOLO = {
    "al_dia": "OK   ",
    "retrasada": "AVISO",
    "obsoleta": "STALE",
    "sin_datos": "VACIA",
}


def evaluar_frescura(conn) -> list[dict]:
    """Estado de frescura de todas las fuentes activas, de la peor a la mejor."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT fuente_id, codigo, nombre, entidad, periodicidad,
                   periodicidad_dias, ultima_actualizacion, fecha_corte_dato,
                   dias_desde_extraccion, frescura
            FROM curated.vw_frescura_fuentes
            ORDER BY CASE frescura
                        WHEN 'sin_datos' THEN 0
                        WHEN 'obsoleta'  THEN 1
                        WHEN 'retrasada' THEN 2
                        ELSE 3
                     END,
                     dias_desde_extraccion DESC NULLS FIRST,
                     nombre
            """
        )
        return cur.fetchall()


def resumen(filas: list[dict]) -> dict[str, int]:
    """Conteo por estado, con todos los estados presentes aunque valgan 0."""
    conteo = dict.fromkeys(ESTADOS, 0)
    for fila in filas:
        estado = fila["frescura"] or "sin_datos"
        conteo[estado] = conteo.get(estado, 0) + 1
    return conteo


def informar(filas: list[dict]) -> None:
    """Imprime el estado por fuente, empezando por lo que necesita atención."""
    for fila in filas:
        estado = fila["frescura"] or "sin_datos"
        dias = fila["dias_desde_extraccion"]
        detalle = (
            f"hace {dias} d (esperado ≤ {fila['periodicidad_dias']} d)"
            if dias is not None
            else "nunca extraída"
        )
        corte = fila["fecha_corte_dato"]
        corte_txt = f" · datos hasta {corte}" if corte else ""
        print(f"[{_SIMBOLO.get(estado, estado)}] {fila['nombre']}: {detalle}{corte_txt}")


def main() -> int:
    with conectar() as conn:
        filas = evaluar_frescura(conn)

    if not filas:
        log.warning("no hay fuentes activas registradas")
        return 1

    informar(filas)
    conteo = resumen(filas)
    print(
        f"\nFrescura: {conteo['al_dia']} al día · {conteo['retrasada']} retrasadas · "
        f"{conteo['obsoleta']} obsoletas · {conteo['sin_datos']} sin datos"
    )

    # Solo lo obsoleto o sin datos rompe: una fuente "retrasada" avisa pero no
    # debe tumbar un cron todas las noches.
    problematicas = conteo["obsoleta"] + conteo["sin_datos"]
    if problematicas:
        log.warning("%d fuente(s) obsoletas o sin datos", problematicas)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
