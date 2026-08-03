"""Conector piloto ART/PDET - fuente de la fase 2 del plan.

Acceso: datos abiertos de la Agencia de Renovación del Territorio (sección 5).
El endpoint de proyectos PDET se configura con PDET_URL. Carga proyectos en
curated.pdet_proyectos y la inversión agregada en serie_historica (indicador
pdet_inversion), ambas con linaje completo.
"""

from __future__ import annotations

import os

import pandas as pd

from etl.common.cargar import insertar_serie, periodo_anual, resolver_territorio, upsert_fuente, upsert_indicador
from etl.common.db import transaccion
from etl.common.descargas import descargar_socrata_paginado
from etl.common.lineage import Lineage, hash_registro
from etl.common.pipeline import PipelineETL
import pandera as pa

from etl.common.validation import (
    EsquemaSerieNormalizada,
    encontrar_columna,
    encontrar_columna_opcional,
    validar,
)

EsquemaProyectoPDET = pa.DataFrameSchema(
    columns={
        "codigo_divipola": pa.Column(str),
        "nombre": pa.Column(str),
        "estado": pa.Column(str, nullable=True),
        "avance_pct": pa.Column(float, nullable=True),
        "valor_inversion": pa.Column(float, nullable=True),
        "anio": pa.Column(float, nullable=True),
    }
)

ALIASES = {
    "codigo": [
        "codigo_municipio", "cod_municipio", "cod_divipola", "codigomunicipio",
        "codigo_mun", "codigodane", "dane_municipio",
    ],
    "nombre": [
        "nombre_proyecto", "proyecto", "nombre", "titulo_proyecto", "t_tulo_iniciativa", "titulo",
    ],
    "estado": ["estado", "estado_proyecto", "fase", "estado_del_proceso"],
    "avance": ["avance", "avance_pct", "porcentaje_avance", "avance_fisico"],
    "inversion": ["valor_inversion", "valor", "inversion", "valor_total", "presupuesto", "valor_contrato"],
    "anio": ["anio", "vigencia", "ano", "año", "year"],
}


class ART_PDET(PipelineETL):
    pipeline_id = "art_pdet"
    tabla_raw = "art_pdet"

    def extraer(self) -> tuple[pd.DataFrame, Lineage]:
        url = os.getenv("PDET_URL", "")
        if not url:
            raise ValueError("Variable PDET_URL no configurada (ver docs/fuentes/art.md)")

        # Paginación Socrata: sin $limit la API devuelve solo 1000 filas
        # por defecto. Usamos el mismo helper que policía y CNMH.
        # Nota: algunos datasets de la ART no son Socrata (JSON plano de
        # una sola página); en ese caso descargar_socrata_paginado
        # devuelve todas las filas de la primera (y única) página.
        df = pd.DataFrame(descargar_socrata_paginado(url, timeout=60))
        lineage = Lineage.ahora(
            fuente="Agencia de Renovación del Territorio",
            url_origen=url,
            fecha_corte_dato=None,
            licencia="Verificar en ficha (sección 3, punto 5)",
        )
        return df, lineage

    def transformar(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        df = df.rename(columns={c: c.lower() for c in df.columns})
        col_codigo = encontrar_columna(df, ALIASES["codigo"], "código DIVIPOLA", "docs/fuentes/art.md")
        col_nombre = encontrar_columna(df, ALIASES["nombre"], "nombre del proyecto", "docs/fuentes/art.md")
        col_estado = encontrar_columna_opcional(df, ALIASES["estado"])
        col_avance = encontrar_columna_opcional(df, ALIASES["avance"])
        col_inversion = encontrar_columna_opcional(df, ALIASES["inversion"])
        col_anio = encontrar_columna_opcional(df, ALIASES["anio"])

        # Las columnas financieras y el año son opcionales: datasets reales de
        # la ART (p. ej. Iniciativas PDET) no los reportan (auditoría
        # 2026-08-02); solo código y nombre son obligatorios.
        nulos = pd.Series([None] * len(df), index=df.index)
        return pd.DataFrame(
            {
                "codigo_divipola": df[col_codigo].astype(str).str.zfill(5),
                "nombre": df[col_nombre].astype(str),
                "estado": df[col_estado].astype(str) if col_estado else nulos,
                "avance_pct": pd.to_numeric(df[col_avance], errors="coerce") if col_avance else nulos,
                "valor_inversion": pd.to_numeric(df[col_inversion], errors="coerce") if col_inversion else nulos,
                "anio": pd.to_numeric(df[col_anio], errors="coerce") if col_anio else nulos,
            }
        ).replace({float("nan"): None, "nan": None})

    def cargar_curated(self, df: pd.DataFrame) -> None:
        if df.empty:
            return
        with transaccion(self.conn):
            fuente_id = upsert_fuente(
                self.conn,
                nombre="Agencia de Renovación del Territorio",
                entidad="ART",
                tipo="nacional",
                descripcion="PDET, obras, proyectos (sección 5)",
                url_base="https://www.renovacionterritorio.gov.co/",
                metodo_acceso="descarga",
                periodicidad="mensual",
                formato="JSON/CSV",
                licencia=self.lineage.licencia,
                ficha_doc="docs/fuentes/art.md",
            )
            insertadas = self._cargar_proyectos(df, fuente_id)
            insertadas += self._cargar_inversion(df, fuente_id)
            print(f"[pdet] filas cargadas: {insertadas} (proyectos + serie inversión)")

    def _cargar_proyectos(self, df: pd.DataFrame, fuente_id: int) -> int:
        df = validar(df, EsquemaProyectoPDET)[0]
        insertadas = 0
        sin_territorio = 0
        filas = []
        for fila in df.to_dict("records"):
            if not fila["nombre"]:
                continue
            municipio_id, departamento_id = resolver_territorio(self.conn, fila["codigo_divipola"])
            if municipio_id is None and departamento_id is None:
                sin_territorio += 1
                continue
            anio = None if fila["anio"] is None else int(fila["anio"])
            avance = None if fila["avance_pct"] is None else float(fila["avance_pct"])
            inversion = None if fila["valor_inversion"] is None else float(fila["valor_inversion"])
            filas.append(
                (
                    municipio_id,
                    departamento_id,
                    fila["nombre"],
                    fila["estado"],
                    avance,
                    inversion,
                    anio,
                    fuente_id,
                    self.lineage.url_origen,
                    self.lineage.fecha_extraccion,
                    self.lineage.fecha_corte_dato,
                    hash_registro(fila),
                )
            )
        if filas:
            with self.conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO curated.pdet_proyectos
                        (municipio_id, departamento_id, nombre, estado, avance_pct,
                         valor_inversion, anio, fuente_id, url_origen, fecha_extraccion,
                         fecha_corte_dato, hash_registro)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (hash_registro) DO NOTHING
                    """,
                    filas,
                )
                insertadas = cur.rowcount
        if sin_territorio:
            print(
                f"[pdet] AVISO: {sin_territorio} proyectos descartados por territorio no resuelto "
                f"(¿catálogo DIVIPOLA sembrado? python -m etl.common.divipola)"
            )
        return insertadas

    def _cargar_inversion(self, df: pd.DataFrame, fuente_id: int) -> int:
        con_datos = df.dropna(subset=["valor_inversion", "anio"])
        if con_datos.empty:
            print("[pdet] sin datos de inversión con año en la fuente (no se agrega serie)")
            return 0
        indicador_id = upsert_indicador(
            self.conn,
            codigo="pdet_inversion",
            nombre="Inversión PDET",
            descripcion="Inversión en proyectos PDET por municipio/año",
            unidad="COP",
            granularidad_min="municipio",
            periodicidad="mensual",
            metodologia_doc="docs/metodologia/indicadores.md",
        )
        agregado = (
            con_datos.groupby(["codigo_divipola", "anio"], as_index=False)["valor_inversion"].sum()
        )
        periodo = agregado["anio"].apply(periodo_anual)
        serie = pd.DataFrame(
            {
                "codigo_divipola": agregado["codigo_divipola"],
                "periodo_inicio": periodo.apply(lambda p: p[0]),
                "periodo_fin": periodo.apply(lambda p: p[1]),
                "valor": agregado["valor_inversion"],
                "indicador_id": indicador_id,
            }
        )
        serie = validar(serie, EsquemaSerieNormalizada)[0]
        return insertar_serie(self.conn, serie, fuente_id, self.lineage.url_origen, self.lineage.fecha_extraccion)


if __name__ == "__main__":
    ART_PDET().ejecutar()
