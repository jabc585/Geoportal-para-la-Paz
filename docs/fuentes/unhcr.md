# UNHCR — Población refugiada y desplazada de Colombia

> Fuente internacional (plan2.md Fase B, fuente 1). API pública **sin
> autenticación**, verificada en vivo 2026-08-02. Se carga en
> `curated.indicador_internacional` a nivel **país** (secciones 5.2 y 7.6).

| Campo | Valor |
|---|---|
| Entidad | Oficina del Alto Comisionado de las Naciones Unidas para los Refugiados (ACNUR) |
| URL base | https://api.unhcr.org/population/v1/ |
| Método de acceso | API (JSON) |
| Periodicidad | Anual |
| Formato | JSON |
| Licencia | UNHCR Public Data (acceso público) |
| Variable | `UNHCR_BASE_URL` (default: `https://api.unhcr.org/population/v1`) |
| Estado | Conector activo: `etl/internacional/unhcr.py` |

## Qué se carga

Serie anual (1981–2025) de población colombiana (`coo=COL`) por tipo de
protección, un indicador por tipo en `curated.indicador_internacional`:

| Columna API | Indicador |
|---|---|
| `refugees` | Población refugiada colombiana |
| `asylum_seekers` | Solicitantes de asilo colombianos |
| `returned_refugees` | Retornados refugiados |
| `idps` | Desplazados internos (IDP) |
| `returned_idps` | Retornados desplazados internos |
| `stateless` | Apátridas |
| `ooc` | Otros en necesidad de protección (OOC) |
| `oip` | Otros en situación similar a IDP (OIP) |

## Notas de gobernanza

- Los valores `-` (no disponible) se descartan en `transformar()`; `0` literal
  se conserva como dato válido.
- No hay PII: series agregadas a nivel país por año (checklist de privacidad,
  sección 3.1).
- Verificar en ficha antes de integración productiva: las cifras de IDP de
  UNHCR pueden diferir del registro oficial de la Unidad para las Víctimas
  (metodologías distintas); usar como capa de contexto internacional, no de
  reconciliación.
