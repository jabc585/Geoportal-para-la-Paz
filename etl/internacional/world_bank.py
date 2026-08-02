"""Conector de comparabilidad internacional: Banco Mundial (sección 5.2 y 7.6).

API oficial de World Bank Open Data: datos a nivel país. Se cargan en
curated.indicador_internacional, deliberadamente separados de la serie por
municipio (sección 7.6). Los indicadores se configuran con la variable
WB_INDICADORES como lista "codigo:nombres" separada por comas.
"""

from __future__ import annotations

import os

import pandas as pd
import psycopg
import requests

from etl.common.cargar import insertar_indicador_internacional, upsert_fuente
from etl.common.lineage import Lineage, hash_registro
from etl.common.db import transaccion
from etl.common.pipeline import PipelineETL

URL_WB = "https://api.worldbank.org/v2/country/CO/indicator"
PAIS = "Colombia"


class Internacional_WorldBank(PipelineETL):
    pipeline_id = "internacional_worldbank"
    tabla_raw = "internacional_worldbank"

    def _indicadores(self) -> dict[str, str]:
        """Devuelve {codigo_indicator: nombre} desde WB_INDICADORES."""
        lista = os.getenv("WB_INDICADORES", "")
        if not lista:
            raise ValueError(
                "Variable WB_INDICADORES no configurada, p. ej. 'NY.GDP.PCAP.PP.CD:PIB per cápita (PPA)'"
            )
        resultado = {}
        for item in lista.split(","):
            codigo, _, nombre = item.partition(":")
            resultado[codigo.strip()] = nombre.strip() or codigo.strip()
        return resultado

    def extraer(self) -> tuple[pd.DataFrame, Lineage]:
        filas = []
        for codigo, nombre in self._indicadores().items():
            url = f"{URL_WB}/{codigo}"
            resp = requests.get(url, params={"format": "json", "per_page": 100}, timeout=60)
            resp.raise_for_status()
            cuerpo = resp.json()
            if not isinstance(cuerpo, list) or len(cuerpo) < 2:
                continue
            for dato in cuerpo[1]:
                filas.append(
                    {
                        "indicador_codigo": codigo,
                        "indicador_nombre": nombre,
                        "anio": dato.get("date"),
                        "valor": dato.get("value"),
                    }
                )
        df = pd.DataFrame(filas)
        url_origen = f"{URL_WB}/{next(iter(self._indicadores()), '')}"
        lineage = Lineage.ahora(
            fuente="Banco Mundial",
            url_origen=url_origen,
            fecha_corte_dato=None,
            licencia="Open Data (CC BY 4.0)",
        )
        return df, lineage

    def transformar(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        df = df.dropna(subset=["valor"])
        df["anio"] = pd.to_numeric(df["anio"], errors="coerce")
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
        return df.dropna(subset=["anio"])

    def cargar_curated(self, df: pd.DataFrame) -> None:
        if df.empty:
            return
        with transaccion(self.conn):
            fuente_id = self._fuente_id()
            insertadas = insertar_indicador_internacional(
                self.conn, df, fuente_id, PAIS,
                self.lineage.url_origen, self.lineage.fecha_extraccion,
                self.lineage.fecha_corte_dato, unidad=None,
                col_indicador="indicador_nombre",
            )
            print(f"[worldbank] indicadores internacionales cargados: {insertadas}")

    def _fuente_id(self) -> int:
        from etl.common.cargar import upsert_fuente

        return upsert_fuente(
            self.conn,
            nombre="Banco Mundial",
            entidad="World Bank Open Data",
            tipo="internacional",
            descripcion="PIB, pobreza, indicadores sociales y de desarrollo (sección 5.2)",
            url_base="https://data.worldbank.org/",
            metodo_acceso="api",
            periodicidad="anual",
            formato="JSON",
            licencia=self.lineage.licencia,
            ficha_doc="docs/fuentes/internacional.md",
        )


if __name__ == "__main__":
    Internacional_WorldBank().ejecutar()
