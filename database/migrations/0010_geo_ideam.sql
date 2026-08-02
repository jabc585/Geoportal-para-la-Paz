-- Migración 0010: capa geo municipal (DIVIPOLA) + raw del pipeline IDEAM
-- ============================================================

-- La capa de contexto (sección 5.1) no tenía vínculo al catálogo DIVIPOLA.
ALTER TABLE curated.capa_contexto_territorial
    ADD COLUMN IF NOT EXISTS codigo_divipola CHAR(5);

-- Una sola geometría vigente por municipio (la siembra es idempotente).
CREATE UNIQUE INDEX IF NOT EXISTS uq_capa_divipola_codigo
    ON curated.capa_contexto_territorial (codigo_divipola)
    WHERE tipo = 'divipola' AND codigo_divipola IS NOT NULL;

-- Raw del pipeline IDEAM: una fila de metadatos por raster procesado
-- (el raster completo queda en data/raw/ideam/, inmutable).
CREATE TABLE IF NOT EXISTS raw.ideam_ambiental (
    id_raw           BIGSERIAL PRIMARY KEY,
    archivo          TEXT NOT NULL,
    contenido        JSONB NOT NULL,
    url_origen       TEXT,
    fecha_extraccion TIMESTAMPTZ NOT NULL DEFAULT now(),
    hash_fila        TEXT NOT NULL
);
