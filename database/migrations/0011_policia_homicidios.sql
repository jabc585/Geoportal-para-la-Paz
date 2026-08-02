-- Migración 0011: raw del pipeline de homicidios (Policía Nacional)
-- ============================================================

-- Los Excel SIEDCO se agregan a municipio-año; raw guarda solo metadatos
-- por archivo descargado (el Excel completo queda en memoria, sin duplicarse).
CREATE TABLE IF NOT EXISTS raw.policia_homicidios (
    id_raw           BIGSERIAL PRIMARY KEY,
    archivo          TEXT NOT NULL,
    contenido        JSONB NOT NULL,
    url_origen       TEXT,
    fecha_extraccion TIMESTAMPTZ NOT NULL DEFAULT now(),
    hash_fila        TEXT NOT NULL
);
