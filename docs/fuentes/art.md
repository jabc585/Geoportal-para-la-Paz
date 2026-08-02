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

Variable de entorno requerida: `PDET_URL` (endpoint del catálogo de proyectos PDET).

## Transformaciones aplicadas

El pipeline `etl/pdet/pipeline.py`:

1. Normaliza nombres de columnas y detecta aliases (código DIVIPOLA, nombre del proyecto, estado, avance, inversión, año).
2. Carga proyectos en `curated.pdet_proyectos` con linaje completo.
3. Agrega la inversión por municipio/año y carga en `curated.serie_historica` con indicador `pdet_inversion`.

## Limitaciones conocidas

- La cobertura es solo de municipios PDET (170 municipios en 16 subregiones), no de todo el país.
- Los valores de inversión pueden venir en distintas unidades (COP corriente vs. constante) — verificar y documentar.
- El avance declarado no siempre refleja la ejecución física verificada.

## Notas de gobernanza

- No contiene datos sensibles de víctimas; checklist de privacidad general aplica (sección 3.1).
