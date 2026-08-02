# Unidad para las Víctimas — Datos Paz

| Campo | Valor |
|---|---|
| Entidad | Unidad Administrativa Especial para la Atención y Reparación a las Víctimas |
| Datos principales | Víctimas, desplazamiento, retornos, reparación |
| URL base | https://datospaz.unidadvictimas.gov.co/ |
| Método de acceso | API (Socrata, datos.gov.co) |
| Periodicidad de actualización | Mensual (cortes de la UARIV) |
| Formato | JSON |
| Licencia | Verificar en ficha (sección 3, punto 5) antes de integración productiva |
| ¿Se combina con cifras municipales? | Sí (municipio/año — nunca a nivel individual) |
| Responsable del conector | Equipo técnico |
| Estado | Conector en desarrollo (carga a `curated` implementada) |

## Descripción

Fuente oficial de hechos victimizantes del conflicto armado: desplazamiento forzado, homicidio, secuestro, minas antipersonal, entre otros. Es el dataset más sensible del observatorio por la naturaleza de los datos.

## Método de acceso

**Hallazgo (auditoría 2026-08-02): el CSV de datos abiertos de Datos Paz**
(`https://datospaz.unidadvictimas.gov.co/archivos/datosabiertos/hechosvictimizantes.csv`)
**responde 404** — el sitio hoy publica sus reportes como Power BI embebido, sin
descarga CSV. La UARIV publica los mismos agregados en el portal oficial de
datos abiertos de Colombia:

- **Dataset municipal** (fuente del conector): "Cifras de Víctimas por Hechos
  Municipal", resource `9qih-4vkc` en https://www.datos.gov.co/resource/9qih-4vkc.json
- **Dataset nacional**: `wy34-4u9y` (totales por corte, para validación)

Verificado en vivo: el corte `31/12/2025` del dataset municipal suma
`sum(per_sa)` = **9.572.942**, que coincide con la cifra oficial de personas
incluidas en el RUV (~9,5 millones) y con el total del dataset nacional.
`per_sa` = sujetos de atención (personas incluidas en el RUV, acumulado a
corte); `per_ocu` = ocurrencia; `eventos` = número de eventos.

El conector usa el resource Socrata municipal como fuente. Si `VICTIMAS_URL`
alguna vez vuelve a responder, se prefiere el CSV configurado (sin default
hardcodeado, riesgo de dominio no controlado):

```
export VICTIMAS_URL="https://datospaz.unidadvictimas.gov.co/archivos/datosabiertos"
```

## Transformaciones aplicadas

El pipeline `etl/victimas/pipeline.py`:

1. Obtiene los cortes disponibles del dataset (`$group=fecha_corte`) y selecciona el último corte de cada año (serie anual de acumulados RUV). Formatos de fecha mixtos en la fuente: `31/12/2025`, `30/09/24`, `31/07/2024 00:00`.
2. Para cada corte agrega `per_sa` (sujetos de atención) por municipio vía Socrata (`$group=cod_estado_depto,cod_ciudad_muni`), descartando la fila `SIN DEFINIR` (código 0).
3. Códigos DIVIPOLA sin cero inicial en la fuente (`5001`) → se normalizan con `zfill(5)` (`05001`).
4. Genera el indicador `victimas_ruv` (personas incluidas en el RUV) en `curated.indicadores`.
5. Valida con Pandera y carga en `curated.serie_historica` con linaje completo.

## Carga verificada (2026-08-02)

Serie anual por municipio del indicador `victimas_ruv` (personas incluidas en
el RUV, acumulado a corte), totales nacionales que coinciden con las cifras
oficiales de la UARIV:

| Año (corte) | Personas incluidas en el RUV |
|---|---|
| 2024 (31/12/2024) | 9.267.604 |
| **2025 (31/12/2025)** | **9.572.942** |
| 2026 (30/06/2026) | 9.625.248 |

La fila `SIN DEFINIR` del dataset municipal (personas sin municipio de reporte,
~1,04M en 2025) se conserva como fila nacional en `serie_historica` — no se
descarta, para que el KPI nacional cuadre con la cifra oficial. El mapa
municipal la excluye naturalmente (no tiene `municipio_id`).

## Limitaciones conocidas

- Las cifras del Registro Único de Víctimas pueden diferir de las de otras entidades (Fiscalía, Medicina Legal) — se documentan discrepancias, no se ocultan (sección 7.5).
- El registro acumulado no es equivalente a la suma de hechos del periodo (revisiones y actualizaciones).
- No publicar jamás a nivel de individuo; cualquier granularidad más fina que municipio/año requiere revisión del comité asesor (sección 3, punto 6) y del checklist de privacidad (sección 3.1).

## Notas de gobernanza

- **Checklist de privacidad ejecutado**: `docs/metodologia/checklist_victimas.md` (evidencia archivada).
- Aprobación del comité asesor requerida antes de habilitar el endpoint público sobre este dataset.
