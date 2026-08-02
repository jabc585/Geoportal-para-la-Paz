# Fiscalía — Estadísticas judiciales (datasets V3)

> Fuente nacional (plan2.md Fase B, fuente 3). Datasets reales verificados en
> vivo 2026-08-02 — pero **no implementada operativamente por volumen**.

| Campo | Valor |
|---|---|
| Entidad | Fiscalía General de la Nación |
| URL base | https://www.datos.gov.co/ (datasets V3) |
| Método de acceso | API Socrata (JSON) |
| Periodicidad | Trimestral |
| Formato | JSON |
| Licencia | Verificar en ficha (sección 3, punto 5) antes de integración productiva |
| Variables | `FISCALIA_PROCESOS_URL`, `FISCALIA_VICTIMAS_URL` |
| Estado | **Pendiente**: pipeline escrito y probado, no activo |

## Datasets verificados

| Dataset | Resource-id | Filas | Shape |
|---|---|---|---|
| Procesos V3 | `dbdv-iihs` | 23.212.036 | fila = proceso (`a_o_hecho`, `cod_dane_hecho`, `titulo_delito`, …) |
| Víctimas V3 | `hr73-zqjf` | 17.534.229 | fila = víctima (`id_victima_anonimizado`, datos sociodemográficos) |
| Procesados V3 | `piva-db2c` | 15.414.424 | fila = procesado (no se usa: sin agregar por territorio) |

## Por qué no está activa (hallazgo de volumen, 2026-08-02)

La agregación server-side de SoQL (`$select` + `$group` por municipio/año/título
del delito) reescanea las decenas de millones de filas por consulta: **~10
minutos por página de 50.000 combinaciones** (2020+ ya supera las 50.000;
todo el rango 1980–2026 serían ~200.000 → horas por dataset). No existe un
dataset agregado de estadísticas judiciales en el catálogo (los demás
resultados de "fiscalía" son índices de información clasificada). Un app token
Socrata no acelera el escaneo.

`etl/fiscalia/pipeline.py` queda escrito y probado (agregación SoQL, dimensión
`titulo_delito`, víctimas sin dedupe por id anonimizado — documentado en la
descripción del indicador) y listo para activarse si:

1. la Fiscalía publica datasets agregados por municipio/año, o
2. se acepta una corrida programada de horas (fuera de `run_all`).

## Notas de gobernanza

- Los identificadores de procesos/víctimas ya vienen pseudonimizados por la
  fuente (`proceso_anonimizado`, `id_victima_anonimizado`); la fila individual
  nunca se promueve a curated/API (checklist de privacidad, sección 3.1).
- Sin dedupe por id anonimizado en víctimas a esa escala: el conteo es de
  registros víctima-proceso (una víctima con varios procesos cuenta varias
  veces) — reflejado en el nombre del indicador.
- Registro completo del hallazgo: `config/investigacion_fuentes.yaml`.
