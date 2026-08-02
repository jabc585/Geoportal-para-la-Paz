# ART — Agencia de Renovación del Territorio (PDET)

| Campo | Valor |
|---|---|
| Entidad | Agencia de Renovación del Territorio |
| Datos principales | Proyectos PDET: avance, inversión, obras |
| URL base | https://www.renovacionterritorio.gov.co/ |
| Método de acceso | Descarga (API/portal en definición) |
| Periodicidad de actualización | Mensual |
| Formato | JSON / CSV |
| Licencia | Verificar en ficha (sección 3, punto 5) antes de integración productiva |
| ¿Se combina con cifras municipales? | Sí (municipios PDET) |
| Responsable del conector | Equipo técnico |
| Estado | Conector en desarrollo (carga a `curated` implementada) |

## Descripción

Proyectos de los Programas de Desarrollo con Enfoque Territorial (PDET), con su estado de avance e inversión. Módulo funcional "Desarrollo Territorial" y seguimiento al Acuerdo de Paz (sección 11).

## Método de acceso

**Verificado en vivo (auditoría 2026-08-02, tercera pasada):** la ART publica datos PDET en datos.gov.co (Socrata), y el conector funciona contra ellos:

- **Iniciativas PDET** — `https://www.datos.gov.co/resource/gmvf-t63e.json` (~18.6k iniciativas de los 16 PDET). Columnas reales: `codigodane` (código DANE del municipio), `t_tulo_iniciativa`, `subregi_n`, `municipio_sujeto_concertaci`, `pilar`, `sector`, etc. **No reporta estado, avance, inversión ni año** → el conector los trata como opcionales (migración 0008 permite `anio` nulo).
- **Contratación Municipios PDET** — `https://www.datos.gov.co/resource/xqtq-puna.json`: sí trae `valor_contrato` y `estado_del_proceso`, pero **sin columna de municipio** (el código DANE está embebido en el nombre de la entidad) — no se usa todavía; candidato para enriquecer inversión en una iteración futura.

**Carga verificada (2026-08-02):** dataset de iniciativas activado (`PDET_URL`), 33.007 filas crudas → **965 proyectos** en **170 municipios PDET** cargados a `curated.pdet_proyectos`. El dataset de iniciativas no reporta inversión/año → no agrega serie (comportamiento documentado). Endpoint `GET /api/v1/pdet/proyectos` (proyectos + municipios) alimenta el KPI del dashboard.

Variable de entorno: `PDET_URL` (cualquier dataset Socrata con `codigodane` + columna de nombre).

> Nota operativa: las filas con `codigodane` `00000`/`99999` (mesas de concertación, cabildos, nivel "SUBREGIONAL") no son municipios y se descartan con aviso — comportamiento esperado, no es pérdida de datos.

## Transformaciones aplicadas

El pipeline `etl/pdet/pipeline.py`:

1. Normaliza nombres de columnas y detecta aliases (código DIVIPOLA, nombre del proyecto, estado, avance, inversión, año). Código y nombre son obligatorios; el resto opcional (datasets reales de la ART no los reportan).
2. Carga proyectos en `curated.pdet_proyectos` con linaje completo (`executemany` para volumen).
3. Agrega la inversión por municipio/año y carga en `curated.serie_historica` con indicador `pdet_inversion` — solo si la fuente reporta inversión y año; si no, lo informa y no agrega serie.

## Limitaciones conocidas

- La cobertura es solo de municipios PDET (170 municipios en 16 subregiones), no de todo el país.
- Los valores de inversión pueden venir en distintas unidades (COP corriente vs. constante) — verificar y documentar.
- El avance declarado no siempre refleja la ejecución física verificada.

## Notas de gobernanza

- No contiene datos sensibles de víctimas; checklist de privacidad general aplica (sección 3.1).
