# Unidad para las Víctimas — Datos Paz

| Campo | Valor |
|---|---|
| Entidad | Unidad Administrativa Especial para la Atención y Reparación a las Víctimas |
| Datos principales | Víctimas, desplazamiento, retornos, reparación |
| URL base | https://datospaz.unidadvictimas.gov.co/ |
| Método de acceso | API |
| Periodicidad de actualización | Trimestral (reportes de la UARIV) |
| Formato | JSON |
| Licencia | Verificar en ficha (sección 3, punto 5) antes de integración productiva |
| ¿Se combina con cifras municipales? | Sí (municipio/año — nunca a nivel individual) |
| Responsable del conector | Equipo técnico |
| Estado | Conector en desarrollo (carga a `curated` implementada) |

## Descripción

Fuente oficial de hechos victimizantes del conflicto armado: desplazamiento forzado, homicidio, secuestro, minas antipersonal, entre otros. Es el dataset más sensible del observatorio por la naturaleza de los datos.

## Método de acceso

API de Datos Paz:

```
GET https://datospaz.unidadvictimas.gov.co/api/v1/hechos_victimizantes
```

Variable de entorno opcional: `VICTIMAS_URL` (default: URL anterior).

## Transformaciones aplicadas

El pipeline `etl/victimas/pipeline.py`:

1. Normaliza nombres de columnas y detecta aliases (código DIVIPOLA, año, tipo de hecho, casos).
2. **Agrega por municipio/año/tipo de hecho** (sección 3, punto 2: nivel mínimo de agregación).
3. Genera un indicador por tipo de hecho (`victimas_<tipo>` en `curated.indicadores`).
4. Valida con Pandera y carga en `curated.serie_historica` con linaje completo.

## Limitaciones conocidas

- Las cifras del Registro Único de Víctimas pueden diferir de las de otras entidades (Fiscalía, Medicina Legal) — se documentan discrepancias, no se ocultan (sección 7.5).
- El registro acumulado no es equivalente a la suma de hechos del periodo (revisiones y actualizaciones).
- No publicar jamás a nivel de individuo; cualquier granularidad más fina que municipio/año requiere revisión del comité asesor (sección 3, punto 6) y del checklist de privacidad (sección 3.1).

## Notas de gobernanza

- **Checklist de privacidad ejecutado**: `docs/metodologia/checklist_victimas.md` (evidencia archivada).
- Aprobación del comité asesor requerida antes de habilitar el endpoint público sobre este dataset.
