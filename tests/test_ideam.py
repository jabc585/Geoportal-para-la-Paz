"""Pruebas del conector IDEAM (raster de deforestación, plan2.md Fase C).

Usan un raster sintético (CRS EPSG:3116, píxel 100 m = 1 ha) y geometrías
cuadradas alineadas a los píxeles, replicando el shape real verificado
(2026-08-02: cambio_2021_2022_v8_230705.img, 5 clases).
"""

from __future__ import annotations

import io
import zipfile

import numpy as np
import pandas as pd
import pytest
import rasterio

from etl.common.config import settings
from etl.ideam.pipeline import CLASES, IDEAM_Ambiental, _PATRON_PERIODO

CRS = "EPSG:3116"


def _raster_sintetico(ruta):
    """8x8 píxeles, 100 m (1 ha). Deforestación (2) en el bloque 2x2 superior
    izquierdo; el resto bosque estable (1); una celda sin información (5)."""
    datos = np.ones((8, 8), dtype=np.uint8) * 1
    datos[0:2, 0:2] = 2
    datos[7, 7] = 5
    with rasterio.open(
        ruta,
        "w",
        driver="GTiff",
        height=8,
        width=8,
        count=1,
        dtype="uint8",
        crs=CRS,
        transform=rasterio.transform.from_origin(0, 800, 100, 100),
    ) as dst:
        dst.write(datos, 1)
    return ruta


@pytest.fixture()
def pipeline_sintetico(tmp_path):
    p = IDEAM_Ambiental()
    p._ruta_img = _raster_sintetico(tmp_path / "cambio_2021_2022_test.img")
    p._anio_inicio, p._anio_fin = 2021, 2022
    p._municipios = [("05001", "Medellín"), ("05002", "Envigado")]
    p._geometrias = {
        "05001": {
            "type": "Polygon",
            "coordinates": [[[0, 800], [0, 500], [300, 500], [300, 800], [0, 800]]],
        },
        "05002": {
            "type": "Polygon",
            "coordinates": [[[400, 800], [400, 600], [700, 600], [700, 800], [400, 800]]],
        },
    }
    p._geometria = lambda codigo: p._geometrias.get(codigo)
    return p


def test_clases_definidas_para_el_raster_real():
    assert set(CLASES) == {1, 2, 3, 4}  # 5 = Sin información, se descarta
    assert CLASES[2][0] == "ideam_deforestacion"


def test_periodo_desde_nombre_del_raster():
    m = _PATRON_PERIODO.search("cambio_2021_2022_v8_230705.img")
    assert m.groups() == ("2021", "2022")


def test_transformar_estadistica_zonal(pipeline_sintetico):
    out = pipeline_sintetico.transformar(pd.DataFrame())
    filas = out.to_dict("records")
    # 05001 cubre 3x3 px: 4 ha deforestación + 5 ha bosque estable
    defo = [f for f in filas if f["codigo_divipola"] == "05001" and f["indicador_codigo"] == "ideam_deforestacion"]
    bosque = [f for f in filas if f["codigo_divipola"] == "05001" and f["indicador_codigo"] == "ideam_bosque_estable"]
    assert len(defo) == 1 and defo[0]["valor"] == pytest.approx(4.0)
    assert len(bosque) == 1 and bosque[0]["valor"] == pytest.approx(5.0)
    # 05002 cubre 3x2 px, todo bosque estable (la celda 5 queda fuera)
    assert not [f for f in filas if f["codigo_divipola"] == "05002" and f["indicador_codigo"] == "ideam_deforestacion"]
    assert [f for f in filas if f["codigo_divipola"] == "05002" and f["indicador_codigo"] == "ideam_bosque_estable"][0]["valor"] == pytest.approx(6.0)
    # La clase 5 (sin información) nunca produce fila
    assert not [f for f in filas if "ideam" in f["indicador_codigo"] and f["valor"] == 1.0 and f["codigo_divipola"] == "05002"]
    assert all(f["unidad"] == "ha" for f in filas)


def test_transformar_sin_capa_municipal_devuelve_vacio(tmp_path):
    p = IDEAM_Ambiental()
    p._ruta_img = _raster_sintetico(tmp_path / "cambio_2021_2022_test.img")
    p._anio_inicio, p._anio_fin = 2021, 2022
    p._municipios = []
    assert p.transformar(pd.DataFrame()).empty


def test_zip_sin_raster_lanza(monkeypatch, tmp_path):
    zip_ruta = tmp_path / "vacio.zip"
    with zipfile.ZipFile(zip_ruta, "w") as z:
        z.writestr("nota.txt", "sin raster")
    with pytest.raises(StopIteration):
        with zipfile.ZipFile(zip_ruta) as z:
            next(n for n in z.namelist() if n.lower().endswith(".img"))


def test_url_zip_configurada_tiene_prioridad(monkeypatch):
    monkeypatch.setattr(settings, "ideam_bosque_url", "https://example.test/cambio.zip")
    assert IDEAM_Ambiental()._url_zip() == "https://example.test/cambio.zip"


def test_url_zip_resuelve_redireccion(monkeypatch):
    monkeypatch.setattr(settings, "ideam_bosque_url", None)

    class _Resp:
        status_code = 302

        def raise_for_status(self):
            pass

        @property
        def headers(self):
            return {"Location": "https://datos.gov.co/archivo.zip"}

    monkeypatch.setattr("etl.ideam.pipeline.requests.get", lambda *a, **k: _Resp())
    assert IDEAM_Ambiental()._url_zip() == "https://datos.gov.co/archivo.zip"


def test_extraer_guarda_zip_e_img_y_parsea_periodo(monkeypatch, tmp_path):
    img_bytes = io.BytesIO()
    with rasterio.open(
        img_bytes,
        "w",
        driver="GTiff",
        height=2,
        width=2,
        count=1,
        dtype="uint8",
        crs=CRS,
        transform=rasterio.transform.from_origin(0, 200, 100, 100),
    ) as dst:
        dst.write(np.ones((2, 2), dtype=np.uint8), 1)

    zip_bytes = io.BytesIO()
    with zipfile.ZipFile(zip_bytes, "w") as z:
        z.writestr("cambio_2020_2021_v9_test.img", img_bytes.getvalue())

    class _ZipResp:
        status_code = 302

        def __init__(self, contenido):
            self._c = contenido

        def raise_for_status(self):
            pass

        @property
        def content(self):
            return self._c

        @property
        def headers(self):
            return {"Location": "https://datos.gov.co/archivo.zip"}

    def fake_get(url, timeout=900, **kwargs):
        return _ZipResp(zip_bytes.getvalue())

    monkeypatch.setattr("etl.ideam.pipeline.requests.get", fake_get)
    p = IDEAM_Ambiental()
    monkeypatch.setattr(p, "_cargar_municipios", lambda: [])
    df, lineage = p.extraer()
    assert df.iloc[0]["periodo"] == "2020-2021"
    assert p._anio_inicio == 2020 and p._anio_fin == 2021
    assert p._ruta_img is not None and p._ruta_img.exists()
    assert lineage.fuente == "IDEAM"
