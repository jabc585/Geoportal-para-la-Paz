"""Conector de estadísticas judiciales: Fiscalía V3 (plan2.md Fase B, fuente 3).

Datasets reales en datos.gov.co (verificados en vivo 2026-08-02):

- `dbdv-iihs` Procesos V3: 23.212.036 filas (fila = proceso).
- `hr73-zqjf` Víctimas V3: 17.534.229 filas (fila = víctima con id anonimizado).

**Diseño por volumen**: descargar decenas de millones de filas es inviable para
un ETL programado y para la capa raw; se usa la agregación server-side de SoQL
(`$select` con `count(*)` + `$group`), que devuelve conteos por
municipio/año/título del delito — además, publicar solo agregados es el
principio de privacidad del proyecto (sección 3.1: nunca la fila individual).
Nota de honestidad: en víctimas, el recuento es de *registros* (una víctima con
varios procesos cuenta varias veces; no es deduplicable server-side a esa escala).

Cada corrida escanea la tabla completa en la API (~4-5 minutos por dataset).
"""

from __future__ import annotations

import pandas as pd
import requests

from etl.common.cargar import insertar_serie, periodo_anual, slugificar, upsert_fuente, upsert_indicador
from etl.common.config import get_source_url
from etl.common.lineage import Lineage
from etl.common.pipeline import PipelineETL
from etl.common.validation import EsquemaSerieNormalizada, validar

TAMANO_PAGINA = 50000
ANIO_MINIMO = 1980
ANIO_MAXIMO = 2027

DATASETS = {
    "procesos": {
        "variable": "FISCALIA_PROCESOS_URL",
        "resource_id": "dbdv-iihs",
        "col_anio": "a_o_hecho",
        "col_codigo": "cod_dane_hecho",
        "col_dim": "titulo_delito",
        "prefijo_indicador": "Procesos judiciales (Fiscalía)",
        "unidad": "procesos",
        "descripcion": "Procesos judiciales por municipio/año y título del delito (Fiscalía V3, agregado server-side)",
    },
    "victimas": {
        "variable": "FISCALIA_VICTIMAS_URL",
        "resource_id": "hr73-zqjf",
        "col_anio": "a_o_hecho_origen",
        "col_codigo": "cod_dane_hecho_origen",
        "col_dim": "titulo_delito",
        "prefijo_indicador": "Registros de víctimas en procesos judiciales (Fiscalía)",
        "unidad": "registros",
        "descripcion": "Registros de víctimas en procesos judiciales por municipio/año y título del delito (Fiscalía V3, agregado server-side; sin dedupe por id anonimizado)",
    },
}


def _agregar_soql(url: str, select: str, group: str) -> list[dict]:
    """Consulta agregada de SoQL ($select/$group) con paginación por offset."""
    filas: list[dict] = []
    offset = 0
    while True:
        resp = requests.get(
            url,
            params={
                "$select": select,
                "$group": group,
                "$limit": TAMANO_PAGINA,
                "$offset": offset,
            },
            timeout=600,
        )
        resp.raise_for_status()
        batch = resp.json()
        filas.extend(batch)
        if len(batch) < TAMANO_PAGINA:
            return filas
        offset += len(batch)


class Fiscalia_Estadisticas(PipelineETL):
    pipeline_id = "fiscalia_estadisticas"
    tabla_raw = "fiscalia_estadisticas"

    def __init__(self, dataset: str = "procesos") -> None:
        super().__init__()
        if dataset not in DATASETS:
            raise ValueError(f"Dataset Fiscalía desconocido: {dataset} (opciones: {', '.join(DATASETS)})")
        self._dataset = dataset
        self._cfg = DATASETS[dataset]
        self.pipeline_id = f"fiscalia_{dataset}"
        self.tabla_raw = f"fiscalia_{dataset}"

    def extraer(self) -> tuple[pd.DataFrame, Lineage]:
        url = get_source_url(
            self._cfg["variable"],
            ayuda=f"Dataset Socrata V3 (resource {self._cfg['resource_id']})",
        )
        select = (
            f"{self._cfg['col_codigo']} as codigo, "
            f"{self._cfg['col_anio']} as anio, "
            f"{self._cfg['col_dim']} as dimension, count(*) as n"
        )
        df = pd.DataFrame(_agregar_soql(url, select, "codigo, anio, dimension"))
        lineage = Lineage.ahora(
            fuente="Fiscalía",
            url_origen=url,
            fecha_corte_dato=None,
            licencia="Fiscalía General de la Nación - verificar en ficha (sección 3, punto 5)",
        )
        return df, lineage

    def transformar(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        anio = pd.to_numeric(df["anio"], errors="coerce")
        df = df.assign(
            codigo_divipola=df["codigo"].astype(str).str.zfill(5),
            anio=anio,
            dimension=df["dimension"].fillna("Sin información").astype(str).str.strip(),
            valor=pd.to_numeric(df["n"], errors="coerce"),
        )
        df = df[df["anio"].between(ANIO_MINIMO, ANIO_MAXIMO)].dropna(subset=["valor"])

        periodo = df["anio"].apply(periodo_anual)
        df["periodo_inicio"] = periodo.apply(lambda p: p[0])
        df["periodo_fin"] = periodo.apply(lambda p: p[1])
        return df.drop(columns=["anio", "codigo", "n"])

    def cargar_curated(self, df: pd.DataFrame) -> None:
        if df.empty:
            return
        with self.conn:
            fuente_id = upsert_fuente(
                self.conn,
                nombre="Fiscalía",
                entidad="Fiscalía General de la Nación",
                tipo="nacional",
                descripcion="Estadísticas judiciales: procesos y víctimas (datasets V3, sección 5)",
                url_base="https://www.fiscalia.gov.co/",
                metodo_acceso="api",
                periodicidad="trimestral",
                formato="JSON",
                licencia=self.lineage.licencia,
                ficha_doc="docs/fuentes/fiscalia.md",
            )
            insertadas = 0
            for dimension, grupo in df.groupby("dimension"):
                indicador_id = upsert_indicador(
                    self.conn,
                    codigo=f"fiscalia_{self._dataset}_{slugificar(dimension)}",
                    nombre=f"{self._cfg['prefijo_indicador']}: {dimension}",
                    descripcion=self._cfg["descripcion"],
                    unidad=self._cfg["unidad"],
                    granularidad_min="municipio",
                    periodicidad="trimestral",
                    metodologia_doc="docs/metodologia/indicadores.md",
                )
                grupo = grupo.assign(indicador_id=indicador_id)
                grupo = validar(grupo, EsquemaSerieNormalizada)[0]
                insertadas += insertar_serie(
                    self.conn, grupo, fuente_id, self.lineage.url_origen, self.lineage.fecha_extraccion
                )
            print(f"[fiscalia/{self._dataset}] filas cargadas a serie_historica: {insertadas}")


if __name__ == "__main__":
    import sys

    dataset = sys.argv[1] if len(sys.argv) > 1 else "procesos"
    Fiscalia_Estadisticas(dataset).ejecutar()
