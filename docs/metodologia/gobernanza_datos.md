# Gobernanza y ética de datos

> Documento formal del Observatorio para la Paz en Colombia (sección 3 del plan).
> Estado: borrador — pendiente de validación externa (sección 21, pasos 1-2).

## Principios

1. **Solo fuentes oficiales y públicas.** No se scrapean redes sociales ni se infieren datos de terceros no verificados.
2. **Nivel mínimo de agregación.** Datos de víctimas, alertas tempranas y hechos victimizantes publicados agregados (municipio/año como mínimo), nunca a nivel individual — principio de "no daño" (Unidad de Víctimas, CICR).
3. **Neutralidad y verificabilidad.** El observatorio no atribuye responsabilidad penal ni política a actores armados; reporta cifras oficiales con su fuente. Análisis interpretativos siempre etiquetados como tales.
4. **Trazabilidad obligatoria.** Todo registro conserva: `fuente`, `url_origen`, `fecha_extraccion`, `fecha_corte_dato`, `licencia`.
5. **Revisión de licencias.** Verificada fuente por fuente antes de integrar (Datos Abiertos Colombia: CC BY 4.0 por defecto; fuentes internacionales caso por caso — p. ej. ACLED exige atribución).
6. **Comité asesor plural.** Composición mínima:
   - Organización de víctimas
   - Centro académico o de investigación
   - Entidad del Estado (p. ej. DNP o CNMH)
   - ONG de derechos humanos
   
   El comité valida metodología de indicadores, criterios de agregación y aprueba explícitamente cualquier módulo de análisis automatizado antes de su publicación.
7. **Corrección y actualización.** Mecanismo público para reportar errores o solicitar corrección/retiro de un dato (canal de contacto en el sitio).

## Privacidad

- Sin PII: ningún pipeline ingiere ni almacena datos a nivel de individuo identificable (sección 13).
- Checklist de privacidad (sección 3.1) ejecutada y archivada antes de habilitar cualquier dataset nuevo: `docs/metodologia/checklist_privacidad.md`.

## Decisiones pendientes

- [ ] Confirmación del umbral de k-anonimato (≥ 5 propuesto) con el comité asesor.
- [ ] Conformación del comité asesor con las 4 categorías de actores.
- [ ] Validación del catálogo inicial de indicadores con al menos dos organizaciones aliadas.
- [ ] Criterio metodológico de reconciliación de homicidios (Policía vs. Medicina Legal) — sección 7.5.
