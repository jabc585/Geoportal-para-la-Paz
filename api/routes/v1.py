"""Rutas núcleo de la API v1 (sección 8)."""

from __future__ import annotations

import csv
import io
import os

from fastapi import APIRouter, HTTPException, Path, Query, Request
from fastapi.responses import StreamingResponse

from api.limiter import limiter
from api.models.schemas import (
    FuenteEstadoOut,
    FuenteOut,
    HealthOut,
    IndicadorTotalOut,
    MapaOut,
    MunicipioOut,
    Pagina,
    PdetOut,
    SerieOut,
)
from api.services.consultas import (
    consultar_mapa,
    consultar_serie,
    consultar_territorio,
    consultar_total,
    contar_proyectos_pdet,
    exportar_serie_csv,
    indicador_existe,
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
@limiter.limit(os.getenv("API_RATE_LIMIT", "120/minute"))
def get_health(request: Request) -> HealthOut:
    return HealthOut(estado="ok", fuentes=[FuenteEstadoOut(**f) for f in estado_fuentes()])


@router.get(
    "/pdet/proyectos",
    response_model=PdetOut,
    summary="Conteos del módulo PDET",
    description=(
        "Proyectos y municipios PDET cargados desde el dataset de iniciativas "
        "de la ART (sección 11 del plan)."
    ),
)
@limiter.limit(os.getenv("API_RATE_LIMIT", "120/minute"))
def get_pdet_proyectos(request: Request) -> PdetOut:
    return PdetOut(**contar_proyectos_pdet())


@router.get(
    "/territorios/{codigo_divipola}",
    response_model=MunicipioOut,
    summary="Municipio por código DIVIPOLA",
)
@limiter.limit(os.getenv("API_RATE_LIMIT", "120/minute"))
def get_territorio(request: Request, codigo_divipola: str = Path(pattern=r"^\d{2,5}$")) -> MunicipioOut:
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
@limiter.limit(os.getenv("API_RATE_LIMIT", "120/minute"))
def get_indicador(
    request: Request,
    indicador: str = Path(pattern=r"^[a-z0-9_]+$"),
    territorio: str | None = Query(default=None, description="Código DIVIPOLA (5 dígitos municipio o 2 departamento)"),
    desde: str | None = Query(default=None, description="Fecha inicio del periodo (YYYY-MM-DD)"),
    hasta: str | None = Query(default=None, description="Fecha fin del periodo (YYYY-MM-DD)"),
    limit: int = Query(default=100, ge=1, le=1000),
    cursor: str | None = Query(default=None, description="Cursor de paginación devuelto por la API"),
) -> Pagina[SerieOut]:
    try:
        filas, next_cursor = consultar_serie(indicador, territorio, desde, hasta, limit, cursor)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not filas and not indicador_existe(indicador):
        raise HTTPException(status_code=404, detail="Indicador no encontrado")
    return Pagina(items=[SerieOut(**f) for f in filas], next_cursor=next_cursor)


@router.get(
    "/indicadores/{indicador}/total",
    response_model=IndicadorTotalOut,
    summary="Total nacional por año de un indicador (KPIs del dashboard)",
)
@limiter.limit(os.getenv("API_RATE_LIMIT", "120/minute"))
def get_indicador_total(
    request: Request,
    indicador: str = Path(pattern=r"^[a-z0-9_]+$"),
) -> IndicadorTotalOut:
    resultado = consultar_total(indicador)
    if not resultado:
        raise HTTPException(status_code=404, detail="Indicador no encontrado")
    return IndicadorTotalOut(**resultado)


@router.get(
    "/fuentes",
    response_model=list[FuenteOut],
    summary="Catálogo de fuentes con metadatos de linaje",
)
@limiter.limit(os.getenv("API_RATE_LIMIT", "120/minute"))
def get_fuentes(request: Request) -> list[FuenteOut]:
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
@limiter.limit(os.getenv("API_RATE_LIMIT", "120/minute"))
def get_mapa(
    request: Request,
    indicador: str = Path(pattern=r"^[a-z0-9_]+$"),
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
@limiter.limit("10/minute")
def get_indicador_csv(
    request: Request,
    indicador: str = Path(pattern=r"^[a-z0-9_]+$"),
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
