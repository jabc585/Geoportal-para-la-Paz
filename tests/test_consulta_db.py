"""Tests de integración: cada consulta SQL de la API contra PostgreSQL real.

Por qué existe este archivo
---------------------------
`tests/test_api.py` simula la capa de servicios ("sin BD"), así que ningún test
llega a ejecutar el SQL. Con esa cobertura, un error de SQL solo aparece en
producción — y apareció: `ficha_territorio()` devolvía **500 en todos los
municipios** por un `SELECT nombre` ambiguo entre `departamento` y `municipio`,
y el CI no lo vio porque el paso de integración terminaba en
`|| echo "integration tests skipped"` sobre un archivo que nunca se creó.

Este módulo ejecuta de verdad cada consulta pública de `api/services/consultas.py`.
No comprueba cifras concretas —la BD de CI está vacía tras las migraciones—
sino que **el SQL corre y devuelve la forma esperada**, que es la clase de fallo
que se escapaba. Se salta entero si no hay base disponible.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

psycopg = pytest.importorskip("psycopg")

from api.services import consultas  # noqa: E402

# Códigos fuera de DIVIPOLA real: no colisionan con datos cargados.
DEPTO_TEST = "ZZ"
MUNICIPIO_TEST = "99999"
INDICADOR_TEST = "test_integracion_sql"


def _conectar():
    from api.db import obtener_conexion

    return obtener_conexion()


@pytest.fixture(scope="module")
def bd():
    """Conexión a la BD real; salta el módulo entero si no hay o falta esquema."""
    try:
        with _conectar() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1 FROM curated.municipio LIMIT 1")
    except Exception as exc:
        pytest.skip(f"sin PostgreSQL con esquema curated: {exc}")
    return True


@pytest.fixture(scope="module")
def territorio_sembrado(bd):
    """Siembra territorio + indicador + serie mínimos y los retira al terminar.

    Hace falta sembrar: con la BD vacía de CI, `ficha_territorio()` saldría en el
    primer SELECT sin llegar nunca al JOIN que tenía el error.
    """
    from api.db import obtener_conexion

    with obtener_conexion() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO curated.departamento (codigo_divipola, nombre) VALUES (%s, %s) "
                "ON CONFLICT (codigo_divipola) DO UPDATE SET nombre = EXCLUDED.nombre "
                "RETURNING departamento_id",
                (DEPTO_TEST, "DEPARTAMENTO DE PRUEBA"),
            )
            depto_id = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO curated.municipio (codigo_divipola, nombre, departamento_id) "
                "VALUES (%s, %s, %s) ON CONFLICT (codigo_divipola, valido_desde) DO UPDATE "
                "SET nombre = EXCLUDED.nombre RETURNING municipio_id",
                (MUNICIPIO_TEST, "MUNICIPIO DE PRUEBA", depto_id),
            )
            municipio_id = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO curated.fuentes "
                "(codigo, nombre, entidad, tipo, metodo_acceso, periodicidad, formato, "
                " licencia, activa) "
                "VALUES (%s, %s, %s, 'nacional', 'descarga', 'anual', 'CSV', 'prueba', true) "
                "ON CONFLICT (codigo) DO UPDATE SET nombre = EXCLUDED.nombre RETURNING fuente_id",
                ("test_integracion", "Fuente de prueba", "Prueba"),
            )
            fuente_id = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO curated.indicadores "
                "(codigo, nombre, unidad, granularidad_min, periodicidad, fuente_primaria_id) "
                "VALUES (%s, %s, 'casos', 'municipio', 'anual', %s) "
                "ON CONFLICT (codigo) DO UPDATE SET nombre = EXCLUDED.nombre "
                "RETURNING indicador_id",
                (INDICADOR_TEST, "Indicador de prueba", fuente_id),
            )
            indicador_id = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO curated.serie_historica "
                "(indicador_id, municipio_id, periodo_inicio, periodo_fin, valor, fuente_id, "
                " fecha_extraccion, hash_registro) "
                "VALUES (%s, %s, %s, %s, 7, %s, %s, %s) ON CONFLICT DO NOTHING",
                (
                    indicador_id,
                    municipio_id,
                    date(2025, 1, 1),
                    date(2025, 12, 31),
                    fuente_id,
                    datetime.now(UTC),
                    "hash_test_integracion",
                ),
            )

    yield MUNICIPIO_TEST

    with obtener_conexion() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM curated.serie_historica WHERE hash_registro = 'hash_test_integracion'"
            )
            cur.execute("DELETE FROM curated.indicadores WHERE codigo = %s", (INDICADOR_TEST,))
            cur.execute("DELETE FROM curated.municipio WHERE codigo_divipola = %s", (MUNICIPIO_TEST,))
            cur.execute("DELETE FROM curated.departamento WHERE codigo_divipola = %s", (DEPTO_TEST,))
            cur.execute("DELETE FROM curated.fuentes WHERE codigo = 'test_integracion'")


# ── El caso que se escapó ────────────────────────────────────────────────────


def test_ficha_territorio_ejecuta_todas_sus_consultas(territorio_sembrado):
    """Regresión del 500: el JOIN con departamento tenía `nombre` sin calificar.

    Solo se dispara con un municipio existente, por eso el fixture siembra uno.
    """
    ficha = consultas.ficha_territorio(territorio_sembrado)

    assert ficha is not None
    assert ficha["municipio"] == "MUNICIPIO DE PRUEBA"
    assert ficha["departamento"] == "DEPARTAMENTO DE PRUEBA"
    assert any(i["codigo"] == INDICADOR_TEST for i in ficha["indicadores"])


def test_ficha_territorio_inexistente_devuelve_none(bd):
    assert consultas.ficha_territorio("00000") is None


# ── El resto de la superficie SQL ────────────────────────────────────────────


def test_consultar_territorio(territorio_sembrado):
    territorio = consultas.consultar_territorio(territorio_sembrado)
    assert territorio["nombre"] == "MUNICIPIO DE PRUEBA"
    assert territorio["departamento"] == "DEPARTAMENTO DE PRUEBA"


def test_indicador_existe(territorio_sembrado):
    assert consultas.indicador_existe(INDICADOR_TEST) is True
    assert consultas.indicador_existe("no_existe_este_indicador") is False


def test_consultar_serie_con_y_sin_filtros(territorio_sembrado):
    filas, _cursor = consultas.consultar_serie(INDICADOR_TEST)
    assert filas and filas[0]["valor"] == 7

    filtradas, _ = consultas.consultar_serie(
        INDICADOR_TEST, territorio=territorio_sembrado, desde="2020-01-01", hasta="2030-12-31"
    )
    assert len(filtradas) == 1

    vacias, _ = consultas.consultar_serie(INDICADOR_TEST, territorio="00000")
    assert vacias == []


def test_consultar_serie_pagina_con_cursor(territorio_sembrado):
    """La rama con cursor añade una condición al WHERE: es SQL distinto."""
    filas, cursor = consultas.consultar_serie(INDICADOR_TEST, limit=1)
    assert len(filas) == 1
    if cursor:
        siguientes, _ = consultas.consultar_serie(INDICADOR_TEST, limit=1, cursor=cursor)
        assert isinstance(siguientes, list)


def test_poblacion_para_modo_tasa(bd):
    """El cruce con población alimenta el modo 'tasa' de las rutas."""
    poblacion = consultas._poblacion_municipio_anio()
    assert isinstance(poblacion, dict)


def test_consultar_total(territorio_sembrado):
    total = consultas.consultar_total(INDICADOR_TEST)
    assert total["indicador"] == INDICADOR_TEST
    assert total["totales"][0]["valor"] == 7


def test_consultar_mapa(territorio_sembrado):
    mapa = consultas.consultar_mapa(INDICADOR_TEST)
    assert mapa is None or mapa["type"] == "FeatureCollection"


def test_consultar_mapa_indicador_inexistente(bd):
    assert consultas.consultar_mapa("no_existe_este_indicador") is None


def test_exportar_serie_csv(territorio_sembrado):
    filas = consultas.exportar_serie_csv(INDICADOR_TEST)
    assert filas and filas[0]["indicador"] == INDICADOR_TEST


def test_listar_fuentes_incluye_frescura(bd):
    fuentes = consultas.listar_fuentes()
    assert isinstance(fuentes, list)
    if fuentes:
        # El LEFT JOIN con vw_frescura_fuentes debe resolver aunque no haya datos.
        assert "frescura" in fuentes[0]


def test_listar_frescura(bd):
    estados = {"al_dia", "retrasada", "obsoleta", "sin_datos"}
    for fila in consultas.listar_frescura():
        assert fila["frescura"] in estados


def test_contar_proyectos_pdet(bd):
    conteo = consultas.contar_proyectos_pdet()
    assert conteo["proyectos"] >= 0
    assert conteo["municipios"] >= 0


# ── Acumulación: el otro fallo que solo aparece contra una BD real ───────────


def test_serie_departamental_no_se_duplica_entre_corridas(territorio_sembrado):
    """Regresión de la inflación ×3 (migración 0017).

    `uq_serie_dedup` era UNIQUE a secas: PostgreSQL trata cada NULL como
    distinto, así que las series **departamentales** (municipio_id NULL) no
    conflictuaban nunca y el ETL las reinsertaba en cada corrida. La API llegó a
    servir 16.716 eventos ACLED de 2025 en vez de 5.572.

    Cargar dos veces el mismo lote debe dejar una sola fila.
    """
    import pandas as pd

    from api.db import obtener_conexion
    from etl.common.cargar import insertar_serie

    with obtener_conexion() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT indicador_id FROM curated.indicadores WHERE codigo = %s", (INDICADOR_TEST,))
            indicador_id = cur.fetchone()[0]
            cur.execute("SELECT fuente_id FROM curated.fuentes WHERE codigo = 'test_integracion'")
            fuente_id = cur.fetchone()[0]

        df = pd.DataFrame(
            {
                "indicador_id": [indicador_id],
                "codigo_divipola": [DEPTO_TEST],  # 2 dígitos → municipio_id NULL
                "periodo_inicio": [date(2024, 1, 1)],
                "periodo_fin": [date(2024, 12, 31)],
                "valor": [42.0],
            }
        )
        ahora = datetime.now(UTC)
        insertar_serie(conn, df, fuente_id=fuente_id, url_origen="test", fecha_extraccion=ahora)
        insertar_serie(conn, df, fuente_id=fuente_id, url_origen="test", fecha_extraccion=ahora)

        with conn.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM curated.serie_historica "
                "WHERE indicador_id = %s AND municipio_id IS NULL AND periodo_inicio = %s",
                (indicador_id, date(2024, 1, 1)),
            )
            copias = cur.fetchone()[0]
            cur.execute(
                "DELETE FROM curated.serie_historica "
                "WHERE indicador_id = %s AND periodo_inicio = %s",
                (indicador_id, date(2024, 1, 1)),
            )

    assert copias == 1, f"la fila departamental se duplicó ({copias} copias)"
