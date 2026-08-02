# DANE — Departamento Administrativo Nacional de Estadística

| Campo | Valor |
|---|---|
| Entidad | DANE |
| Datos principales | Población, pobreza, empleo, educación |
| URL base | https://www.dane.gov.co/ (datos abiertos: https://www.datos.gov.co/) |
| Método de acceso | API (Socrata) |
| Periodicidad de actualización | Anual (proyecciones de población); censos decenales |
| Formato | JSON / CSV |
| Licencia | CC BY 4.0 (Datos Abiertos Colombia) — verificar en el dataset específico (sección 3, punto 5) |
| ¿Se combina con cifras municipales? | Sí (población por municipio) |
| Responsable del conector | Equipo técnico |
| Estado | Conector en desarrollo (carga a `curated` implementada) |

## Descripción

Fuente oficial de estadísticas sociodemográficas de Colombia. Para el observatorio, la prioridad es la población por municipio (proyecciones y conciliación censal), que sirve como denominador para tasas de homicidio, victimización y cobertura.

## Método de acceso

Los datasets de datos.gov.co se consultan por la API Socrata:

```
GET https://www.datos.gov.co/resource/<dataset_id>.json?$limit=50000
```

Variable de entorno requerida:

- `DANE_POBLACION_DATASET` — identificador del dataset de proyecciones de población (p. ej. el dataset de proyecciones municipales 2018-2035).

## Transformaciones aplicadas

El pipeline `etl/dane/pipeline.py`:

1. Normaliza nombres de columnas a minúsculas y detecta aliases comunes (código DIVIPOLA, año, población).
2. Convierte valores a numéricos y descarta filas sin año o valor.
3. Construye el periodo anual (sección 7.1) y valida con Pandera (`EsquemaSerieNormalizada`).
4. Carga en `curated.serie_historica` con indicador `poblacion` y linaje completo.

## Limitaciones conocidas

- Las proyecciones son estimaciones, no conteos censales.
- Cambios de código DIVIPOLA (creación de municipios) se resuelven contra el SCD tipo 2 de `curated.municipio` (sección 7.2).
- Los nombres de columnas pueden variar entre datasets de la misma fuente; el mapeo por aliases cubre los conocidos.

## Notas de gobernanza

- Licencia verificada en el dataset concreto antes del primer uso productivo.
- No aplica checklist de privacidad especial (población agregada no es identificable), aunque se ejecuta el checklist general (sección 3.1).
