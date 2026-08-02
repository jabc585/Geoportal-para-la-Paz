# Policía Nacional — Delitos por municipio

> Fuente nacional (plan2.md Fase B, fuente 5). Datasets reales en datos.gov.co,
> verificados en vivo 2026-08-02, uno por tipo de delito.

| Campo | Valor |
|---|---|
| Entidad | Policía Nacional de Colombia |
| URL base | https://www.datos.gov.co/ (datasets de delitos) |
| Método de acceso | API Socrata (JSON), paginada |
| Periodicidad | Mensual |
| Formato | JSON |
| Licencia | Verificar en ficha (sección 3, punto 5) antes de integración productiva |
| Variables | `POLICIA_HURTO_URL`, `POLICIA_VIOLENCIA_URL`, `POLICIA_SEXUALES_URL` |
| Estado | Conector activo: `etl/policia/pipeline.py` (uno por delito) |

## Datasets y modelo

| Delito | Resource-id | Filas (2026-08-02) | Dimensión |
|---|---|---|---|
| Hurto | `d4fr-sbn2` | 44.169 | tipo de hurto (3) |
| Violencia intrafamiliar | `vuyt-mqpw` | 682.558 | — |
| Delitos sexuales | `fpe5-yrmw` | 392.576 | delito (23) |

Cada fila trae `cantidad` por segmento demográfico (`genero`, `grupo_etario`);
el pipeline **suma `cantidad`** por municipio/año (y tipo cuando existe). El
`codigo_dane` viene como DIVIPOLA de 5 dígitos + "000" (p. ej. `44420000`) y se
recorta al código real.

## Pendiente

**Homicidios**: el dataset general de homicidios intencionales no aparece en el
catálogo (investigación 2026-08-02; `ha6j-pa2r` es "homicidios en accidente de
tránsito", otro fenómeno). `POLICIA_HOMICIDIOS_URL` queda documentada vacía
hasta localizarlo — es la fuente que alimentaría `vw_homicidios_reconciliado`
(sección 7.5).

## Notas de gobernanza

- Filas con fecha inválida o fuera de 1980–2027 se descartan en `transformar`.
- Los datos policiales son denuncias/capturas: pueden diferir de registros
  judiciales (Fiscalía) o de memoria histórica (CNMH); cada fuente conserva su
  linaje y no se mezclan en el dashboard.
