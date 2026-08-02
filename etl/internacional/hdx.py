"""Conector internacional: HDX HAPI (plan2.md Fase B, fuente 4).

Dataset dedicado a Colombia de Humanitarian Data Exchange (hdx-hapi-col,
verificado en vivo 2026-08-02). Se carga el recurso *Conflict Events*:
346.698 filas mensuales por municipio (admin_level=2, 2018–2026), con tipos
de evento y víctimas. Los códigos admin2 de HAPI ("CO76890") son DIVIPOLA con
prefijo "CO": se descarta el prefijo y se resuelve contra el catálogo
(curated.municipio). Agrega por municipio/año: eventos y fatalidades.
"""

from __future__ import annotations

import io

import pandas as pd
import requests

from etl.common.cargar import insertar_serie, periodo_anual, upsert_fuente, upsert_indicador
from etl.common.db import transaccion
from etl.common.config import get_source_url
from etl.common.descargas import descargar_a_buffer
from etl.common.lineage import Lineage
from etl.common.pipeline import PipelineETL
from etl.common.validation import EsquemaSerieNormalizada, validar

ANIO_MINIMO = 1980
ANIO_MAXIMO = 2027

INDICADORES = [
    {
        "codigo": "hdx_conflicto_eventos",
        "nombre": "Eventos de conflicto (HDX HAPI)",
        "unidad": "eventos",
        "columna": "events",
    },
    {
        "codigo": "hdx_conflicto_fatalidades",
        "nombre": "Fatalidades en eventos de conflicto (HDX HAPI)",
        "unidad": "fatalidades",
        "columna": "fatalities",
    },
]


def _url_firmada(url_base: str, resource_id: str) -> str:
    """Resuelve la URL de descarga (S3 firmada) vía resource_show de CKAN."""
    resp = requests.get(
        f"{url_base.rstrip('/')}/action/resource_show", params={"id": resource_id}, timeout=60
    )
    resp.raise_for_status()
    return resp.json()["result"]["url"]


class Internacional_HDX(PipelineETL):
    pipeline_id = "internacional_hdx"
    tabla_raw = "internacional_hdx"

    def _url_recurso(self) -> str:
        return _url_firmada(
            get_source_url("HDX_BASE_URL", ayuda="API CKAN de HDX (default: https://data.humdata.org/api/3)"),
            get_source_url(
                "HDX_CONFLICTO_RESOURCE_ID",
                ayuda="Resource id de 'Conflict Events for Colombia' (hdx-hapi-col)",
            ),
        )

    def extraer(self) -> tuple[pd.DataFrame, Lineage]:
        url = self._url_recurso()
        # Límite de tamaño de descarga (auditoría 2026-08-02): el CSV de HDX
        # trae ~346K filas; un archivo anómalo no debe agotar la memoria.
        df = pd.read_csv(descargar_a_buffer(url, timeout=600))
        columnas = [
            "admin2_code",
            "admin2_name",
            "event_type",
            "events",
            "fatalities",
            "reference_period_start",
            "reference_period_end",
        ]
        df = df[[c for c in columnas if c in df.columns]]
        lineage = Lineage.ahora(
            fuente="HDX",
            url_origen=url,
            fecha_corte_dato=None,
            licencia="HDX - verificar por dataset (sección 3, punto 5)",
        )
        return df, lineage

    def transformar(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        df = df.assign(
            codigo_divipola=df["admin2_code"].astype(str).str.replace(r"^CO", "", regex=True).str.zfill(5),
            anio=pd.to_numeric(df["reference_period_start"].astype(str).str[:4], errors="coerce"),
        )
        df = df[df["anio"].between(ANIO_MINIMO, ANIO_MAXIMO)]

        piezas = []
        for config in INDICADORES:
            agrupado = (
                df.groupby(["codigo_divipola", "anio"], as_index=False)[config["columna"]]
                .sum()
                .rename(columns={config["columna"]: "valor"})
            )
            periodo = agrupado["anio"].apply(periodo_anual)
            agrupado["periodo_inicio"] = periodo.apply(lambda p: p[0])
            agrupado["periodo_fin"] = periodo.apply(lambda p: p[1])
            agrupado["indicador"] = config["codigo"]
            piezas.append(agrupado.drop(columns=["anio"]))
        return pd.concat(piezas, ignore_index=True)

    def cargar_curated(self, df: pd.DataFrame) -> None:
        if df.empty:
            return
        with transaccion(self.conn):
            fuente_id = upsert_fuente(
                self.conn,
                nombre="HDX",
                entidad="Humanitarian Data Exchange (OCHA)",
                tipo="internacional",
                descripcion="Datos humanitarios de Colombia: eventos de conflicto (hdx-hapi-col)",
                url_base="https://data.humdata.org/",
                metodo_acceso="api",
                periodicidad="mensual",
                formato="CSV",
                licencia=self.lineage.licencia,
                ficha_doc="docs/fuentes/hdx.md",
            )
            insertadas = 0
            for config in INDICADORES:
                grupo = df[df["indicador"] == config["codigo"]]
                indicador_id = upsert_indicador(
                    self.conn,
                    codigo=config["codigo"],
                    nombre=config["nombre"],
                    descripcion=(
                        "Eventos de conflicto (ACLED vía HDX HAPI) agregados por municipio/año "
                        f"({config['unidad']} del recurso Conflict Events de hdx-hapi-col)"
                    ),
                    unidad=config["unidad"],
                    granularidad_min="municipio",
                    periodicidad="mensual",
                    metodologia_doc="docs/metodologia/indicadores.md",
                )
                grupo = grupo.assign(indicador_id=indicador_id)
                grupo = validar(grupo, EsquemaSerieNormalizada)[0]
                insertadas += insertar_serie(
                    self.conn, grupo, fuente_id, self.lineage.url_origen, self.lineage.fecha_extraccion
                )
            print(f"[hdx] filas cargadas a serie_historica: {insertadas}")


if __name__ == "__main__":
    Internacional_HDX().ejecutar()
