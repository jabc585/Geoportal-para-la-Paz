-- ============================================================
-- Migración 0009: capas raw para fuentes de Fase B (plan2.md)
-- Tablas crudas de los pipelines nuevos: CNMH SIEVCAC (una por
-- tipo de hecho), UNHCR, Fiscalía V3, Policía. Incluye también
-- raw.internacional_worldbank, que el pipeline World Bank ya
-- existente necesita pero nunca se había creado (gap de auditoría).
-- ============================================================

CREATE TABLE IF NOT EXISTS raw.internacional_worldbank (
    id_raw           BIGSERIAL PRIMARY KEY,
    archivo          TEXT NOT NULL,
    contenido        JSONB NOT NULL,
    url_origen       TEXT,
    fecha_extraccion TIMESTAMPTZ NOT NULL DEFAULT now(),
    hash_fila        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.internacional_unhcr (
    id_raw           BIGSERIAL PRIMARY KEY,
    archivo          TEXT NOT NULL,
    contenido        JSONB NOT NULL,
    url_origen       TEXT,
    fecha_extraccion TIMESTAMPTZ NOT NULL DEFAULT now(),
    hash_fila        TEXT NOT NULL
);

-- CNMH SIEVCAC: una tabla por tipo de hecho (minas, atentados,
-- desaparición, bienes, reclutamiento, acciones bélicas)
CREATE TABLE IF NOT EXISTS raw.cnmh_minas (
    id_raw           BIGSERIAL PRIMARY KEY,
    archivo          TEXT NOT NULL,
    contenido        JSONB NOT NULL,
    url_origen       TEXT,
    fecha_extraccion TIMESTAMPTZ NOT NULL DEFAULT now(),
    hash_fila        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.cnmh_atentados (
    id_raw           BIGSERIAL PRIMARY KEY,
    archivo          TEXT NOT NULL,
    contenido        JSONB NOT NULL,
    url_origen       TEXT,
    fecha_extraccion TIMESTAMPTZ NOT NULL DEFAULT now(),
    hash_fila        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.cnmh_desaparicion (
    id_raw           BIGSERIAL PRIMARY KEY,
    archivo          TEXT NOT NULL,
    contenido        JSONB NOT NULL,
    url_origen       TEXT,
    fecha_extraccion TIMESTAMPTZ NOT NULL DEFAULT now(),
    hash_fila        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.cnmh_bienes (
    id_raw           BIGSERIAL PRIMARY KEY,
    archivo          TEXT NOT NULL,
    contenido        JSONB NOT NULL,
    url_origen       TEXT,
    fecha_extraccion TIMESTAMPTZ NOT NULL DEFAULT now(),
    hash_fila        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.cnmh_reclutamiento (
    id_raw           BIGSERIAL PRIMARY KEY,
    archivo          TEXT NOT NULL,
    contenido        JSONB NOT NULL,
    url_origen       TEXT,
    fecha_extraccion TIMESTAMPTZ NOT NULL DEFAULT now(),
    hash_fila        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.cnmh_acciones (
    id_raw           BIGSERIAL PRIMARY KEY,
    archivo          TEXT NOT NULL,
    contenido        JSONB NOT NULL,
    url_origen       TEXT,
    fecha_extraccion TIMESTAMPTZ NOT NULL DEFAULT now(),
    hash_fila        TEXT NOT NULL
);

-- Fiscalía V3 (procesos y víctimas) y Policía (por delito)
CREATE TABLE IF NOT EXISTS raw.fiscalia_procesos (
    id_raw           BIGSERIAL PRIMARY KEY,
    archivo          TEXT NOT NULL,
    contenido        JSONB NOT NULL,
    url_origen       TEXT,
    fecha_extraccion TIMESTAMPTZ NOT NULL DEFAULT now(),
    hash_fila        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.fiscalia_victimas (
    id_raw           BIGSERIAL PRIMARY KEY,
    archivo          TEXT NOT NULL,
    contenido        JSONB NOT NULL,
    url_origen       TEXT,
    fecha_extraccion TIMESTAMPTZ NOT NULL DEFAULT now(),
    hash_fila        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.policia_hurto (
    id_raw           BIGSERIAL PRIMARY KEY,
    archivo          TEXT NOT NULL,
    contenido        JSONB NOT NULL,
    url_origen       TEXT,
    fecha_extraccion TIMESTAMPTZ NOT NULL DEFAULT now(),
    hash_fila        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.policia_violencia (
    id_raw           BIGSERIAL PRIMARY KEY,
    archivo          TEXT NOT NULL,
    contenido        JSONB NOT NULL,
    url_origen       TEXT,
    fecha_extraccion TIMESTAMPTZ NOT NULL DEFAULT now(),
    hash_fila        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.policia_sexuales (
    id_raw           BIGSERIAL PRIMARY KEY,
    archivo          TEXT NOT NULL,
    contenido        JSONB NOT NULL,
    url_origen       TEXT,
    fecha_extraccion TIMESTAMPTZ NOT NULL DEFAULT now(),
    hash_fila        TEXT NOT NULL
);

-- ACLED: agregados país-año descargados a data/external (2026-08-02, sin API key)
CREATE TABLE IF NOT EXISTS raw.internacional_acled (
    id_raw           BIGSERIAL PRIMARY KEY,
    archivo          TEXT NOT NULL,
    contenido        JSONB NOT NULL,
    url_origen       TEXT,
    fecha_extraccion TIMESTAMPTZ NOT NULL DEFAULT now(),
    hash_fila        TEXT NOT NULL
);

-- HDX: CSV firmado de Conflict Events (hdx-hapi-col), fila por evento mensual
CREATE TABLE IF NOT EXISTS raw.internacional_hdx (
    id_raw           BIGSERIAL PRIMARY KEY,
    archivo          TEXT NOT NULL,
    contenido        JSONB NOT NULL,
    url_origen       TEXT,
    fecha_extraccion TIMESTAMPTZ NOT NULL DEFAULT now(),
    hash_fila        TEXT NOT NULL
);
