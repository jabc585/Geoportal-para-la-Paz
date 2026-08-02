"""Conector internacional: UNHCR/ACNUR (plan2.md Fase B, fuente 1).

API pública de UNHCR (sin autenticación, verificada en vivo 2026-08-02):
series anuales de población colombiana por tipo de protección. Se cargan en
curated.indicador_internacional, igual que World Bank (sección 7.6): a nivel
país, separadas de la serie municipal.
"""

from __future__ import annotations

import pandas as pd
import requests

from etl.common.config import get_source_url
from etl.common.db import transaccion
from etl.common.lineage import Lineage, hash_registro
from etl.common.pipeline import PipelineETL

PAIS = "Colombia"

# columna de la API → nombre del indicador en curated.indicadores
TIPOS_POBLACION = {
    "refugees": "Población refugiada colombiana",
    "asylum_seekers": "Solicitantes de asilo colombianos",
    "returned_refugees": "Retornados refugiados",
    "idps": "Desplazados internos (IDP)",
    "returned_idps": "Retornados desplazados internos",
    "stateless": "Apátridas",
    "ooc": "Otros en necesidad de protección (OOC)",
    "oip": "Otros en situación similar a IDP (OIP)",
}


class Internacional_UNHCR(PipelineETL):
    pipeline_id = "internacional_unhcr"
    tabla_raw = "internacional_unhcr"

    def _url_base(self) -> str:
        return get_source_url(
            "UNHCR_BASE_URL",
            ayuda="API pública de UNHCR (default: https://api.unhcr.org/population/v1)",
        )

    def extraer(self) -> tuple[pd.DataFrame, Lineage]:
        url = f"{self._url_base()}/population/"
        resp = requests.get(url, params={"coo": "COL"}, timeout=60)
        resp.raise_for_status()
        filas = []
        for item in resp.json().get("items", []):
            anio = item.get("year")
            for columna, nombre in TIPOS_POBLACION.items():
                filas.append(
                    {
                        "indicador": nombre,
                        "anio": anio,
                        "valor": item.get(columna),
                    }
                )
        df = pd.DataFrame(filas)
        lineage = Lineage.ahora(
            fuente="UNHCR",
            url_origen=url,
            fecha_corte_dato=None,
            licencia="UNHCR Public Data (acceso público)",
        )
        return df, lineage

    def transformar(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        # "-" y "0" literales: no son datos (la API los usa como NA)
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
        df = df.dropna(subset=["valor"])
        df["anio"] = pd.to_numeric(df["anio"], errors="coerce")
        return df.dropna(subset=["anio"])

    def cargar_curated(self, df: pd.DataFrame) -> None:
        if df.empty:
            return
        with transaccion(self.conn):
            fuente_id = self._fuente_id()
            insertadas = 0
            with self.conn.cursor() as cur:
                for fila in df.to_dict("records"):
                    cur.execute(
                        """
                        INSERT INTO curated.indicador_internacional
                            (fuente_id, pais, indicador, periodo, valor, unidad,
                             url_origen, fecha_extraccion, fecha_corte_dato, hash_registro)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (fuente_id, pais, indicador, periodo) DO NOTHING
                        """,
                        (
                            fuente_id,
                            PAIS,
                            fila["indicador"],
                            f"{int(fila['anio'])}-01-01",
                            float(fila["valor"]),
                            "personas",
                            self.lineage.url_origen,
                            self.lineage.fecha_extraccion,
                            self.lineage.fecha_corte_dato,
                            hash_registro(fila),
                        ),
                    )
                    insertadas += cur.rowcount > 0
            print(f"[unhcr] indicadores internacionales cargados: {insertadas}")

    def _fuente_id(self) -> int:
        from etl.common.cargar import upsert_fuente

        return upsert_fuente(
            self.conn,
            nombre="UNHCR",
            entidad="Oficina del Alto Comisionado de las Naciones Unidas para los Refugiados",
            tipo="internacional",
            descripcion="Población refugiada, solicitantes de asilo y desplazados de Colombia (sección 5.2)",
            url_base="https://www.unhcr.org/",
            metodo_acceso="api",
            periodicidad="anual",
            formato="JSON",
            licencia=self.lineage.licencia,
            ficha_doc="docs/fuentes/unhcr.md",
        )


if __name__ == "__main__":
    Internacional_UNHCR().ejecutar()
