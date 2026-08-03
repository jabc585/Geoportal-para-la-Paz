"""Servicios de acceso a datos desde curated (solo lectura, sección 7.3)."""

from __future__ import annotations

import base64
import json

from psycopg.rows import dict_row

from api.db import obtener_conexion

# Umbral de supresión k (auditoría integral §4): municipios con menos de k
# casos no se exponen individualmente en modo tasa para evitar revelar
# información indirecta en territorios de baja población.
UMBRAL_K = 5


def _cursor_payload(serie_id: int) -> str:
    return base64.urlsafe_b64encode(json.dumps({"serie_id": serie_id}).encode()).decode()


def _poblacion_municipio_anio() -> dict[tuple[str, int], float]:
    """Cache de población por (codigo_divipola, año). Usada para tasas."""
    with obtener_conexion() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT m.codigo_divipola,
                   EXTRACT(YEAR FROM s.periodo_inicio)::int AS anio,
                   s.valor
            FROM curated.serie_historica s
            JOIN curated.indicadores i ON i.indicador_id = s.indicador_id
            JOIN curated.municipio m ON m.municipio_id = s.municipio_id
            WHERE i.codigo = 'poblacion' AND s.valor > 0
            """
        )
        poblacion: dict[tuple[str, int], float] = {}
        for f in cur.fetchall():
            poblacion[(f["codigo_divipola"], f["anio"])] = float(f["valor"])
        return poblacion


def _aplicar_tasa(filas: list[dict], poblacion: dict[tuple[str, int], float]) -> list[dict]:
    """Convierte valores absolutos a tasas por 100.000 habitantes. Suprime
    filas con denominador muy bajo (umbral k, auditoría integral §4)."""
    resultado = []
    for f in filas:
        cod = f.get("codigo_divipola")
        anio = f.get("periodo_inicio")
        if cod and anio:
            try:
                anio_int = int(str(anio)[:4])
                pob = poblacion.get((str(cod).zfill(5), anio_int))
            except (ValueError, TypeError):
                pob = None
            if pob and pob >= UMBRAL_K:
                f = dict(f)
                f["valor"] = (float(f["valor"]) / pob) * 100_000
                f["unidad"] = f.get("unidad", "") + " (tasa × 100.000 hab.)"
            elif pob is not None and pob < UMBRAL_K:
                continue  # suprimir: municipio con menos de k habitantes
        resultado.append(f)
    return resultado or filas  # si se suprimieron todas, devolver original


def indicador_existe(indicador: str) -> bool:
    """True si el indicador está en el catálogo curated.indicadores."""
    with obtener_conexion() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT 1 FROM curated.indicadores WHERE codigo = %s", (indicador,))
        return cur.fetchone() is not None


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
        # Cursor malformado (base64/JSON inválido) → HTTP 400, no 500 genérico
        # (auditoría 2026-08-02).
        try:
            payload = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
        except (ValueError, json.JSONDecodeError) as exc:
            raise ValueError("Cursor de paginación inválido") from exc
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
    with obtener_conexion() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        filas = cur.fetchall()

    hay_mas = len(filas) > limit
    filas = filas[:limit]
    next_cursor = _cursor_payload(filas[-1]["serie_id"]) if hay_mas else None
    return filas, next_cursor


def exportar_serie_csv(
    indicador: str,
    territorio: str | None = None,
    desde: str | None = None,
    hasta: str | None = None,
) -> list[dict]:
    """Serie completa de un indicador para exportación CSV (sección 8 y 10).

    Mismos filtros que `consultar_serie` pero sin paginación: se devuelven
    todas las filas del indicador (tope 200.000) ordenadas por periodo.
    """
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

    sql = f"""
        SELECT i.codigo AS indicador, i.nombre AS indicador_nombre, i.unidad,
               m.codigo_divipola, m.nombre AS municipio,
               d.codigo_divipola AS departamento_divipola, d.nombre AS departamento,
               s.periodo_inicio, s.periodo_fin, s.valor, f.nombre AS fuente
        FROM curated.serie_historica s
        JOIN curated.indicadores i ON i.indicador_id = s.indicador_id
        JOIN curated.fuentes f     ON f.fuente_id = s.fuente_id
        LEFT JOIN curated.municipio m    ON m.municipio_id = s.municipio_id
        LEFT JOIN curated.departamento d ON d.departamento_id = s.departamento_id
        WHERE {' AND '.join(where)}
        ORDER BY s.periodo_inicio, m.nombre
        LIMIT 200000
    """
    with obtener_conexion() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def listar_fuentes() -> list[dict]:
    with obtener_conexion() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT f.fuente_id, f.nombre, f.entidad, f.licencia,
                   f.ultima_actualizacion, f.url_base,
                   f.fecha_corte_dato, f.periodicidad,
                   v.dias_desde_extraccion, v.frescura
            FROM curated.fuentes f
            LEFT JOIN curated.vw_frescura_fuentes v USING (fuente_id)
            WHERE f.activa
            ORDER BY f.nombre
            """
        )
        return cur.fetchall()


def listar_frescura() -> list[dict]:
    """Estado de vigencia por fuente (migración 0015).

    Compara la última extracción contra la periodicidad que declara la propia
    fuente: al_dia / retrasada / obsoleta / sin_datos. Ordena por lo que
    necesita atención primero.
    """
    with obtener_conexion() as conn, conn.cursor(row_factory=dict_row) as cur:
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


def contar_proyectos_pdet() -> dict:
    """Conteos del módulo PDET (sección 11 del plan): proyectos, municipios PDET
    y valor de inversión agregado (si lo reportara la fuente)."""
    with obtener_conexion() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM curated.pdet_proyectos) AS proyectos,
                (SELECT COUNT(DISTINCT municipio_id) FROM curated.pdet_proyectos) AS municipios
            """
        )
        fila = cur.fetchone()
        return {"proyectos": fila["proyectos"], "municipios": fila["municipios"]}


def consultar_territorio(codigo_divipola: str) -> dict | None:
    with obtener_conexion() as conn, conn.cursor(row_factory=dict_row) as cur:
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


def consultar_total(indicador: str) -> dict | None:
    """Total nacional por año de un indicador (para KPIs del dashboard).

    Suma todas las fuentes que cargan el indicador (cada una conserva su
    linaje); el dashboard muestra el año más reciente.
    """
    with obtener_conexion() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT i.codigo, i.nombre, i.unidad
            FROM curated.indicadores i
            WHERE i.codigo = %s
            """,
            (indicador,),
        )
        meta = cur.fetchone()
        if not meta:
            return None
        cur.execute(
            """
            SELECT EXTRACT(YEAR FROM s.periodo_inicio)::int AS anio,
                   round(sum(s.valor))::float AS valor
            FROM curated.serie_historica s
            JOIN curated.indicadores i ON i.indicador_id = s.indicador_id
            WHERE i.codigo = %s
            GROUP BY 1
            ORDER BY 1 DESC
            """,
            (indicador,),
        )
        totales = cur.fetchall()
    return {
        "indicador": meta["codigo"],
        "nombre": meta["nombre"],
        "unidad": meta["unidad"],
        "totales": totales,
    }


def consultar_mapa(indicador: str, anio: int | None = None) -> dict | None:
    """Capa coroplética municipal (fase 5): GeoJSON simplificado.

    Une el agregado municipal-año del indicador con la capa geo DIVIPOLA
    (sección 5.1). Si `anio` es None usa el año más reciente con datos.
    Geometría simplificada (~110 m) para payloads razonables; los municipios
    sin dato salen con valor null para pintarse en gris.
    """
    with obtener_conexion() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT i.codigo, i.nombre, i.unidad,
                   EXTRACT(YEAR FROM MAX(s.periodo_inicio))::int AS anio_max
            FROM curated.indicadores i
            LEFT JOIN curated.serie_historica s ON s.indicador_id = i.indicador_id
                AND s.municipio_id IS NOT NULL
            WHERE i.codigo = %s
            GROUP BY i.codigo, i.nombre, i.unidad
            """,
            (indicador,),
        )
        meta = cur.fetchone()
        if not meta:
            return None
        if meta["anio_max"] is None:
            return {
                "indicador": meta["codigo"],
                "nombre": meta["nombre"],
                "unidad": meta["unidad"],
                "anio": anio,
                "features": [],
            }
        anio_efectivo = anio if anio is not None else meta["anio_max"]
        cur.execute(
            """
            SELECT c.codigo_divipola, m.nombre AS municipio, d.nombre AS departamento,
                   ST_AsGeoJSON(ST_SimplifyPreserveTopology(c.geometria, 0.002), 6) AS geojson,
                   a.valor
            FROM curated.capa_contexto_territorial c
            JOIN curated.municipio m    ON m.codigo_divipola = c.codigo_divipola AND m.vigente
            JOIN curated.departamento d ON d.departamento_id = m.departamento_id
            LEFT JOIN (
                SELECT s.municipio_id, sum(s.valor) AS valor
                FROM curated.serie_historica s
                JOIN curated.indicadores i ON i.indicador_id = s.indicador_id
                WHERE i.codigo = %s
                  AND EXTRACT(YEAR FROM s.periodo_inicio) = %s
                  AND s.municipio_id IS NOT NULL
                GROUP BY s.municipio_id
            ) a ON a.municipio_id = m.municipio_id
            WHERE c.tipo = 'divipola'
            """,
            (indicador, anio_efectivo),
        )
        features = []
        for fila in cur.fetchall():
            geometria = json.loads(fila["geojson"])
            features.append(
                {
                    "type": "Feature",
                    "geometry": geometria,
                    "properties": {
                        "codigo_divipola": fila["codigo_divipola"],
                        "municipio": fila["municipio"],
                        "departamento": fila["departamento"],
                        "valor": float(fila["valor"]) if fila["valor"] is not None else None,
                    },
                }
            )
    return {
        "indicador": meta["codigo"],
        "nombre": meta["nombre"],
        "unidad": meta["unidad"],
        "anio": anio_efectivo,
        "type": "FeatureCollection",
        "features": features,
    }


def ficha_territorio(codigo_divipola: str) -> dict | None:
    """Todos los indicadores del año más reciente para un municipio
    (auditoría integral §3, Bloque 3: ficha de territorio)."""
    with obtener_conexion() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT municipio_id, nombre, codigo_divipola FROM curated.municipio "
            "WHERE codigo_divipola = %s AND vigente",
            (codigo_divipola,),
        )
        mun = cur.fetchone()
        if not mun:
            return None

        cur.execute(
            # d.nombre calificado: municipio también tiene `nombre` y el JOIN
            # hacía la referencia ambigua → 500 en toda ficha de territorio.
            "SELECT d.nombre FROM curated.departamento d "
            "JOIN curated.municipio m ON m.departamento_id = d.departamento_id "
            "WHERE m.codigo_divipola = %s",
            (codigo_divipola,),
        )
        depto = cur.fetchone()

        cur.execute(
            """
            SELECT i.codigo, i.nombre, i.unidad,
                   EXTRACT(YEAR FROM MAX(s.periodo_inicio))::int AS anio_max,
                   SUM(s.valor) FILTER (
                       WHERE EXTRACT(YEAR FROM s.periodo_inicio) =
                           (SELECT EXTRACT(YEAR FROM MAX(s2.periodo_inicio))::int
                            FROM curated.serie_historica s2
                            WHERE s2.municipio_id = %s AND s2.indicador_id = i.indicador_id)
                   ) AS valor
            FROM curated.indicadores i
            JOIN curated.serie_historica s ON s.indicador_id = i.indicador_id
            WHERE s.municipio_id = %s
            GROUP BY i.codigo, i.nombre, i.unidad
            HAVING SUM(s.valor) > 0
            ORDER BY i.nombre
            """,
            (mun["municipio_id"], mun["municipio_id"]),
        )
        indicadores = cur.fetchall()

    return {
        "municipio": mun["nombre"],
        "codigo_divipola": mun["codigo_divipola"],
        "departamento": depto["nombre"] if depto else None,
        "indicadores": [
            {
                "codigo": i["codigo"],
                "nombre": i["nombre"],
                "unidad": i["unidad"],
                "anio": i["anio_max"],
                "valor": float(i["valor"]) if i["valor"] is not None else None,
            }
            for i in indicadores
        ],
    }
