"""Siembra la capa geo de municipios (tipo 'divipola') en
curated.capa_contexto_territorial a partir de los límites oficiales COD-AB
(HDX/OCHA, fuente MGN DANE-IGAC, admin2 = municipios, EPSG:4326).

Uso: python -m etl.common.capas_geo

Prerrequisito: catálogo DIVIPOLA sembrado (python -m etl.common.divipola) para
poder reportar municipios del catálogo sin geometría y viceversa.
Idempotente: reemplaza la capa tipo='divipola' en cada corrida.
"""

from __future__ import annotations

import tempfile
import zipfile
import json
from pathlib import Path

import geopandas as gpd
import psycopg
import requests

from etl.common.cargar import upsert_fuente
from etl.common.config import settings
from etl.common.db import conectar, transaccion
from etl.common.descargas import descargar_con_limite

# Recurso fijo de https://data.humdata.org/dataset/cod-ab-col
RECURSO_COD_AB = "32fba556-0109-4d1c-84cb-c8abddf7775b"


def _url_firmada() -> str:
    resp = requests.get(
        f"{settings.hdx_base_url}/action/resource_show",
        params={"id": RECURSO_COD_AB},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["result"]["url"]


def _leer_municipios(url: str) -> gpd.GeoDataFrame:
    print("[capas_geo] descargando límites COD-AB (admin2)…")
    # Límite de tamaño de descarga (auditoría 2026-08-02)
    contenido = descargar_con_limite(url, timeout=900)
    # El .shp necesita sus sidecars (.dbf/.shx): se extrae a disco temporal.

    with tempfile.TemporaryDirectory() as tmp:
        zip_ruta = Path(tmp) / "codab.zip"
        zip_ruta.write_bytes(contenido)
        with zipfile.ZipFile(zip_ruta) as z:
            z.extractall(tmp)
        nombre = next(Path(tmp).glob("*adm2*.shp"))
        gdf = gpd.read_file(nombre)
    gdf = gdf.to_crs(4326)
    return gdf


def sembrar() -> None:
    url = _url_firmada()
    gdf = _leer_municipios(url)
    with transaccion(conectar()) as conn:
        fuente_id = upsert_fuente(
            conn,
            nombre="IGAC-DANE (COD-AB)",
            entidad="Instituto Geográfico Agustín Codazzi / DANE (vía OCHA COD-AB)",
            tipo="nacional",
            descripcion="Límites municipales oficiales admin2 (MGN), fuente del catálogo geo",
            url_base="https://data.humdata.org/dataset/cod-ab-col",
            metodo_acceso="descarga",
            periodicidad="variable",
            formato="SHP",
            licencia="COD-AB (OCHA) — revisar ficha (sección 3, punto 5)",
            ficha_doc="docs/fuentes/ideam.md",
        )
        with conn.cursor() as cur:
            cur.execute("DELETE FROM curated.capa_contexto_territorial WHERE tipo = 'divipola'")
            for _, fila in gdf.iterrows():
                codigo = str(fila["ADM2_PCODE"])
                if codigo.startswith("CO"):
                    codigo = codigo[2:]
                cur.execute(
                    """
                    INSERT INTO curated.capa_contexto_territorial
                        (tipo, nombre, geometria, codigo_divipola, fuente_id, url_origen)
                    VALUES ('divipola', %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326), %s, %s, %s)
                    """,
                    (
                        fila["ADM2_ES"],
                        json.dumps(fila["geometry"].__geo_interface__),
                        codigo,
                        fuente_id,
                        url,
                    ),
                )
        print(f"[capas_geo] {len(gdf)} municipios sembrados (tipo 'divipola').")
        _reportar_cobertura(conn)


def _reportar_cobertura(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM curated.municipio WHERE vigente")
        catalogo = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM curated.capa_contexto_territorial WHERE tipo = 'divipola'")
        capa = cur.fetchone()[0]
        cur.execute(
            """
            SELECT count(*) FROM curated.municipio m
            LEFT JOIN curated.capa_contexto_territorial c
              ON c.tipo = 'divipola' AND c.codigo_divipola = m.codigo_divipola
            WHERE m.vigente AND c.capa_id IS NULL
            """
        )
        sin_geo = cur.fetchone()[0]
    print(f"[capas_geo] catálogo: {catalogo} municipios | capa: {capa} | sin geometría: {sin_geo}")


if __name__ == "__main__":
    sembrar()
