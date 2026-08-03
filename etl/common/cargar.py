"""Carga a curated con resolución de catálogos y linaje (secciones 7 y 12).

Helpers compartidos para que los pipelines piloto escriban en
curated.serie_historica con: indicador, territorio (municipio/departamento),
periodo flexible (sección 7.1) y linaje completo (sección 3, punto 4).
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date

import pandas as pd
import psycopg

from etl.common.lineage import hash_registro
from etl.common.logs import obtener_logger_etl


def slugificar(texto: str) -> str:
    """Normaliza un texto a código seguro: minúsculas, sin acentos, guiones bajos."""
    texto = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^a-z0-9]+", "_", texto.lower())
    return texto.strip("_")


def upsert_fuente(conn: psycopg.Connection, **datos) -> int:
    """Inserta o recupera el fuente_id del catálogo curated.fuentes.

    codigo (slug estable) se deriva del nombre si el pipeline no lo provee.
    """
    datos.setdefault("nombre", "")
    datos.setdefault("codigo", slugificar(datos["nombre"]))
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO curated.fuentes (codigo, nombre, entidad, tipo, descripcion, url_base,
                                         metodo_acceso, periodicidad, formato, licencia, ficha_doc)
            VALUES (%(codigo)s, %(nombre)s, %(entidad)s, %(tipo)s, %(descripcion)s, %(url_base)s,
                    %(metodo_acceso)s, %(periodicidad)s, %(formato)s, %(licencia)s, %(ficha_doc)s)
            ON CONFLICT (nombre) DO UPDATE SET url_base = EXCLUDED.url_base
            RETURNING fuente_id
            """,
            datos,
        )
        return cur.fetchone()[0]


def upsert_indicador(conn: psycopg.Connection, codigo: str, **datos) -> int:
    """Inserta o recupera el indicador_id del catálogo curated.indicadores.

    fuente_primaria_id y limites_conocidos son opcionales para los conectores;
    se registran como NULL si el pipeline no los provee.
    """
    datos["codigo"] = codigo
    datos.setdefault("fuente_primaria_id", None)
    datos.setdefault("limites_conocidos", None)
    datos.setdefault("metodologia_doc", None)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO curated.indicadores (codigo, nombre, descripcion, unidad,
                                             granularidad_min, fuente_primaria_id,
                                             periodicidad, metodologia_doc, limites_conocidos)
            VALUES (%(codigo)s, %(nombre)s, %(descripcion)s, %(unidad)s,
                    %(granularidad_min)s, %(fuente_primaria_id)s,
                    %(periodicidad)s, %(metodologia_doc)s, %(limites_conocidos)s)
            ON CONFLICT (codigo) DO NOTHING
            RETURNING indicador_id
            """,
            datos,
        )
        fila = cur.fetchone()
        if fila:
            return fila[0]
        cur.execute("SELECT indicador_id FROM curated.indicadores WHERE codigo = %s", (codigo,))
        return cur.fetchone()[0]


def resolver_territorio(conn: psycopg.Connection, codigo_divipola: str) -> tuple[str | None, str | None]:
    """Resuelve código DIVIPOLA a (municipio_id, departamento_id) vigentes (sección 7.2)."""
    codigo = str(codigo_divipola).zfill(5 if len(str(codigo_divipola)) > 2 else 2)
    with conn.cursor() as cur:
        if len(codigo) == 5:
            cur.execute(
                "SELECT municipio_id, departamento_id FROM curated.municipio "
                "WHERE codigo_divipola = %s AND vigente",
                (codigo,),
            )
        else:
            cur.execute(
                "SELECT NULL, departamento_id FROM curated.departamento "
                "WHERE codigo_divipola = %s AND vigente",
                (codigo,),
            )
        return cur.fetchone() or (None, None)


def marcar_fuente_actualizada(
    conn: psycopg.Connection,
    fuente_id: int,
    fecha_extraccion,
    fecha_corte_dato=None,
) -> None:
    """Sella en curated.fuentes cuándo se extrajo y hasta qué periodo llegan los datos.

    `curated.fuentes.ultima_actualizacion` existía en el esquema desde el
    principio pero ningún pipeline la escribía: la API la exponía siempre como
    NULL y el dashboard mostraba un guion. Sin este sello no hay forma de
    validar frescura (migración 0015).

    Las fechas solo avanzan: una recarga de datos históricos no debe hacer
    retroceder el sello de una carga más reciente.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE curated.fuentes
               SET ultima_actualizacion = GREATEST(
                       COALESCE(ultima_actualizacion, %(extraccion)s), %(extraccion)s),
                   fecha_corte_dato = GREATEST(
                       COALESCE(fecha_corte_dato, %(corte)s), %(corte)s)
             WHERE fuente_id = %(fuente_id)s
            """,
            {
                "fuente_id": fuente_id,
                "extraccion": fecha_extraccion,
                "corte": fecha_corte_dato,
            },
        )


def periodo_maximo(df: pd.DataFrame, columna: str = "periodo_fin"):
    """Fecha de corte real de un lote: el periodo más reciente que trae la fuente.

    Se deriva de los datos en vez de declararse a mano — ACLED tenía la suya
    escrita como literal en el código, que envejece sin que nadie lo note.
    """
    if df.empty or columna not in df.columns:
        return None
    serie = pd.to_datetime(df[columna], errors="coerce").dropna()
    return None if serie.empty else serie.max().date()


def insertar_serie(conn: psycopg.Connection, df: pd.DataFrame, fuente_id: int, url_origen: str, fecha_extraccion) -> int:
    """Inserta filas normalizadas en curated.serie_historica con deduplicación por hash.

    El DataFrame debe contener: codigo_divipola, periodo_inicio (date),
    periodo_fin (date), valor, indicador_id. Las filas cuyo territorio no se
    resuelve contra el catálogo DIVIPOLA se descartan y se cuentan, para que
    ningún descarte pase en silencio (hallazgo de auditoría).

    Batch (auditoría 2026-08-02): el territorio se resuelve UNA vez por código
    DIVIPOLA único (no una vez por fila) y el INSERT se hace con executemany en
    una sola llamada — antes eran 2 round-trips por fila (N+1 en el hot path).
    """
    if df.empty:
        return 0
    codigos_unicos = pd.unique(df["codigo_divipola"].astype(str))
    mapa_territorio = {c: resolver_territorio(conn, c) for c in codigos_unicos}
    registros = []
    sin_territorio = 0
    for fila in df.to_dict("records"):
        municipio_id, departamento_id = mapa_territorio[str(fila["codigo_divipola"])]
        if municipio_id is None and departamento_id is None:
            sin_territorio += 1
            continue
        registros.append(
            (
                fila["indicador_id"],
                municipio_id,
                departamento_id,
                fila["periodo_inicio"],
                fila["periodo_fin"],
                fila["valor"],
                fuente_id,
                url_origen,
                fecha_extraccion,
                fila.get("fecha_corte_dato"),
                hash_registro(
                    {
                        "indicador_id": fila["indicador_id"],
                        "codigo_divipola": str(fila["codigo_divipola"]),
                        "periodo_inicio": str(fila["periodo_inicio"]),
                        "periodo_fin": str(fila["periodo_fin"]),
                        "valor": str(fila["valor"]),
                    }
                ),
            )
        )
    if not registros:
        if sin_territorio:
            log = obtener_logger_etl("cargar")
            log.warning(
                "%d filas descartadas por territorio no resuelto "
                "(¿catálogo DIVIPOLA sembrado? python -m etl.common.divipola)",
                sin_territorio,
            )
        return 0
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO curated.serie_historica
                (indicador_id, municipio_id, departamento_id, periodo_inicio, periodo_fin,
                 valor, fuente_id, url_origen, fecha_extraccion, fecha_corte_dato, hash_registro)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (indicador_id, municipio_id, departamento_id, periodo_inicio, periodo_fin, fuente_id)
            -- Las fuentes oficiales revisan sus cifras (el DANE ajusta
            -- proyecciones, la Policía corrige consolidados). Con DO NOTHING el
            -- primer valor observado quedaba congelado para siempre y la
            -- corrección se perdía en silencio. Se actualiza solo cuando el
            -- valor cambia de verdad; el histórico completo de cada extracción
            -- sigue intacto en raw.*, que es inmutable.
            DO UPDATE SET
                valor            = EXCLUDED.valor,
                url_origen       = EXCLUDED.url_origen,
                fecha_extraccion = EXCLUDED.fecha_extraccion,
                fecha_corte_dato = EXCLUDED.fecha_corte_dato,
                hash_registro    = EXCLUDED.hash_registro
            WHERE curated.serie_historica.valor IS DISTINCT FROM EXCLUDED.valor
            """,
            registros,
        )
        insertadas = cur.rowcount
    # Sella la fuente con esta extracción y con el periodo más reciente cargado.
    marcar_fuente_actualizada(conn, fuente_id, fecha_extraccion, periodo_maximo(df))
    if sin_territorio:
        log = obtener_logger_etl("cargar")
        log.warning(
            "%d filas descartadas por territorio no resuelto "
            "(¿catálogo DIVIPOLA sembrado? python -m etl.common.divipola)",
            sin_territorio,
        )
    return insertadas


def insertar_indicador_internacional(
    conn: psycopg.Connection,
    df: pd.DataFrame,
    fuente_id: int,
    pais: str,
    url_origen: str,
    fecha_extraccion: str,
    fecha_corte_dato: str | None = None,
    unidad: str | None = None,
    *,
    col_indicador: str = "indicador",
) -> int:
    """Inserta indicadores internacionales (país-año) en lote con executemany.

    Reemplaza el loop fila-a-fila (N+1) que estaba triplicado en world_bank,
    unhcr y acled (plan3.md, Fase 1.7). El DataFrame debe tener columnas
    ``anio``, ``valor`` y ``col_indicador`` (default "indicador"). ``unidad``
    puede ser un literal o el nombre de una columna del DataFrame.
    """
    if df.empty:
        return 0
    es_col_unidad = unidad is not None and unidad in df.columns
    registros = []
    for fila in df.to_dict("records"):
        registros.append(
            (
                fuente_id,
                pais,
                str(fila[col_indicador]),
                f"{int(fila['anio'])}-01-01",
                float(fila["valor"]),
                str(fila[unidad]) if es_col_unidad else unidad,
                url_origen,
                fecha_extraccion,
                fecha_corte_dato,
                hash_registro(fila),
            )
        )
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO curated.indicador_internacional
                (fuente_id, pais, indicador, periodo, valor, unidad,
                 url_origen, fecha_extraccion, fecha_corte_dato, hash_registro)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (fuente_id, pais, indicador, periodo)
            -- Mismo criterio que serie_historica: el Banco Mundial y ACNUR
            -- revisan sus series retroactivamente; congelar el primer valor
            -- dejaría la cifra desactualizada sin aviso.
            DO UPDATE SET
                valor            = EXCLUDED.valor,
                unidad           = EXCLUDED.unidad,
                url_origen       = EXCLUDED.url_origen,
                fecha_extraccion = EXCLUDED.fecha_extraccion,
                fecha_corte_dato = EXCLUDED.fecha_corte_dato,
                hash_registro    = EXCLUDED.hash_registro
            WHERE curated.indicador_internacional.valor IS DISTINCT FROM EXCLUDED.valor
            """,
            registros,
        )
        insertadas = cur.rowcount
    # El periodo más reciente de estas series es el año máximo cargado.
    corte = fecha_corte_dato
    if corte is None and "anio" in df.columns:
        anios = pd.to_numeric(df["anio"], errors="coerce").dropna()
        if not anios.empty:
            corte = date(int(anios.max()), 12, 31)
    marcar_fuente_actualizada(conn, fuente_id, fecha_extraccion, corte)
    return insertadas


def periodo_anual(anio: int | str) -> tuple[date, date]:
    """Periodo flexible (sección 7.1): un año completo."""
    anio = int(anio)
    return date(anio, 1, 1), date(anio, 12, 31)
