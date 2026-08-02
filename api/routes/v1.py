"""Rutas núcleo de la API v1 (sección 8)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from api.models.schemas import (
    ErrorOut,
    FuenteEstadoOut,
    FuenteOut,
    HealthOut,
    IndicadorTotalOut,
    MunicipioOut,
    Pagina,
    SerieOut,
)
from api.services.consultas import consultar_serie, consultar_territorio, consultar_total, listar_fuentes
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
