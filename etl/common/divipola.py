"""Seed del catálogo territorial DIVIPOLA (secciones 5.1 y 7.2).

Descarga los datasets oficiales de DANE en datos.gov.co y puebla
curated.departamento / curated.municipio con SCD tipo 2 (valido_desde = hoy,
valido_hasta = NULL).

Ejecución:  python -m etl.common.divipola
Requisito:  BD viva (DATABASE_URL). Los dataset IDs se pueden sobreescribir
            con DIVIPOLA_DEPT_DATASET y DIVIPOLA_MUN_DATASET.
"""

from __future__ import annotations

import os

import psycopg

from etl.common.db import conectar, transaccion
from etl.common.descargas import descargar_socrata_paginado

DEFAULT_DEPT_DATASET = "vcjz-niiq"
DEFAULT_MUN_DATASET = "gdxc-w37w"
URL_SOCRATA = "https://www.datos.gov.co/resource"

# Áreas No Municipalizadas (ANM) que el dataset Socrata de municipios
# (gdxc-w37w) no publica pero DANE sí incluye en las proyecciones de
# población 2020-2035 (auditoría 2026-08-02: Mapiripana, 94663, faltaba y
# descartaba 16 filas/año del pipeline). Formato: (codigo, nombre, codigo_depto).
ANMS_FALTANTES = [
    ("94663", "MAPIRIPANA", "94"),
]


def _descargar(dataset_id: str) -> list[dict]:
    url = f"{URL_SOCRATA}/{dataset_id}.json"
    return descargar_socrata_paginado(url, tamano_pagina=50000, timeout=120)


def sembrar_departamentos(conn: psycopg.Connection) -> int:
    filas = _descargar(os.getenv("DIVIPOLA_DEPT_DATASET", DEFAULT_DEPT_DATASET))
    insertadas = 0
    with conn.cursor() as cur:
        for f in filas:
            cur.execute(
                """
                INSERT INTO curated.departamento (codigo_divipola, nombre, valido_desde)
                VALUES (%s, %s, CURRENT_DATE)
                ON CONFLICT (codigo_divipola) DO NOTHING
                """,
                (f["codigo_departamento"], f["nombre_departamento"]),
            )
            insertadas += cur.rowcount > 0
    return insertadas


def sembrar_municipios(conn: psycopg.Connection) -> int:
    filas = _descargar(os.getenv("DIVIPOLA_MUN_DATASET", DEFAULT_MUN_DATASET))
    insertadas = 0
    con_departamento_ausente = 0
    with conn.cursor() as cur:
        for f in filas:
            cur.execute(
                """
                INSERT INTO curated.municipio (codigo_divipola, nombre, departamento_id, valido_desde)
                SELECT %s, %s, d.departamento_id, CURRENT_DATE
                FROM curated.departamento d
                WHERE d.codigo_divipola = %s AND d.vigente
                ON CONFLICT (codigo_divipola, valido_desde) DO NOTHING
                """,
                (f["cod_mpio"], f["nom_mpio"], f["cod_dpto"]),
            )
            insertadas += cur.rowcount > 0
            con_departamento_ausente += cur.rowcount == 0
        for codigo, nombre, codigo_depto in ANMS_FALTANTES:
            cur.execute(
                """
                INSERT INTO curated.municipio (codigo_divipola, nombre, departamento_id, valido_desde)
                SELECT %s, %s, d.departamento_id, CURRENT_DATE
                FROM curated.departamento d
                WHERE d.codigo_divipola = %s AND d.vigente
                ON CONFLICT (codigo_divipola, valido_desde) DO NOTHING
                """,
                (codigo, nombre, codigo_depto),
            )
            insertadas += cur.rowcount > 0
    if con_departamento_ausente:
        print(f"[divipola] {con_departamento_ausente} municipios sin departamento vigente (descartados)")
    return insertadas


if __name__ == "__main__":
    with transaccion(conectar()) as conn:
        n_dept = sembrar_departamentos(conn)
        n_mun = sembrar_municipios(conn)
    print(f"[divipola] departamentos sembrados: {n_dept}, municipios sembrados: {n_mun}")
