"""Plantilla base de pipeline ETL con trazabilidad y métricas (secciones 7.4 y 12).

Flujo: extract -> data/raw (inmutable) -> raw.<tabla> con linaje -> staging -> curated.
Los conectores piloto extienden esta clase.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from datetime import datetime

import pandas as pd

from etl.common.db import conectar, insertar_raw, registrar_metricas
from etl.common.lineage import Lineage, hash_registro


class PipelineETL(ABC):
    """Pipeline base: extrae, carga crudo con linaje y reporta métricas de calidad."""

    pipeline_id: str
    tabla_raw: str

    def __init__(self) -> None:
        self.lineage: Lineage | None = None
        self._conn = conectar()

    @abstractmethod
    def extraer(self) -> tuple[pd.DataFrame, Lineage]:
        """Descarga los datos crudos y devuelve (dataframe, linaje)."""

    @abstractmethod
    def transformar(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza a staging (códigos DIVIPOLA, periodos, valores numéricos)."""

    @abstractmethod
    def cargar_curated(self, df: pd.DataFrame) -> None:
        """Promueve datos validados a curated.serie_historica."""

    def ejecutar(self) -> None:
        inicio = time.monotonic()
        estado, error, leidos, validos, rechazados = "exitoso", None, 0, 0, 0
        try:
            df, self.lineage = self.extraer()
            leidos = len(df)

            filas_raw = [
                {
                    "archivo": f"{self.pipeline_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    "contenido": fila.to_dict(),
                    "url_origen": self.lineage.url_origen,
                    "fecha_extraccion": self.lineage.fecha_extraccion,
                    "hash_fila": hash_registro(fila.to_dict()),
                }
                for _, fila in df.iterrows()
            ]
            insertar_raw(self._conn, self.tabla_raw, filas_raw)

            df_staging = self.transformar(df)
            validos = len(df_staging)
            rechazados = leidos - validos
            self.cargar_curated(df_staging)
        except Exception as exc:  # noqa: BLE001
            estado, error = "fallido", str(exc)
        finally:
            registrar_metricas(
                self._conn,
                self.pipeline_id,
                leidos,
                validos,
                rechazados,
                nulos={},
                duracion_segundos=round(time.monotonic() - inicio, 2),
                estado=estado,
                mensaje_error=error,
            )
            if estado == "fallido":
                raise RuntimeError(f"Pipeline {self.pipeline_id} falló: {error}")
