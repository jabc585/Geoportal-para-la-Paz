"""Conector piloto Unidad de Víctimas (Datos Paz) - fuente de la fase 2 del plan.

Acceso: API de Datos Paz (sección 5). Los hechos victimizantes se publican
agregados (municipio/periodo/tipo de hecho), nunca a nivel individual
(sección 3, punto 2: principio de no daño). Antes de habilitar este dataset
en la API se ejecuta el checklist de privacidad (sección 3.1) — evidencia en
docs/metodologia/checklist_victimas.md.
"""

from __future__ import annotations

import os

import pandas as pd

from etl.common.cargar import insertar_serie, periodo_anual, slugificar, upsert_fuente, upsert_indicador
from etl.common.lineage import Lineage
from etl.common.pipeline import PipelineETL
from etl.common.validation import EsquemaSerieNormalizada, validar

ALIASES = {
    "codigo": ["codigo_municipio", "cod_municipio", "cod_divipola", "codigomunicipio", "codigo_mun"],
    "anio": ["anio", "ano", "año", "year", "periodo"],
    "hecho": ["hecho", "tipo_hecho", "hecho_victimizante", "tipo", "modalidad"],
    "valor": ["casos", "victimas", "personas", "numero_casos", "cantidad"],
}


def _columna(df: pd.DataFrame, aliases: list[str], etiqueta: str) -> str:
    for alias in aliases:
        if alias in df.columns:
            return alias
    raise ValueError(f"No se encontró columna para {etiqueta} (buscadas: {aliases}). Revisar ficha docs/fuentes/victimas.md")


class Victimas_Hechos(PipelineETL):
    pipeline_id = "victimas_hechos"
    tabla_raw = "victimas_hechos"

    def extraer(self) -> tuple[pd.DataFrame, Lineage]:
        # Sin default hardcodeado: si el dominio cambiara de dueño, un valor
        # por defecto podría consumir contenido no controlado (auditoría,
        # sección 3, punto 3). La URL real de Datos Paz se configura explícitamente.
        url_base = os.getenv("VICTIMAS_URL", "")
        if not url_base:
            raise ValueError("Variable VICTIMAS_URL no configurada (ver docs/fuentes/victimas.md)")
        url = f"{url_base.rstrip('/')}/hechos_victimizantes"
        import requests

        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        df = pd.DataFrame(resp.json())
        lineage = Lineage.ahora(
            fuente="Unidad para las Víctimas",
            url_origen=url,
            fecha_corte_dato=None,
            licencia="Verificar en ficha (sección 3, punto 5)",
        )
        return df, lineage

    def transformar(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        df = df.rename(columns={c: c.lower() for c in df.columns})
        col_codigo = _columna(df, ALIASES["codigo"], "código DIVIPOLA")
        col_anio = _columna(df, ALIASES["anio"], "año")
        col_hecho = _columna(df, ALIASES["hecho"], "tipo de hecho")
        col_valor = _columna(df, ALIASES["valor"], "casos")

        agregado = (
            df.assign(
                codigo_divipola=df[col_codigo].astype(str).str.zfill(5),
                anio=pd.to_numeric(df[col_anio], errors="coerce"),
                hecho=df[col_hecho].astype(str).str.strip(),
                valor=pd.to_numeric(df[col_valor], errors="coerce"),
            )
            .dropna(subset=["anio", "valor"])
            .groupby(["codigo_divipola", "anio", "hecho"], as_index=False)["valor"]
            .sum()
        )

        periodo = agregado["anio"].apply(periodo_anual)
        agregado["periodo_inicio"] = periodo.apply(lambda p: p[0])
        agregado["periodo_fin"] = periodo.apply(lambda p: p[1])
        return agregado.drop(columns=["anio"])

    def cargar_curated(self, df: pd.DataFrame) -> None:
        if df.empty:
            return
        with self.conn:
            fuente_id = upsert_fuente(
                self.conn,
                nombre="Unidad para las Víctimas",
                entidad="Unidad Administrativa Especial para la Atención y Reparación a las Víctimas",
                tipo="nacional",
                descripcion="Víctimas, desplazamiento, retornos, reparación (sección 5)",
                url_base="https://datospaz.unidadvictimas.gov.co/",
                metodo_acceso="api",
                periodicidad="trimestral",
                formato="JSON",
                licencia=self.lineage.licencia,
                ficha_doc="docs/fuentes/victimas.md",
            )
            insertadas = 0
            for hecho, grupo in df.groupby("hecho"):
                codigo_indicador = f"victimas_{slugificar(hecho)}"
                indicador_id = upsert_indicador(
                    self.conn,
                    codigo=codigo_indicador,
                    nombre=f"Hechos victimizantes: {hecho}",
                    descripcion=f"Hechos victimizantes de tipo '{hecho}' agregados por municipio/año",
                    unidad="casos",
                    granularidad_min="municipio",
                    periodicidad="trimestral",
                    metodologia_doc="docs/metodologia/indicadores.md",
                )
                grupo = grupo.assign(indicador_id=indicador_id)
                grupo = validar(grupo, EsquemaSerieNormalizada)[0]
                insertadas += insertar_serie(
                    self.conn, grupo, fuente_id, self.lineage.url_origen, self.lineage.fecha_extraccion
                )
            print(f"[victimas] filas cargadas a serie_historica: {insertadas}")


if __name__ == "__main__":
    Victimas_Hechos().ejecutar()
