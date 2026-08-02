# Policía Nacional — Delitos por municipio

> Fuente nacional (plan2.md Fase B, fuente 5). Datasets reales en datos.gov.co
> (delitos) y Excel oficial SIEDCO (homicidios), verificados en vivo 2026-08-02.

| Campo | Valor |
|---|---|
| Entidad | Policía Nacional de Colombia |
| URL base | https://www.datos.gov.co/ (datasets de delitos) y https://www.policia.gov.co/estadistica-delictiva/homicidios (Excel SIEDCO) |
| Método de acceso | API Socrata (JSON) paginada + descarga de Excel |
| Periodicidad | Mensual (delitos); anual (homicidios) |
| Formato | JSON, Excel |
| Licencia | Verificar en ficha (sección 3, punto 5) antes de integración productiva |
| Variables | `POLICIA_HURTO_URL`, `POLICIA_VIOLENCIA_URL`, `POLICIA_SEXUALES_URL`, `POLICIA_HOMICIDIOS_URL` |
| Estado | Conector activo: `etl/policia/pipeline.py` (uno por delito + homicidios) |

## Datasets y modelo

| Delito | Resource-id | Filas (2026-08-02) | Dimensión |
|---|---|---|---|
| Hurto | `d4fr-sbn2` | 44.169 | tipo de hurto (3) |
| Violencia intrafamiliar | `vuyt-mqpw` | 682.558 | — |
| Delitos sexuales | `fpe5-yrmw` | 392.576 | delito (23) |
| Homicidios (Excel SIEDCO) | — | 13.727 (2025) | — |

Cada fila trae `cantidad` por segmento demográfico (`genero`, `grupo_etario`);
el pipeline **suma `cantidad`** por municipio/año (y tipo cuando existe). El
`codigo_dane` viene como DIVIPOLA de 5 dígitos + "000" (p. ej. `44420000`) y se
recorta al código real.

## Homicidios (Excel oficial SIEDCO)

No existe dataset Socrata de homicidios intencionales, pero la Policía publica
el Excel SIEDCO por año en `policia.gov.co/estadistica-delictiva/homicidios`
(p. ej. `Homicidio Intencional2025.xlsx`, 507 KB, 13.727 filas con
`FECHA HECHO`, `CODIGO DANE` y `CANTIDAD`). `Policia_Homicidios` lo descarga
(variable `POLICIA_HOMICIDIOS_URL` o patrón por año) y carga el indicador
`homicidios` bajo la fuente `policia` (una fila por homicidio, agregada a
municipio-año; sin PII) — alimenta `vw_homicidios_reconciliado` (sección 7.5).

Nota verificada: "Homicidio Intencional2024.xlsx" es **parcial** (solo 2024-12 +
ene-abr 2025) y contaminaría el total anual con doble conteo; el default del
pipeline es solo el último año completo.

## Notas de gobernanza

- Filas con fecha inválida o fuera de 1980–2027 se descartan en `transformar`.
- Los datos policiales son denuncias/capturas: pueden diferir de registros
  judiciales (Fiscalía) o de memoria histórica (CNMH); cada fuente conserva su
  linaje y no se mezclan en el dashboard.
