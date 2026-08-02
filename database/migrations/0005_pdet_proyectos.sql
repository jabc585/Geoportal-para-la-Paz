-- ============================================================
-- Migración 0005: Tabla de proyectos PDET (sección 7: entidad PDET).
-- Proyectos, avance e inversión, con linaje completo.
-- ============================================================
CREATE TABLE curated.pdet_proyectos (
    proyecto_id      BIGSERIAL PRIMARY KEY,
    municipio_id     INTEGER REFERENCES curated.municipio (municipio_id),
    departamento_id  INTEGER REFERENCES curated.departamento (departamento_id),
    nombre           TEXT NOT NULL,
    estado           TEXT,
    avance_pct       NUMERIC(5, 2) CHECK (avance_pct BETWEEN 0 AND 100),
    valor_inversion  NUMERIC,
    anio             INTEGER NOT NULL,
    fuente_id        INTEGER NOT NULL REFERENCES curated.fuentes (fuente_id),
    url_origen       TEXT,
    fecha_extraccion TIMESTAMPTZ NOT NULL,
    fecha_corte_dato DATE,
    hash_registro    TEXT NOT NULL,
    creado_en        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_pdet_municipio ON curated.pdet_proyectos (municipio_id, anio);

COMMENT ON TABLE curated.pdet_proyectos IS 'Proyectos PDET de la ART (sección 7): avance e inversión por municipio, con linaje completo.';
