-- 0014: CHECK rechazados >= 0 (plan.md Bug 5, 2026-08-03).
-- Pipelines con canal lateral (Policía_Homicidios, IDEAM) devolvían
-- registros_rechazados negativo porque extraer() retorna 1 fila de
-- metadatos mientras el canal lateral produce miles de filas reales.
-- La corrección en pipeline.py (self._rechazados) evita el negativo,
-- y esta restricción impide que vuelva a ocurrir por otro camino.

ALTER TABLE curated.data_quality_metrics
  ADD CONSTRAINT dqm_rechazados_no_negativo CHECK (registros_rechazados >= 0);
