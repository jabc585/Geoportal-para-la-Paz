"""Conector IDEAM: cambio en la superficie cubierta por bosque natural.

Fuente: dataset de archivo (no tabular) `39dh-rc72` en datos.gov.co — ZIP con
un raster Erdas Imagine (.img) por periodo (verificado 2026-08-02: periodo
2021-2022, CRS EPSG:3116, píxel ~30 m, 5 clases). El pipeline:

1. Descarga el ZIP (URL en IDEAM_BOSQUE_URL o resuelta por redirección) y lo
   guarda inmutable en data/raw/ideam/.
2. Calcula estadística zonal por municipio (capa `capa_contexto_territorial`
   tipo 'divipola', sembrada con `python -m etl.common.capas_geo`).
3. Carga superficie (ha) por clase y municipio a `curated.serie_historica`.

Clases del raster: 1 Bosque Estable, 2 Deforestación, 3 Regeneración,
4 No Bosque estable, 5 Sin información (se descarta). El área se deriva del
conteo de píxeles × el tamaño de píxel del propio raster: es el área del
producto IDEAM, no una medición independiente.
"""

from __future__ import annotations

import io
import json
import re
import zipfile
from datetime import date
from pathlib import Path

import pandas as pd
import psycopg
import rasterio
import requests
from rasterstats import zonal_stats

from etl.common.cargar import insertar_serie, upsert_fuente, upsert_indicador
from etl.common.config import settings
from etl.common.lineage import Lineage, hash_registro
from etl.common.pipeline import PipelineETL

RUTA_REPO = Path(__file__).resolve().parents[2]

# vía pública de descarga del dataset 39dh-rc72 (redirige al archivo ZIP real)
URL_DATOS_GOV = "https://www.datos.gov.co/download/39dh-rc72"

CLASES = {
    1: ("ideam_bosque_estable", "Superficie de bosque estable (IDEAM)"),
    2: ("ideam_deforestacion", "Superficie deforestada (IDEAM)"),
    3: ("ideam_regeneracion", "Superficie regenerada (IDEAM)"),
    4: ("ideam_no_bosque", "Superficie sin bosque estable (IDEAM)"),
}

_PATRON_PERIODO = re.compile(r"(\d{4})_(\d{4})")


class IDEAM_Ambiental(PipelineETL):
    pipeline_id = "ideam_ambiental"
    tabla_raw = "ideam_ambiental"

    def __init__(self) -> None:
        super().__init__()
        self._ruta_img: Path | None = None
        self._anio_inicio: int | None = None
        self._anio_fin: int | None = None
        self._municipios: list[tuple[str, str]] = []  # (codigo_divipola, nombre)

    # ── extraer ───────────────────────────────────────────────────────────

    def _url_zip(self) -> str:
        if settings.ideam_bosque_url:
            return settings.ideam_bosque_url
        # Sin variable configurada: resolver la redirección pública.
        resp = requests.get(URL_DATOS_GOV, timeout=60, allow_redirects=False)
        resp.raise_for_status()
        if resp.status_code not in (301, 302, 303, 307, 308):
            raise RuntimeError(f"Redirección inesperada del dataset IDEAM: HTTP {resp.status_code}")
        return resp.headers["Location"]

    def _descargar(self, url: str) -> Path:
        destino = RUTA_REPO / "data" / "raw" / "ideam"
        destino.mkdir(parents=True, exist_ok=True)
        ruta = destino / f"{self.pipeline_id}_{self.lineage.fecha_extraccion:%Y%m%d_%H%M%S}.zip"
        resp = requests.get(url, timeout=900)
        resp.raise_for_status()
        ruta.write_bytes(resp.content)
        return ruta

    def extraer(self) -> tuple[pd.DataFrame, Lineage]:
        self.lineage = Lineage.ahora(
            fuente="IDEAM",
            url_origen=URL_DATOS_GOV,
            fecha_corte_dato=None,
            licencia="Datos crudos IDEAM (cláusulas del dataset: sin validación; no como evidencia jurídica)",
        )
        url = self._url_zip()
        print(f"[ideam] descargando raster ({url})…")
        zip_ruta = self._descargar(url)
        with zipfile.ZipFile(zip_ruta) as z:
            nombre_img = next(n for n in z.namelist() if n.lower().endswith(".img"))
            destino = zip_ruta.parent / nombre_img
            with z.open(nombre_img) as origen, open(destino, "wb") as salida:
                salida.write(origen.read())
        self._ruta_img = destino

        periodo = _PATRON_PERIODO.search(destino.name)
        if not periodo:
            raise ValueError(f"No se identificó el periodo en el nombre del raster: {destino.name}")
        self._anio_inicio, self._anio_fin = (int(g) for g in periodo.groups())

        with rasterio.open(destino) as r:
            metadatos = {
                "archivo": destino.name,
                "periodo": f"{self._anio_inicio}-{self._anio_fin}",
                "crs": str(r.crs),
                "shape": list(r.shape),
                "res": list(r.res),
                "dtype": r.dtypes[0],
                "tamano_mb": round(destino.stat().st_size / 1e6, 1),
            }
        df = pd.DataFrame([metadatos])
        self._municipios = self._cargar_municipios()
        return df, self.lineage

    def _cargar_municipios(self) -> list[tuple[str, str]]:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT codigo_divipola, nombre
                FROM curated.capa_contexto_territorial
                WHERE tipo = 'divipola'
                ORDER BY codigo_divipola
                """
            )
            return cur.fetchall()

    # ── transformar ───────────────────────────────────────────────────────

    def transformar(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self._municipios or self._ruta_img is None:
            print("[ideam] AVISO: sin capa municipal (¿sembrada? python -m etl.common.capas_geo) — nada que cargar.")
            return pd.DataFrame()

        with rasterio.open(self._ruta_img) as r:
            res_x, res_y = r.res
            factor = res_x * res_y / 10_000  # m² → ha por píxel

        filas = []
        for codigo, nombre in self._municipios:
            geo_texto = self._geometria(codigo)
            if geo_texto is None:
                continue
            geo = json.loads(geo_texto) if isinstance(geo_texto, str) else geo_texto
            stats = zonal_stats(
                [geo], self._ruta_img, categorical=True, nodata=None, all_touched=False
            )[0]
            if not stats:
                continue
            for clase, (codigo_ind, nombre_ind) in CLASES.items():
                conteo = stats.get(clase, 0)
                if conteo:
                    filas.append(
                        {
                            "codigo_divipola": codigo,
                            "municipio": nombre,
                            "indicador_codigo": codigo_ind,
                            "indicador_nombre": nombre_ind,
                            "anio_inicio": self._anio_inicio,
                            "anio_fin": self._anio_fin,
                            "valor": conteo * factor,
                            "unidad": "ha",
                        }
                    )
        return pd.DataFrame(filas)

    def _geometria(self, codigo: str):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT ST_AsGeoJSON(ST_Transform(geometria, 3116))
                FROM curated.capa_contexto_territorial
                WHERE tipo = 'divipola' AND codigo_divipola = %s
                """,
                (codigo,),
            )
            fila = cur.fetchone()
        return fila[0] if fila else None

    # ── cargar ────────────────────────────────────────────────────────────

    def cargar_curated(self, df: pd.DataFrame) -> None:
        if df.empty:
            return
        with self.conn:
            fuente_id = upsert_fuente(
                self.conn,
                nombre="IDEAM",
                entidad="Instituto de Hidrología, Meteorología y Estudios Ambientales",
                tipo="nacional",
                descripcion="Cambio en la superficie cubierta por bosque natural (raster por periodo, estadística zonal municipal)",
                url_base="https://www.ideam.gov.co/",
                metodo_acceso="descarga",
                periodicidad="anual",
                formato="raster (Erdas Imagine .img)",
                licencia=self.lineage.licencia,
                ficha_doc="docs/fuentes/ideam.md",
            )
            por_indicador = {
                codigo: upsert_indicador(
                    self.conn,
                    codigo,
                    nombre=nombre,
                    descripcion=f"Superficie por clase de bosque según raster IDEAM (periodo {self._anio_inicio}-{self._anio_fin})",
                    unidad="ha",
                    granularidad_min="municipio",
                    periodicidad="anual",
                )
                for codigo, nombre in [v for v in CLASES.values()]
            }
            a_cargar = df.assign(
                indicador_id=df["indicador_codigo"].map(por_indicador),
                periodo_inicio=df["anio_inicio"].map(lambda a: date(a, 1, 1)),
                periodo_fin=df["anio_fin"].map(lambda a: date(a, 12, 31)),
            )
            insertadas = insertar_serie(
                self.conn,
                a_cargar,
                fuente_id=fuente_id,
                url_origen=self.lineage.url_origen,
                fecha_extraccion=self.lineage.fecha_extraccion,
            )
            print(f"[ideam] filas cargadas a serie_historica: {insertadas}")


if __name__ == "__main__":
    IDEAM_Ambiental().ejecutar()
