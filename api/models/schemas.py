"""Modelos Pydantic de la API (sección 8: tipado y documentación automática)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class FuenteOut(BaseModel):
    fuente_id: int
    nombre: str
    entidad: str
    licencia: str
    ultima_actualizacion: datetime | None
    url_base: str | None


class MunicipioOut(BaseModel):
    municipio_id: int
    codigo_divipola: str
    nombre: str
    departamento: str


class SerieOut(BaseModel):
    indicador: str
    municipio: str | None
    periodo_inicio: date
    periodo_fin: date
    valor: float
    fuente: str
    fecha_extraccion: datetime


class Pagina(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None = Field(
        description="Cursor opaco para la siguiente página; null si no hay más."
    )


class ErrorOut(BaseModel):
    detalle: str


class FuenteEstadoOut(BaseModel):
    variable: str
    fuente: str
    configurada: bool
    ayuda: str
    ultima_corrida_exitosa: datetime | None


class HealthOut(BaseModel):
    estado: str
    fuentes: list[FuenteEstadoOut]


class PdetOut(BaseModel):
    proyectos: int
    municipios: int


class TotalAnualOut(BaseModel):
    anio: int
    valor: float


class IndicadorTotalOut(BaseModel):
    indicador: str
    nombre: str
    unidad: str
    totales: list[TotalAnualOut]


class MapaFeatureOut(BaseModel):
    type: str
    geometry: dict
    properties: dict


class MapaOut(BaseModel):
    indicador: str
    nombre: str
    unidad: str
    anio: int | None
    type: str
    features: list[MapaFeatureOut]
