# IDEAM — Deforestación (cambio en bosque natural)

> Fuente nacional (plan2.md Fase C). Formato **confirmado en vivo 2026-08-02**:
> no es un dataset tabular, es un **raster** por periodo.

| Campo | Valor |
|---|---|
| Entidad | Instituto de Hidrología, Meteorología y Estudios Ambientales (IDEAM) |
| URL base | https://www.datos.gov.co/ (dataset `39dh-rc72`) |
| Método de acceso | Descarga de archivo (ZIP con raster Erdas Imagine) |
| Periodicidad | Anual (un dataset "Cambio" por periodo de años) |
| Formato | ZIP → `.img` + `.rrd` + `Contenido_Cambio.txt` |
| Licencia | Sin validación IDEAM (cláusulas del dataset: datos crudos, no como evidencia jurídica) — revisar en ficha (sección 3, punto 5) |
| Variables | `IDEAM_BOSQUE_URL` |
| Estado | **Pendiente**: requiere estadística zonal del raster |

## Contenido verificado (2026-08-02)

- Descarga real: `https://www.datos.gov.co/api/views/39dh-rc72/files/66e53106-a67b-45ff-a6a5-e1170ec10438?filename=Cambio_2022.zip`
  (ZIP 38MB; el resource-id del archivo puede rotar si IDEAM lo re-publica —
  resolverlo desde la vista `https://www.datos.gov.co/api/views/39dh-rc72.json`
  siguiendo la redirección de `/download/39dh-rc72`).
- ZIP con `cambio_2021_2022_v8_230705.img` (52MB, Erdas Imagine), `.rrd`
  (sidecar) y `Contenido_Cambio.txt`.
- Raster de 5 clases: `1` Bosque Estable, `2` Deforestación, `3` Regeneración,
  `4` No Bosque estable, `5` Sin información.
- El endpoint SoQL responde `403 no row or column access to non-tabular tables`
  (no hay JSON).

## Qué se necesitaría para integrarlo

1. Descargar el ZIP y leer el `.img` (GDAL/rasterio).
2. **Estadística zonal** del raster contra la geometría municipal DIVIPOLA
   (la BD aún no tiene la capa geo de municipios; sección 5.1 la prevé como
   `curated.capa_contexto_territorial`).
3. Derivar por municipio: superficie deforestada/regenerada/bosque estable (ha
   o km²) por periodo → `curated.serie_historica` (fuente IDEAM).

Es un pipeline distinto de los tabulares (procesamiento geoespacial), por eso
queda fuera de `run_all` hasta tener la capa municipal y GDAL en las
dependencias. El hallazgo completo está en
`config/investigacion_fuentes.yaml`.
