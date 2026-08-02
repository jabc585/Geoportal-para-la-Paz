"""Conector de memoria histórica: CNMH SIEVCAC (plan2.md Fase B, fuente 2).

Datasets reales de datos.gov.co (Sistema SIEVCAC del Centro Nacional de Memoria
Histórica), uno por tipo de hecho — verificado en vivo 2026-08-02. Dos shapes:

- *casos* (atentados, reclutamiento): cada fila es un caso (id_caso único).
- *víctimas* (minas, desaparición, bienes, acciones): cada fila es una persona
  (id_persona); se cuentan personas únicas por municipio/año y **nunca** se
  carga la fila individual a curated (checklist de privacidad, sección 3.1).

El dato individual queda solo en raw (capa interna, inmutable, con acceso
controlado); a curated/API solo suben conteos agregados por municipio/año.
"""

from __future__ import annotations

import pandas as pd

from etl.common.cargar import insertar_serie, periodo_anual, upsert_fuente, upsert_indicador
from etl.common.db import transaccion
from etl.common.descargas import descargar_socrata_paginado
from etl.common.config import get_source_url
from etl.common.lineage import Lineage
from etl.common.pipeline import PipelineETL
from etl.common.validation import EsquemaSerieNormalizada, validar

TAMANO_PAGINA = 50000
ANIO_MINIMO = 1980
ANIO_MAXIMO = 2027

# tipo: "casos" (fila = caso) o "victimas" (fila = persona, se agrega)
HECHOS = {
    "minas": {
        "variable": "CNMH_MINAS_URL",
        "resource_id": "52eu-ic7d",
        "tipo": "victimas",
        "nombre": "Minas antipersonal",
        "indicador": "Víctimas de minas antipersonal (CNMH)",
        "codigo_indicador": "cnmh_minas_victimas",
        "unidad": "víctimas",
    },
    "atentados": {
        "variable": "CNMH_ATENTADOS_URL",
        "resource_id": "yfd7-8c9d",
        "tipo": "casos",
        "nombre": "Atentados terroristas",
        "indicador": "Casos de atentados terroristas (CNMH)",
        "codigo_indicador": "cnmh_atentados_casos",
        "unidad": "casos",
    },
    "desaparicion": {
        "variable": "CNMH_DESAPARICION_URL",
        "resource_id": "c59y-p4sz",
        "tipo": "victimas",
        "nombre": "Desaparición forzada",
        "indicador": "Víctimas de desaparición forzada (CNMH)",
        "codigo_indicador": "cnmh_desaparicion_victimas",
        "unidad": "víctimas",
    },
    "bienes": {
        "variable": "CNMH_BIENES_URL",
        "resource_id": "a2ga-ur2i",
        "tipo": "victimas",
        "nombre": "Daño a bienes civiles",
        "indicador": "Víctimas de daño a bienes civiles (CNMH)",
        "codigo_indicador": "cnmh_bienes_victimas",
        "unidad": "víctimas",
    },
    "reclutamiento": {
        "variable": "CNMH_RECLUTAMIENTO_URL",
        "resource_id": "hzd2-7ea7",
        "tipo": "casos",
        "nombre": "Reclutamiento de NNA",
        "indicador": "Casos de reclutamiento de NNA (CNMH)",
        "codigo_indicador": "cnmh_reclutamiento_casos",
        "unidad": "casos",
    },
    "acciones": {
        "variable": "CNMH_ACCIONES_URL",
        "resource_id": "chb6-bfmq",
        "tipo": "victimas",
        "nombre": "Acciones bélicas",
        "indicador": "Víctimas de acciones bélicas (CNMH)",
        "codigo_indicador": "cnmh_acciones_victimas",
        "unidad": "víctimas",
    },
}


class CNMH_Memoria(PipelineETL):
    pipeline_id = "cnmh_memoria"
    tabla_raw = "cnmh_memoria"

    def __init__(self, hecho: str) -> None:
        super().__init__()
        if hecho not in HECHOS:
            raise ValueError(f"Hecho CNMH desconocido: {hecho} (opciones: {', '.join(HECHOS)})")
        self._hecho = hecho
        self._cfg = HECHOS[hecho]
        # Un pipeline_id y tabla_raw por tipo de hecho (data_quality_metrics)
        self.pipeline_id = f"cnmh_{hecho}"
        self.tabla_raw = f"cnmh_{hecho}"

    def extraer(self) -> tuple[pd.DataFrame, Lineage]:
        url = get_source_url(
            self._cfg["variable"],
            ayuda=f"Dataset SIEVCAC de {self._cfg['nombre'].lower()} (datos.gov.co, resource {self._cfg['resource_id']})",
        )
        df = pd.DataFrame(descargar_socrata_paginado(url, tamano_pagina=TAMANO_PAGINA, timeout=120))
        lineage = Lineage.ahora(
            fuente="CNMH",
            url_origen=url,
            fecha_corte_dato=None,
            licencia="CNMH - verificar en ficha (sección 3, punto 5)",
        )
        return df, lineage

    def transformar(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        anio = pd.to_numeric(df["a_o"], errors="coerce")
        df = df.assign(
            codigo_divipola=df["c_digo_dane_de_municipio"].astype(str).str.zfill(5),
            anio=anio,
        )
        # a_o="0" y filas sin año o con año fuera de rango: no son datos
        df = df[df["anio"].between(ANIO_MINIMO, ANIO_MAXIMO)]

        if self._cfg["tipo"] == "casos":
            agregado = (
                df.groupby(["codigo_divipola", "anio"], as_index=False)
                .size()
                .rename(columns={"size": "valor"})
            )
        else:
            # Víctimas: personas únicas por municipio/año — la fila individual
            # (con id_persona) nunca sale de raw (checklist de privacidad).
            personas = df.drop_duplicates(subset=["codigo_divipola", "anio", "id_persona"])
            agregado = (
                personas.groupby(["codigo_divipola", "anio"], as_index=False)
                .size()
                .rename(columns={"size": "valor"})
            )

        periodo = agregado["anio"].apply(periodo_anual)
        agregado["periodo_inicio"] = periodo.apply(lambda p: p[0])
        agregado["periodo_fin"] = periodo.apply(lambda p: p[1])
        return agregado.drop(columns=["anio"])

    def cargar_curated(self, df: pd.DataFrame) -> None:
        if df.empty:
            return
        with transaccion(self.conn):
            fuente_id = upsert_fuente(
                self.conn,
                nombre="CNMH",
                entidad="Centro Nacional de Memoria Histórica",
                tipo="nacional",
                descripcion="Memoria histórica del conflicto armado: minas, atentados, desaparición, reclutamiento, bienes, acciones (SIEVCAC)",
                url_base="https://centrodememoriahistorica.gov.co/",
                metodo_acceso="descarga",
                periodicidad="anual",
                formato="JSON",
                licencia=self.lineage.licencia,
                ficha_doc="docs/fuentes/cnmh.md",
            )
            indicador_id = upsert_indicador(
                self.conn,
                codigo=self._cfg["codigo_indicador"],
                nombre=self._cfg["indicador"],
                descripcion=(
                    f"{self._cfg['indicador']}: casos/víctimas agregados por municipio/año "
                    f"desde SIEVCAC (dataset {self._cfg['resource_id']})"
                ),
                unidad=self._cfg["unidad"],
                granularidad_min="municipio",
                periodicidad="anual",
                metodologia_doc="docs/metodologia/indicadores.md",
            )
            grupo = df.assign(indicador_id=indicador_id)
            grupo = validar(grupo, EsquemaSerieNormalizada)[0]
            insertadas = insertar_serie(
                self.conn, grupo, fuente_id, self.lineage.url_origen, self.lineage.fecha_extraccion
            )
            print(f"[cnmh/{self._hecho}] filas cargadas a serie_historica: {insertadas}")


if __name__ == "__main__":
    import sys

    hecho = sys.argv[1] if len(sys.argv) > 1 else "minas"
    CNMH_Memoria(hecho).ejecutar()
