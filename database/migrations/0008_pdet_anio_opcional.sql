-- ============================================================
-- Migración 0008: anio opcional en curated.pdet_proyectos (hallazgo de
-- auditoría 2026-08-02: el dataset real "Iniciativas PDET" no reporta año
-- de inversión ni monto; obligarlo impedía cargar proyectos legítimos).
-- Idempotente.
-- ============================================================

ALTER TABLE curated.pdet_proyectos ALTER COLUMN anio DROP NOT NULL;
