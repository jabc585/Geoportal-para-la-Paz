# CNMH — Memoria histórica del conflicto (SIEVCAC)

> Fuente nacional de memoria histórica (plan2.md Fase B, fuente 2). Datasets
> reales del Sistema SIEVCAC del Centro Nacional de Memoria Histórica en
> datos.gov.co, verificados en vivo 2026-08-02 — el mejor acceso encontrado
> para fuentes de memoria histórica.

| Campo | Valor |
|---|---|
| Entidad | Centro Nacional de Memoria Histórica (CNMH) |
| URL base | https://www.datos.gov.co/ (datasets SIEVCAC) |
| Método de acceso | API Socrata (JSON), paginada (`$limit`/`$offset`) |
| Periodicidad | Anual |
| Formato | JSON |
| Licencia | Verificar en ficha (sección 3, punto 5) antes de integración productiva |
| Variables | `CNMH_MINAS_URL`, `CNMH_ATENTADOS_URL`, `CNMH_DESAPARICION_URL`, `CNMH_RECLUTAMIENTO_URL`, `CNMH_BIENES_URL`, `CNMH_ACCIONES_URL` |
| Estado | Conector activo: `etl/memoria/pipeline.py` (uno por tipo de hecho) |

## Datasets y modelo

| Hecho | Resource-id | Tipo | Indicador |
|---|---|---|---|
| Minas antipersonal | `52eu-ic7d` | víctimas | `cnmh_minas_victimas` |
| Atentados terroristas | `yfd7-8c9d` | casos | `cnmh_atentados_casos` |
| Desaparición forzada | `c59y-p4sz` | víctimas | `cnmh_desaparicion_victimas` |
| Reclutamiento de NNA | `hzd2-7ea7` | casos | `cnmh_reclutamiento_casos` |
| Daño a bienes civiles | `a2ga-ur2i` | víctimas | `cnmh_bienes_victimas` |
| Acciones bélicas | `chb6-bfmq` | víctimas | `cnmh_acciones_victimas` |

Dos shapes en la fuente (verificado en vivo):

- **casos** (atentados, reclutamiento): cada fila es un caso (`id_caso` único).
- **víctimas** (minas, desaparición, bienes, acciones): cada fila es una
  persona (`id_persona`); el pipeline cuenta personas únicas por municipio/año.

## Privacidad (sección 3.1)

Los datasets de tipo víctimas contienen `id_persona`, `sexo`, `edad`,
`ocupaci_n` y estado actual — **datos personales**. La fila individual queda
solo en la capa `raw` (interna, inmutable, acceso controlado) y **nunca** se
promueve a `curated` ni a la API: a `curated.serie_historica` solo suben
conteos agregados por municipio/año. `latitud_longitud` de los casos tampoco se
promueve. Antes de habilitar este dataset en la API se ejecuta el checklist de
privacidad (mismo procedimiento que `docs/metodologia/checklist_victimas.md`).

## Notas de gobernanza

- `a_o` con valor `0` o fuera de 1980–2027 se descarta (dato corrupto en la
  fuente; ~1.5% de las filas de desaparición).
- El recuento CNMH puede diferir del registro oficial de la Unidad para las
  Víctimas: son metodologías distintas; usar como capa de contexto de memoria
  histórica, no de reconciliación.
- Volúmenes reales (2026-08-02): minas 10.654, atentados 325, desaparición
  82.486, bienes 466, reclutamiento 17.373, acciones 54.032 filas → ~26.800
  series municipio-año en total.
