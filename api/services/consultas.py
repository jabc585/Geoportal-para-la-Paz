"""Servicios de acceso a datos desde curated (solo lectura, sección 7.3)."""

from __future__ import annotations

import base64
import json

from psycopg.rows import dict_row

from etl.common.db import conectar


def _cursor_payload(serie_id: int) -> str:
    return base64.urlsafe_b64encode(json.dumps({"serie_id": serie_id}).encode()).decode()


def consultar_serie(
    indicador: str,
    territorio: str | None = None,
    desde: str | None = None,
    hasta: str | None = None,
    limit: int = 100,
    cursor: str | None = None,
) -> tuple[list[dict], str | None]:
    """Serie histórica con paginación basada en cursor (sección 8).

    El cursor codifica el último serie_id visto; las consultas filtradas por
    indicador/territorio/periodo usan ese valor como condición adicional.
    """
    limit = max(1, min(limit, 1000))
    where = ["i.codigo = %s"]
    params: list = [indicador]
    if territorio:
        where.append("(m.codigo_divipola = %s OR d.codigo_divipola = %s)")
        params.extend([territorio, territorio])
    if desde:
        where.append("s.periodo_inicio >= %s")
        params.append(desde)
    if hasta:
        where.append("s.periodo_fin <= %s")
        params.append(hasta)
    if cursor:
        payload = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
        where.append("s.serie_id > %s")
        params.append(payload["serie_id"])

    sql = f"""
        SELECT s.serie_id, i.codigo AS indicador, m.nombre AS municipio,
               d.nombre AS departamento, s.periodo_inicio, s.periodo_fin,
               s.valor, f.nombre AS fuente, s.fecha_extraccion
        FROM curated.serie_historica s
        JOIN curated.indicadores i ON i.indicador_id = s.indicador_id
        JOIN curated.fuentes f     ON f.fuente_id = s.fuente_id
        LEFT JOIN curated.municipio m    ON m.municipio_id = s.municipio_id
        LEFT JOIN curated.departamento d ON d.departamento_id = s.departamento_id
        WHERE {' AND '.join(where)}
        ORDER BY s.serie_id
        LIMIT %s
    """
    params.append(limit + 1)
    with conectar() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        filas = cur.fetchall()

    hay_mas = len(filas) > limit
    filas = filas[:limit]
    next_cursor = _cursor_payload(filas[-1]["serie_id"]) if hay_mas else None
    return filas, next_cursor


def listar_fuentes() -> list[dict]:
    with conectar() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT fuente_id, nombre, entidad, licencia, ultima_actualizacion, url_base
            FROM curated.fuentes
            WHERE activa
            ORDER BY nombre
            """
        )
        return cur.fetchall()


def consultar_territorio(codigo_divipola: str) -> dict | None:
    with conectar() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT m.municipio_id, m.codigo_divipola, m.nombre,
                   d.nombre AS departamento, d.codigo_divipola AS departamento_divipola
            FROM curated.municipio m
            JOIN curated.departamento d ON d.departamento_id = m.departamento_id
            WHERE m.codigo_divipola = %s AND m.vigente
            """,
            (codigo_divipola,),
        )
        return cur.fetchone()
