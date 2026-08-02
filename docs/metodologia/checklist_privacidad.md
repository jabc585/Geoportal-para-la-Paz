# Checklist de privacidad previo a publicación

> Fuente: adaptado de guías públicas del CICR/ICRC y HRDAG sobre protección de datos en contextos de conflicto (sección 3.1 del plan).
> **Obligatorio antes de habilitar cualquier dataset o vista nueva en `curated/`.** El resultado se anexa como evidencia (issue/PR) junto al dataset.

## Dataset / vista a publicar

- Nombre del dataset:
- Fuente(s) de origen:
- Granularidad propuesta (territorio / temporal):
- Responsable de la revisión:
- Fecha de revisión:

## Verificaciones

### 1. Reidentificación mínima (k-anonimato)
- [ ] ¿El registro más pequeño (municipio/vereda + año + tipo de hecho) tiene un número de casos suficiente para no ser reidentificable? (umbral de k-anonimato ≥ 5, a confirmar con el comité asesor).
- [ ] Anotar aquí el conteo mínimo de casos encontrado:

### 2. Ataque de correlación
- [ ] ¿La combinación de esta vista con otra tabla pública del observatorio permite acotar un hecho a un grupo de personas muy pequeño?
- [ ] Listar las tablas públicas con las que se cruzaría:

### 3. Granularidad temporal + geográfica
- [ ] ¿La granularidad temporal (día/mes) combinada con la geográfica (vereda) reduce demasiado el universo de personas posibles?

### 4. Zonas de baja población
- [ ] ¿Existen municipios/veredas con población total muy baja donde cualquier cifra distinta de cero ya es identificable?

### 5. Paridad con la fuente original
- [ ] ¿La fuente original ya publica el dato a este nivel de detalle, o el observatorio estaría añadiendo granularidad que la fuente no expone?

## Veredicto

- [ ] **APROBADO** para publicación en `curated/`
- [ ] **REQUIERE AJUSTE** (indicar nivel de agregación necesario):
- [ ] **RECHAZADO** (justificación):

## Anexo

- Ficha de fuente(s): `docs/fuentes/<fuente>.md`
- Enlace al PR/issue con la evidencia:
