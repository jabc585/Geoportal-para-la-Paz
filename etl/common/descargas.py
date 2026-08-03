"""Descargas HTTP con límite de tamaño (auditoría 2026-08-02).

Los pipelines traen archivos grandes (raster ZIP de IDEAM, CSV de HDX con
346K filas, shapefiles COD-AB). Sin stream ni chequeo de Content-Length, una
fuente que cambie de comportamiento puede agotar la memoria del proceso. Este
helper descarga con `stream=True` y rechaza respuestas por encima del tope.
"""

from __future__ import annotations

import io

import requests

MAX_BYTES_DEFAULT = 512 * 1024 * 1024  # 512 MiB: margen holgado para raster IDEAM


class DescargaDemasiadoGrande(RuntimeError):
    """La respuesta excede el límite de tamaño configurado."""


def descargar_con_limite(
    url: str,
    *,
    timeout: int = 600,
    max_bytes: int = MAX_BYTES_DEFAULT,
    **kwargs,
) -> bytes:
    """Descarga con stream y verificación de tamaño antes de acumular en memoria.

    Rechaza temprano si Content-Length declarada supera el tope, y corta el
    stream si lo descargado lo supera (fuentes que no declaran Content-Length).
    """
    resp = requests.get(url, stream=True, timeout=timeout, **kwargs)
    resp.raise_for_status()
    headers = getattr(resp, "headers", {}) or {}
    content_length = headers.get("Content-Length")
    if content_length is not None and int(content_length) > max_bytes:
        resp.close()
        raise DescargaDemasiadoGrande(
            f"Respuesta de {url} declara {content_length} bytes "
            f"(límite {max_bytes}): revisar la fuente"
        )
    chunks = []
    acumulado = 0
    for chunk in resp.iter_content(chunk_size=1024 * 1024):
        acumulado += len(chunk)
        if acumulado > max_bytes:
            resp.close()
            raise DescargaDemasiadoGrande(
                f"Respuesta de {url} superó {max_bytes} bytes: revisar la fuente"
            )
        chunks.append(chunk)
    resp.close()
    return b"".join(chunks)


def descargar_a_buffer(
    url: str,
    *,
    timeout: int = 600,
    max_bytes: int = MAX_BYTES_DEFAULT,
    **kwargs,
) -> io.BytesIO:
    """Variante que devuelve un BytesIO (consumo directo de pandas.read_csv)."""
    return io.BytesIO(descargar_con_limite(url, timeout=timeout, max_bytes=max_bytes, **kwargs))


def descargar_socrata_paginado(
    url: str,
    *,
    tamano_pagina: int = 50_000,
    timeout: int = 300,
) -> list[dict]:
    """Descarga paginada de Socrata ($limit/$offset) con app token opcional.

    Usada por Policía (hurto/violencia/sexuales), CNMH y PDET; evita duplicar el
    patrón de paginación en cada pipeline (auditoría 2026-08-02, hallazgo 10).
    Si la variable SOCRATA_APP_TOKEN está configurada, se envía como
    X-App-Token para superar el límite público de ~1000 req/hora.
    """
    from etl.common.config import settings

    token = settings.socrata_app_token
    filas: list[dict] = []
    offset = 0
    while True:
        cabeceras = {"X-App-Token": token} if token else {}
        resp = requests.get(
            url,
            params={"$limit": tamano_pagina, "$offset": offset},
            headers=cabeceras,
            timeout=timeout,
        )
        resp.raise_for_status()
        batch = resp.json()
        filas.extend(batch)
        if len(batch) < tamano_pagina:
            return filas
        offset += len(batch)
