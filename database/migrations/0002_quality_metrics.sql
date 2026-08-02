-- ============================================================
-- Migración 0002: Calidad de datos y auditoría de ETL
-- Sección 7.4 del plan: data_quality_metrics graficable en el tiempo.
-- ============================================================

-- Métricas de calidad por corrida de pipeline (sección 7.4)
CREATE TABLE curated.data_quality_metrics (
    metric_id               BIGSERIAL PRIMARY KEY,
    pipeline_id             TEXT NOT NULL,            -- p. ej. 'dane_poblacion'
    timestamp_ejecucion     TIMESTAMPTZ NOT NULL,
    registros_leidos        INTEGER NOT NULL,
    registros_validos       INTEGER NOT NULL,
    registros_rechazados    INTEGER NOT NULL,
    nulos_por_columna_critica JSONB NOT NULL DEFAULT '{}'::jsonb,
    duracion_segundos       NUMERIC(10, 2) NOT NULL,
    estado                  TEXT NOT NULL CHECK (estado IN ('exitoso', 'parcial', 'fallido')),
    mensaje_error           TEXT,
    CHECK (registros_leidos >= registros_validos + registros_rechazados)
);

CREATE INDEX idx_dqm_pipeline_tiempo ON curated.data_quality_metrics (pipeline_id, timestamp_ejecucion DESC);

COMMENT ON TABLE curated.data_quality_metrics IS 'Métricas de calidad por corrida (sección 7.4). Si registros_rechazados supera un umbral se alerta antes de promover a curated.';

-- Registro de auditoría de ejecuciones (sección 12)
CREATE TABLE curated.audit_log (
    audit_id        BIGSERIAL PRIMARY KEY,
    pipeline_id     TEXT NOT NULL,
    evento          TEXT NOT NULL,             -- 'inicio', 'exito', 'fallo'
    registros_insertados INTEGER DEFAULT 0,
    registros_actualizados INTEGER DEFAULT 0,
    registros_rechazados INTEGER DEFAULT 0,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT now(),
    detalle         JSONB
);

CREATE INDEX idx_audit_pipeline ON curated.audit_log (pipeline_id, timestamp DESC);
