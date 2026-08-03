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

from etl.common.config import (
    settings,  # noqa: F401 — dispara la carga de .env al importar
)
from etl.common.db import conectar, insertar_raw, registrar_metricas
from etl.common.lineage import Lineage, hash_registro
from etl.common.logs import obtener_logger_etl

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
        # Los pipelines con canal lateral (Policía_Homicidios guarda datos
        # en self._datos y extraer() devuelve 1 fila de metadatos; IDEAM
        # guarda self._ruta_img) deben sobrescribir _leidos con el número
        # real de filas procesadas. Si se deja en None, ejecutar() usa
        # len(df) de extraer().
        self._leidos: int | None = None
        # Los pipelines que agregan (groupby), dividen filas en rutas
        # paralelas o usan canales laterales deben sobrescribir _rechazados
        # con el conteo real de filas descartadas por calidad inválida.
        # Si se deja en None, ejecutar() usa leidos - validos.
        self._rechazados: int | None = None

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
        log = obtener_logger_etl(self.pipeline_id)
        inicio = time.monotonic()
        estado, error, leidos, validos, rechazados, nulos = "exitoso", None, 0, 0, 0, {}
        conn: psycopg.Connection | None = None
        try:
            conn = conectar()
            self._conn = conn
            df, self.lineage = self.extraer()
            leidos_raw = len(df)

            # F5.2 (plan.md): df.to_dict("records") en vez de iterrows()
            # + hash_registro por fila. Con 682k filas (policia_violencia),
            # iterrows() dominaba los 118 s del pipeline.
            archivo = f"{self.pipeline_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filas_raw = [
                {
                    "archivo": archivo,
                    "contenido": fila,
                    "url_origen": self.lineage.url_origen,
                    "fecha_extraccion": self.lineage.fecha_extraccion,
                    "hash_fila": hash_registro(fila),
                }
                for fila in df.to_dict("records")
            ]
            nuevas_raw = insertar_raw(conn, self.tabla_raw, filas_raw)
            conn.commit()
            if nuevas_raw != leidos_raw:
                # Migración 0016: raw deduplica por (hash_fila, ocurrencia), así
                # que reextraer un snapshot ya visto no lo reescribe entero.
                log.info(
                    "raw.%s: %d filas extraídas, %d nuevas (%d ya estaban)",
                    self.tabla_raw,
                    leidos_raw,
                    nuevas_raw,
                    leidos_raw - nuevas_raw,
                )

            df_staging = self.transformar(df)
            # _leidos se re-evalúa tras transformar() porque los pipelines
            # de canal lateral (IDEAM, Policia_Homicidios) lo fijan ahí.
            leidos = self._leidos if self._leidos is not None else leidos_raw
            validos = len(df_staging)
            if self._rechazados is not None:
                rechazados = self._rechazados
            else:
                # F0.4 (plan.md): sin override explícito, reportar 0 en vez de
                # inventar un número con leidos - validos (que confunde
                # agregación y filtrado con rechazo real).
                rechazados = 0
                if leidos != validos:
                    log.warning(
                        "%d filas de diferencia entre extraer() y transformar() "
                        "sin self._rechazados declarado → registros_rechazados = 0",
                        abs(leidos - validos),
                    )
            nulos = _nulos_columnas_criticas(df_staging)
            self.cargar_curated(df_staging)
            # Umbral de rechazo: si más del umbral configurable de filas
            # fue descartado por calidad inválida, marcar como 'parcial'
            # en vez de 'exitoso' (plan.md Bug 7, 2026-08-03).
            from etl.common.config import settings

            umbral = float(getattr(settings, "etl_umbral_rechazo", "0.20") or "0.20")
            if leidos and rechazados / leidos > umbral:
                estado = "parcial"
            conn.commit()
        except Exception as exc:
            estado, error = "fallido", str(exc)
            if conn is not None:
                conn.rollback()
        finally:
            if conn is not None:
                try:
                    # F0.3 (plan.md): validar contrato de métricas en la base
                    # antes de llegar al CHECK de Postgres.
                    if leidos < validos + rechazados:
                        raise ValueError(
                            f"[{self.pipeline_id}] métricas incoherentes: leidos={leidos} < "
                            f"validos={validos} + rechazados={rechazados}. Si el pipeline usa "
                            f"canal lateral, debe fijar self._leidos en transformar()."
                        )
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
                except Exception as exc:
                    conn.rollback()
                    log.warning("no se registraron métricas: %s", exc)
                finally:
                    conn.close()
                    self._conn = None
            if estado == "fallido":
                raise RuntimeError(f"Pipeline {self.pipeline_id} falló: {error}")
