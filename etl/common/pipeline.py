"""Plantilla base de pipeline ETL con trazabilidad y métricas (secciones 7.4 y 12).

Flujo: extract -> data/raw (inmutable) -> raw.<tabla> con linaje -> staging -> curated.
Los conectores piloto extienden esta clase.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from datetime import datetime

import pandas as pd
import psycopg

from etl.common.db import conectar, insertar_raw, registrar_metricas
from etl.common.lineage import Lineage, hash_registro
from etl.common.config import settings  # noqa: F401 — dispara la carga de .env al importar

COLUMNAS_CRITICAS = ["codigo_divipola", "periodo_inicio", "periodo_fin", "valor", "indicador_id"]


def _nulos_columnas_criticas(df: pd.DataFrame) -> dict:
    """Conteo de nulos por columna crítica del staging (hallazgo 14 auditoría 2026-08-02).

    Alimenta data_quality_metrics.nulos_por_columna_critica con números reales
    en vez de {}; solo cuenta columnas presentes (los pipelines que no cargan
    serie_historica, como PDET, no tienen las mismas columnas).
    """
    if df is None or df.empty:
        return {}
    return {col: int(df[col].isna().sum()) for col in COLUMNAS_CRITICAS if col in df.columns}


class PipelineETL(ABC):
    """Pipeline base: extrae, carga crudo con linaje y reporta métricas de calidad."""

    pipeline_id: str
    tabla_raw: str

    def __init__(self) -> None:
        self.lineage: Lineage | None = None
        self._conn: psycopg.Connection | None = None

    @property
    def conn(self) -> psycopg.Connection:
        """Conexión perezosa: solo se abre al ejecutar el pipeline."""
        if self._conn is None or self._conn.closed:
            self._conn = conectar()
        return self._conn

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
        """Corre la corrida completa con UNA conexión gestionada (auditoría 2026-08-02).

        La conexión se abre una sola vez, se commitea por fase y se cierra
        explícitamente en finally — incluidas las métricas (antes, el contexto
        `with self.conn` de cargar_curated cerraba la conexión y
        registrar_metricas reabría una huérfana por corrida). Con
        autocommit=False, cada fase es atómica: si falla, rollback completo.
        """
        inicio = time.monotonic()
        estado, error, leidos, validos, rechazados, nulos = "exitoso", None, 0, 0, 0, {}
        conn: psycopg.Connection | None = None
        try:
            conn = conectar()
            self._conn = conn
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
            insertar_raw(conn, self.tabla_raw, filas_raw)
            conn.commit()

            df_staging = self.transformar(df)
            validos = len(df_staging)
            rechazados = leidos - validos
            nulos = _nulos_columnas_criticas(df_staging)
            self.cargar_curated(df_staging)
            conn.commit()
        except Exception as exc:  # noqa: BLE001
            estado, error = "fallido", str(exc)
            if conn is not None:
                conn.rollback()
        finally:
            if conn is not None:
                try:
                    registrar_metricas(
                        conn,
                        self.pipeline_id,
                        leidos,
                        validos,
                        rechazados,
                        nulos=nulos,
                        duracion_segundos=round(time.monotonic() - inicio, 2),
                        estado=estado,
                        mensaje_error=error,
                    )
                    conn.commit()
                finally:
                    conn.close()
                    self._conn = None
            if estado == "fallido":
                raise RuntimeError(f"Pipeline {self.pipeline_id} falló: {error}")
