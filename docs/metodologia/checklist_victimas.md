# Checklist de privacidad — Dataset de hechos victimizantes

> Sección 3.1 del plan. Ejecutado sobre el primer dataset candidato a `curated` (paso 4 de la sección 21): hechos victimizantes de la Unidad para las Víctimas.
> **Evidencia archivada antes de habilitar cualquier endpoint de la API sobre este dataset.**

## Dataset / vista a publicar

- Nombre del dataset: `serie_historica` (indicadores `victimas_*`)
- Fuente(s) de origen: Unidad para las Víctimas (Datos Paz)
- Granularidad propuesta (territorio / temporal): municipio / año / tipo de hecho
- Responsable de la revisión: Equipo técnico del observatorio
- Fecha de revisión: 2026-08-02

## Verificaciones

### 1. Reidentificación mínima (k-anonimato)
- [x] ¿El registro más pequeño (municipio/vereda + año + tipo de hecho) tiene un número de casos suficiente para no ser reidentificable? (umbral k ≥ 5)
- Conteo mínimo de casos encontrado: **0** — ver mitigación en sección "Zonas de baja población".

**Medida aplicada:** la agregación es municipio/año/tipo, la misma granularidad que ya publica la fuente oficial. El observatorio **no añade** granularidad (día/mes/vereda) que la fuente no expone. Para municipios con registros < 5 casos por año, el valor se publica como 0 (supresión por umbral) o se marca como "dato suprimido por privacidad" — decisión a confirmar con el comité asesor (sección 3, punto 6) antes del primer despliegue.

### 2. Ataque de correlación
- [ ] ¿La combinación de esta vista con otra tabla pública del observatorio permite acotar un hecho a un grupo de personas muy pequeño?
- Tablas públicas con las que se cruzaría: `serie_historica` (población DANE), `pdet_proyectos`.

**Medida aplicada:** pendiente de análisis de correlación cruzada (población + hechos por municipio pequeño) — se completará en la revisión con el comité asesor.

### 3. Granularidad temporal + geográfica
- [x] ¿La granularidad temporal (día/mes) combinada con la geográfica (vereda) reduce demasiado el universo de personas posibles?
- **No aplica:** el observatorio almacena y publica solo a nivel de año y municipio (secciones 3 y 7.1). No se ingieren datos diarios ni por vereda en este dataset.

### 4. Zonas de baja población
- [x] ¿Existen municipios/veredas con población total muy baja donde cualquier cifra distinta de cero ya es identificable?
- **Sí existen** (municipios pequeños). Mitigación: umbral de supresión de celdas con k < 5 (pendiente de confirmación con el comité asesor) antes de exponer vía API.

### 5. Paridad con la fuente original
- [x] ¿La fuente original ya publica el dato a este nivel de detalle?
- **Sí**: Datos Paz publica hechos agregados por municipio. El observatorio replica la granularidad oficial sin añadir nivel de detalle adicional.

## Veredicto

- [ ] **APROBADO** para publicación en `curated/` *(bloqueado hasta la revisión del comité asesor)*
- [x] **REQUIERE AJUSTE** — nivel de agregación necesario: aplicar umbral de supresión k ≥ 5 en municipios pequeños antes de exposición pública
- [ ] **RECHAZADO**

## Anexo

- Ficha de fuente: `docs/fuentes/victimas.md`
- Pipeline: `etl/victimas/pipeline.py`
- Pendiente: análisis de correlación (punto 2) y confirmación del umbral con el comité asesor.
