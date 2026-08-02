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


def slugificar(texto: str) -> str:
    """Normaliza un texto a código seguro: minúsculas, sin acentos, guiones bajos."""
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^a-z0-9]+", "_", texto.lower())
    return texto.strip("_")


def upsert_fuente(conn: psycopg.Connection, **datos) -> int:
    """Inserta o recupera el fuente_id del catálogo curated.fuentes."""
    datos.setdefault("nombre", "")
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO curated.fuentes (nombre, entidad, tipo, descripcion, url_base,
                                         metodo_acceso, periodicidad, formato, licencia, ficha_doc)
            VALUES (%(nombre)s, %(entidad)s, %(tipo)s, %(descripcion)s, %(url_base)s,
                    %(metodo_acceso)s, %(periodicidad)s, %(formato)s, %(licencia)s, %(ficha_doc)s)
            ON CONFLICT (nombre) DO UPDATE SET url_base = EXCLUDED.url_base
            RETURNING fuente_id
            """,
            datos,
        )
        return cur.fetchone()[0]


def upsert_indicador(conn: psycopg.Connection, codigo: str, **datos) -> int:
    """Inserta o recupera el indicador_id del catálogo curated.indicadores."""
    datos["codigo"] = codigo
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


def insertar_serie(conn: psycopg.Connection, df: pd.DataFrame, fuente_id: int, url_origen: str, fecha_extraccion) -> int:
    """Inserta filas normalizadas en curated.serie_historica con deduplicación por hash.

    El DataFrame debe contener: codigo_divipola, periodo_inicio (date),
    periodo_fin (date), valor, indicador_id.
    """
    insertadas = 0
    with conn.cursor() as cur:
        for fila in df.to_dict("records"):
            municipio_id, departamento_id = resolver_territorio(conn, fila["codigo_divipola"])
            if municipio_id is None and departamento_id is None:
                continue
            registro = {
                "indicador_id": fila["indicador_id"],
                "municipio_id": municipio_id,
                "departamento_id": departamento_id,
                "periodo_inicio": fila["periodo_inicio"],
                "periodo_fin": fila["periodo_fin"],
                "valor": fila["valor"],
                "fuente_id": fuente_id,
                "url_origen": url_origen,
                "fecha_extraccion": fecha_extraccion,
                "fecha_corte_dato": fila.get("fecha_corte_dato"),
                "hash_registro": hash_registro(
                    {
                        "indicador_id": fila["indicador_id"],
                        "codigo_divipola": fila["codigo_divipola"],
                        "periodo_inicio": str(fila["periodo_inicio"]),
                        "periodo_fin": str(fila["periodo_fin"]),
                        "valor": str(fila["valor"]),
                    }
                ),
            }
            cur.execute(
                """
                INSERT INTO curated.serie_historica
                    (indicador_id, municipio_id, departamento_id, periodo_inicio, periodo_fin,
                     valor, fuente_id, url_origen, fecha_extraccion, fecha_corte_dato, hash_registro)
                VALUES (%(indicador_id)s, %(municipio_id)s, %(departamento_id)s, %(periodo_inicio)s,
                        %(periodo_fin)s, %(valor)s, %(fuente_id)s, %(url_origen)s,
                        %(fecha_extraccion)s, %(fecha_corte_dato)s, %(hash_registro)s)
                ON CONFLICT (indicador_id, municipio_id, departamento_id, periodo_inicio, periodo_fin, fuente_id)
                DO NOTHING
                """,
                registro,
            )
            insertadas += cur.rowcount > 0
    return insertadas


def periodo_anual(anio: int | str) -> tuple[date, date]:
    """Periodo flexible (sección 7.1): un año completo."""
    anio = int(anio)
    return date(anio, 1, 1), date(anio, 12, 31)
