"""Rutas núcleo de la API v1 (sección 8)."""

from __future__ import annotations

import csv
import io

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from api.models.schemas import (
    ErrorOut,
    FuenteEstadoOut,
    FuenteOut,
    HealthOut,
    IndicadorTotalOut,
    MapaOut,
    MunicipioOut,
    Pagina,
    SerieOut,
)
from api.services.consultas import (
    consultar_mapa,
    consultar_serie,
    consultar_territorio,
    consultar_total,
    exportar_serie_csv,
    listar_fuentes,
)
from api.services.health import estado_fuentes

router = APIRouter(prefix="/api/v1", tags=["v1"])


@router.get(
    "/health",
    response_model=HealthOut,
    summary="Estado de configuración de fuentes y últimas corridas",
    description=(
        "Reporta por fuente si su variable de entorno está configurada y la "
        "fecha de la última corrida ETL exitosa (curated.data_quality_metrics). "
        "No expone valores de variables, solo su presencia (plan2.md, Fase A)."
    ),
)
def get_health() -> HealthOut:
    return HealthOut(estado="ok", fuentes=[FuenteEstadoOut(**f) for f in estado_fuentes()])


@router.get(
    "/territorios/{codigo_divipola}",
    response_model=MunicipioOut | ErrorOut,
    summary="Municipio por código DIVIPOLA",
)
def get_territorio(codigo_divipola: str) -> MunicipioOut | ErrorOut:
    resultado = consultar_territorio(codigo_divipola)
    if not resultado:
        raise HTTPException(status_code=404, detail="Territorio no encontrado")
    return MunicipioOut(**resultado)


@router.get(
    "/indicadores/{indicador}",
    response_model=Pagina[SerieOut],
    summary="Serie histórica de un indicador con paginación por cursor",
    description=(
        "Filtros opcionales por territorio (código DIVIPOLA), periodo (desde/hasta). "
        "Paginación por cursor opaco: repetir la consulta con next_cursor hasta que sea null. "
        "Tamaño máximo de página: 1000 (sección 8)."
    ),
)
def get_indicador(
    indicador: str,
    territorio: str | None = Query(default=None, description="Código DIVIPOLA (5 dígitos municipio o 2 departamento)"),
    desde: str | None = Query(default=None, description="Fecha inicio del periodo (YYYY-MM-DD)"),
    hasta: str | None = Query(default=None, description="Fecha fin del periodo (YYYY-MM-DD)"),
    limit: int = Query(default=100, ge=1, le=1000),
    cursor: str | None = Query(default=None, description="Cursor de paginación devuelto por la API"),
) -> Pagina[SerieOut]:
    filas, next_cursor = consultar_serie(indicador, territorio, desde, hasta, limit, cursor)
    return Pagina(items=[SerieOut(**f) for f in filas], next_cursor=next_cursor)


@router.get(
    "/indicadores/{indicador}/total",
    response_model=IndicadorTotalOut,
    summary="Total nacional por año de un indicador (KPIs del dashboard)",
)
def get_indicador_total(indicador: str) -> IndicadorTotalOut:
    resultado = consultar_total(indicador)
    if not resultado:
        raise HTTPException(status_code=404, detail="Indicador no encontrado")
    return IndicadorTotalOut(**resultado)


@router.get(
    "/fuentes",
    response_model=list[FuenteOut],
    summary="Catálogo de fuentes con metadatos de linaje",
)
def get_fuentes() -> list[FuenteOut]:
    return [FuenteOut(**f) for f in listar_fuentes()]


@router.get(
    "/mapas/{indicador}",
    response_model=MapaOut,
    summary="Capa coroplética municipal de un indicador (fase 5)",
    description=(
        "GeoJSON simplificado: agregado municipal del indicador para un año "
        "(por defecto el más reciente con datos) unido a la capa geo DIVIPOLA "
        "(sección 5.1). Los municipios sin dato salen con valor null."
    ),
)
def get_mapa(
    indicador: str,
    anio: int | None = Query(default=None, ge=1900, le=2100, description="Año del agregado; por defecto el más reciente"),
) -> MapaOut:
    resultado = consultar_mapa(indicador, anio)
    if not resultado:
        raise HTTPException(status_code=404, detail="Indicador no encontrado")
    return MapaOut(**resultado)


@router.get(
    "/indicadores/{indicador}/exportar.csv",
    summary="Serie completa de un indicador en CSV (sección 10: exportación de datos)",
    description=(
        "Mismos filtros que /indicadores/{indicador} pero sin paginación, para "
        "descarga directa. BOM UTF-8 para compatibilidad con Excel. "
        "Tope: 200.000 filas."
    ),
)
def get_indicador_csv(
    indicador: str,
    territorio: str | None = Query(default=None, description="Código DIVIPOLA (5 dígitos municipio o 2 departamento)"),
    desde: str | None = Query(default=None, description="Fecha inicio del periodo (YYYY-MM-DD)"),
    hasta: str | None = Query(default=None, description="Fecha fin del periodo (YYYY-MM-DD)"),
) -> StreamingResponse:
    filas = exportar_serie_csv(indicador, territorio, desde, hasta)
    if not filas:
        raise HTTPException(status_code=404, detail="Indicador sin datos")
    columnas = [
        "indicador",
        "indicador_nombre",
        "unidad",
        "codigo_divipola",
        "municipio",
        "departamento_divipola",
        "departamento",
        "periodo_inicio",
        "periodo_fin",
        "valor",
        "fuente",
    ]
    buffer = io.StringIO()
    buffer.write("\ufeff")
    writer = csv.DictWriter(buffer, fieldnames=columnas)
    writer.writeheader()
    writer.writerows(filas)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{indicador}.csv"'
        },
    )
