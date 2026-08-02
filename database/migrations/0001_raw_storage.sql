-- ============================================================
-- Migración 0001: Capas de almacenamiento (raw/staging)
-- Tablas espejo de raw y staging por fuente (sección 7.3).
-- Cada fuente de la fase piloto tiene una tabla cruda.
-- ============================================================

-- raw.dane_poblacion: proyecciones/conciliaciones de población del DANE
CREATE TABLE IF NOT EXISTS raw.dane_poblacion (
    id_raw          BIGSERIAL PRIMARY KEY,
    archivo         TEXT NOT NULL,
    contenido       JSONB NOT NULL,      -- fila completa tal como llega
    url_origen      TEXT,
    fecha_extraccion TIMESTAMPTZ NOT NULL DEFAULT now(),
    hash_fila       TEXT NOT NULL
);

-- raw.victimas_hechos: hechos victimizantes de Datos Paz / Unidad de Víctimas
CREATE TABLE IF NOT EXISTS raw.victimas_hechos (
    id_raw          BIGSERIAL PRIMARY KEY,
    archivo         TEXT NOT NULL,
    contenido       JSONB NOT NULL,
    url_origen      TEXT,
    fecha_extraccion TIMESTAMPTZ NOT NULL DEFAULT now(),
    hash_fila       TEXT NOT NULL
);

-- raw.art_pdet: proyectos PDET de la Agencia de Renovación del Territorio
CREATE TABLE IF NOT EXISTS raw.art_pdet (
    id_raw          BIGSERIAL PRIMARY KEY,
    archivo         TEXT NOT NULL,
    contenido       JSONB NOT NULL,
    url_origen      TEXT,
    fecha_extraccion TIMESTAMPTZ NOT NULL DEFAULT now(),
    hash_fila       TEXT NOT NULL
);
