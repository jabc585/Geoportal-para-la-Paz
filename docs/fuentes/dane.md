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

1. Lee el Excel (openpyxl) y normaliza nombres de columnas (minúsculas, sin acentos).
2. Detecta aliases comunes (código DIVIPOLA, año, población).
3. Convierte valores a numéricos y descarta filas sin año o valor.
4. Construye el periodo anual (sección 7.1) y valida con Pandera (`EsquemaSerieNormalizada`).
5. Carga en `curated.serie_historica` con indicador `poblacion` y linaje completo.

## Limitaciones conocidas

- Las proyecciones son estimaciones, no conteos censales.
- Cambios de código DIVIPOLA (creación de municipios) se resuelven contra el SCD tipo 2 de `curated.municipio` (sección 7.2).
- Los nombres de columnas pueden variar entre datasets de la misma fuente; el mapeo por aliases cubre los conocidos.

## Notas de gobernanza

- Licencia verificada en el dataset concreto antes del primer uso productivo.
- No aplica checklist de privacidad especial (población agregada no es identificable), aunque se ejecuta el checklist general (sección 3.1).
