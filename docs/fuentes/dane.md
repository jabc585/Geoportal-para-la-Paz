# DANE — Departamento Administrativo Nacional de Estadística

| Campo | Valor |
|---|---|
| Entidad | DANE |
| Datos principales | Población, pobreza, empleo, educación |
| URL base | https://www.dane.gov.co/ (datos abiertos: https://www.datos.gov.co/) |
| Método de acceso | **Descarga directa (Excel)** — verificado en auditoría 2026-08-02 |
| Periodicidad de actualización | Anual (proyecciones de población); censos decenales |
| Formato | XLSX (no JSON) |
| Licencia | CC BY 4.0 (Datos Abiertos Colombia) — verificar en el dataset específico (sección 3, punto 5) |
| ¿Se combina con cifras municipales? | Sí (población por municipio) |
| Responsable del conector | Equipo técnico |
| Estado | Conector en desarrollo (carga a `curated` implementada) |

## Descripción

Fuente oficial de estadísticas sociodemográficas de Colombia. Para el observatorio, la prioridad es la población por municipio (proyecciones y conciliación censal), que sirve como denominador para tasas de homicidio, victimización y cobertura.

## Método de acceso (verificado 2026-08-02)

**No existe un dataset Socrata nacional `codigo_municipio × año × población`** (auditoría: búsqueda en `datos.gov.co/api/catalog/v1` por "proyecciones población municipio" devuelve solo datasets locales/departamentales). La serie nacional oficial es un archivo Excel publicado por DANE:

- Archivo: `DCD-area-proypoblacion-Mun-2020-2035-ActPostCOVID-19.xlsx` (dane.gov.co, sección publicaciones — la URL exacta cambia con cada publicación)

Variables de entorno requeridas:

- `DANE_POBLACION_XLSX_URL` — URL directa del Excel de proyecciones por municipio (recomendado)
- `DANE_POBLACION_HOJA` — nombre de la hoja (opcional; default: primera)
- `DANE_POBLACION_DATASET` — legacy: identificador Socrata, solo para datasets locales que cumplan el shape

## Transformaciones aplicadas

El pipeline `etl/dane/pipeline.py`:

1. Lee el Excel (openpyxl) con **encabezado detectado automáticamente**: el archivo oficial trae ~8 filas de título/metadata antes de la fila de columnas reales (fila 9, verificada en auditoría 2026-08-02). Las columnas reales son `DP`, `DPNOM`, `MPIO` (código de 5 dígitos), `DPMP` (contiene el **nombre** del municipio, no un código — nombre confuso pero así lo publica DANE), `AÑO`, `ÁREA GEOGRÁFICA`, `Población`.
2. **Filtra por `ÁREA GEOGRÁFICA == "Total"`**: cada municipio/año aparece 3 veces (Cabecera Municipal / Centros Poblados y Rural Disperso / Total); sin este filtro la población se triplicaría. Ejemplo real verificado: Medellín 2020 → 2.476.569 + 43.023 = 2.519.592.
3. Normaliza nombres de columnas (minúsculas, sin acentos) y detecta aliases (incluye `mpio` para el código).
4. **Recorta el pie de página**: el archivo oficial trae filas finales que no son datos (nota sobre Barrancominas, cita de fuente, fecha de actualización — hallazgo de auditoría 2026-08-02). Se descartan las filas donde todas las columnas de datos (código/año/población) están vacías.
5. Convierte valores a numéricos y descarta filas sin año o valor.
6. Construye el periodo anual (sección 7.1) y valida con Pandera (`EsquemaSerieNormalizada`).
7. Carga en `curated.serie_historica` con indicador `poblacion` y linaje completo.

Como red de seguridad genérica, `insertar_raw()` sanea NaN/NaT a `None` antes de serializar a jsonb (Python escribe el token `NaN`, que Postgres jsonb rechaza: "Token NaN is invalid").

> `DANE_POBLACION_HOJA` sin configurar usa la primera hoja del libro (en pandas, `sheet_name=None` significaría "todas las hojas" y rompería el pipeline; el conector usa `hoja or 0`).

## Limitaciones conocidas

- Las proyecciones son estimaciones, no conteos censales.
- Cambios de código DIVIPOLA (creación de municipios) se resuelven contra el SCD tipo 2 de `curated.municipio` (sección 7.2).
- Los nombres de columnas pueden variar entre datasets de la misma fuente; el mapeo por aliases cubre los conocidos.
- El pie de página del Excel cambia entre publicaciones; el recorte es por columnas de datos vacías, no por contenido de texto.

## Notas de gobernanza

- Licencia verificada en el dataset concreto antes del primer uso productivo.
- No aplica checklist de privacidad especial (población agregada no es identificable), aunque se ejecuta el checklist general (sección 3.1).
