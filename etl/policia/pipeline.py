"""Conector de delitos: Policía Nacional (plan2.md Fase B, fuente 5).

Datasets reales en datos.gov.co (verificados en vivo 2026-08-02), por tipo de
delito: hurto `d4fr-sbn2` (44.169 filas, 3 tipos), violencia intrafamiliar
`vuyt-mqpw` (682.558 filas), delitos sexuales `fpe5-yrmw` (392.576 filas,
23 delitos). Cada fila tiene `cantidad` por segmento demográfico; el pipeline
suma `cantidad` por municipio/año (y tipo de delito cuando el dataset lo
tiene). `codigo_dane` viene como DIVIPOLA de 5 dígitos + "000": se recorta.

Homicidios (`POLICIA_HOMICIDIOS_URL`) queda pendiente: el dataset general de
homicidios intencionales no aparece en el catálogo (investigación 2026-08-02) —
es el que necesita `curated.vw_homicidios_reconciliado` (sección 7.5).
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

DELITOS = {
    "hurto": {
        "variable": "POLICIA_HURTO_URL",
        "resource_id": "d4fr-sbn2",
        "col_dim": "tipo_de_hurto",
        "prefijo_indicador": "Hurto (Policía Nacional)",
        "unidad": "delitos",
        "descripcion": "Hurtos por municipio/año y tipo (Policía Nacional)",
    },
    "violencia": {
        "variable": "POLICIA_VIOLENCIA_URL",
        "resource_id": "vuyt-mqpw",
        "col_dim": None,  # sin dimensión en la fuente
        "prefijo_indicador": "Violencia intrafamiliar (Policía Nacional)",
        "unidad": "delitos",
        "descripcion": "Violencia intrafamiliar por municipio/año (Policía Nacional)",
    },
    "sexuales": {
        "variable": "POLICIA_SEXUALES_URL",
        "resource_id": "fpe5-yrmw",
        "col_dim": "delito",
        "prefijo_indicador": "Delitos sexuales (Policía Nacional)",
        "unidad": "delitos",
        "descripcion": "Delitos sexuales por municipio/año y tipo (Policía Nacional)",
    },
}


def _descargar(url: str) -> list[dict]:
    """Descarga paginada de Socrata ($limit/$offset, sin token)."""
    filas: list[dict] = []
    offset = 0
    while True:
        resp = requests.get(
            url, params={"$limit": TAMANO_PAGINA, "$offset": offset}, timeout=300
        )
        resp.raise_for_status()
        batch = resp.json()
        filas.extend(batch)
        if len(batch) < TAMANO_PAGINA:
            return filas
        offset += len(batch)


class Policia_Delitos(PipelineETL):
    pipeline_id = "policia_delitos"
    tabla_raw = "policia_delitos"

    def __init__(self, delito: str = "hurto") -> None:
        super().__init__()
        if delito not in DELITOS:
            raise ValueError(f"Delito Policía desconocido: {delito} (opciones: {', '.join(DELITOS)})")
        self._delito = delito
        self._cfg = DELITOS[delito]
        self.pipeline_id = f"policia_{delito}"
        self.tabla_raw = f"policia_{delito}"

    def extraer(self) -> tuple[pd.DataFrame, Lineage]:
        url = get_source_url(
            self._cfg["variable"],
            ayuda=f"Dataset Socrata de {self._cfg['prefijo_indicador'].lower()} (resource {self._cfg['resource_id']})",
        )
        df = pd.DataFrame(_descargar(url))
        lineage = Lineage.ahora(
            fuente="Policía Nacional",
            url_origen=url,
            fecha_corte_dato=None,
            licencia="Policía Nacional de Colombia - verificar en ficha (sección 3, punto 5)",
        )
        return df, lineage

    def transformar(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        anio = pd.to_datetime(df["fecha_hecho"], dayfirst=True, errors="coerce").dt.year
        df = df.assign(
            # codigo_dane llega como DIVIPOLA de 5 dígitos + "000" (p. ej. 44420000)
            codigo_divipola=df["codigo_dane"].astype(str).str[:5],
            anio=pd.to_numeric(anio, errors="coerce"),
            valor=pd.to_numeric(df["cantidad"], errors="coerce"),
        )
        df = df[df["anio"].between(ANIO_MINIMO, ANIO_MAXIMO)].dropna(subset=["valor"])

        if self._cfg["col_dim"]:
            df = df.assign(dimension=df[self._cfg["col_dim"]].fillna("Sin información").astype(str).str.strip())
            agrupado = (
                df.groupby(["codigo_divipola", "anio", "dimension"], as_index=False)["valor"].sum()
            )
        else:
            agrupado = df.groupby(["codigo_divipola", "anio"], as_index=False)["valor"].sum()
            agrupado["dimension"] = "violencia_intrafamiliar"

        periodo = agrupado["anio"].apply(periodo_anual)
        agrupado["periodo_inicio"] = periodo.apply(lambda p: p[0])
        agrupado["periodo_fin"] = periodo.apply(lambda p: p[1])
        return agrupado.drop(columns=["anio"])

    def cargar_curated(self, df: pd.DataFrame) -> None:
        if df.empty:
            return
        with self.conn:
            fuente_id = upsert_fuente(
                self.conn,
                nombre="Policía Nacional",
                entidad="Policía Nacional de Colombia",
                tipo="nacional",
                descripcion="Delitos por municipio: hurto, violencia intrafamiliar, delitos sexuales (sección 5)",
                url_base="https://www.policia.gov.co/",
                metodo_acceso="api",
                periodicidad="mensual",
                formato="JSON",
                licencia=self.lineage.licencia,
                ficha_doc="docs/fuentes/policia.md",
            )
            insertadas = 0
            for dimension, grupo in df.groupby("dimension"):
                indicador_id = upsert_indicador(
                    self.conn,
                    codigo=f"policia_{self._delito}_{slugificar(dimension)}",
                    nombre=f"{self._cfg['prefijo_indicador']}: {dimension}",
                    descripcion=self._cfg["descripcion"],
                    unidad=self._cfg["unidad"],
                    granularidad_min="municipio",
                    periodicidad="mensual",
                    metodologia_doc="docs/metodologia/indicadores.md",
                )
                grupo = grupo.assign(indicador_id=indicador_id)
                grupo = validar(grupo, EsquemaSerieNormalizada)[0]
                insertadas += insertar_serie(
                    self.conn, grupo, fuente_id, self.lineage.url_origen, self.lineage.fecha_extraccion
                )
            print(f"[policia/{self._delito}] filas cargadas a serie_historica: {insertadas}")


if __name__ == "__main__":
    import sys

    delito = sys.argv[1] if len(sys.argv) > 1 else "hurto"
    Policia_Delitos(delito).ejecutar()
