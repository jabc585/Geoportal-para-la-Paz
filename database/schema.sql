-- ============================================================
-- Observatorio para la Paz en Colombia
-- Esquema base: raw / staging / curated (sección 7.3 del plan)
-- Separación end-to-end: archivo -> esquema -> consumo
--
-- raw     : solo el proceso ETL escribe; datos inmutables tal como se descargan
-- staging : datos normalizados, validables, limpiables sin afectar lo publicado
-- curated : datos listos para consumo de API y dashboard (solo lectura para API)
--
-- Permisos: rol `etl` escribe en raw/staging/curated; rol `api` solo lee curated.
-- Los GRANT reales a nivel de tabla y el LOGIN se aplican en la migración
-- 0013_privilegios_reales.sql (auditoría 2026-08-02).
-- ============================================================

-- PostGIS: requerido por capa_contexto_territorial (sección 5.1).
-- Idempotente: en la imagen postgis/postgis ya está disponible, solo se activa.
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS curated;

COMMENT ON SCHEMA raw IS 'Datos crudos, inmutables, tal como se descargan de la fuente (sección 7.3).';
COMMENT ON SCHEMA staging IS 'Datos normalizados y validados antes de promoción a curated (sección 7.3).';
COMMENT ON SCHEMA curated IS 'Datos publicables para API y dashboard; linaje completo conservado (sección 7.3).';

-- Roles con privilegios mínimos (sección 7.3 y 13)
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'etl') THEN
    CREATE ROLE etl NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'api') THEN
    CREATE ROLE api NOLOGIN;
  END IF;
END
$$;

GRANT USAGE ON SCHEMA raw TO etl;
GRANT USAGE ON SCHEMA staging TO etl, api;
GRANT USAGE ON SCHEMA curated TO etl, api;

-- ============================================================
-- Catálogo de fuentes (sección 7: entidad Fuente)
-- Incluye fuentes nacionales e internacionales.
-- ============================================================
CREATE TABLE curated.fuentes (
    fuente_id          SERIAL PRIMARY KEY,
    codigo             TEXT NOT NULL UNIQUE,   -- slug estable: 'dane', 'medicina_legal', 'policia', 'banco_mundial'
    nombre             TEXT NOT NULL UNIQUE,
    entidad            TEXT NOT NULL,
    tipo               TEXT NOT NULL CHECK (tipo IN ('nacional', 'internacional')),
    descripcion        TEXT,
    url_base           TEXT,
    metodo_acceso      TEXT NOT NULL CHECK (metodo_acceso IN ('api', 'descarga', 'scraping_autorizado')),
    periodicidad       TEXT NOT NULL,
    formato            TEXT NOT NULL,
    licencia           TEXT NOT NULL,
    ficha_doc          TEXT,                -- ruta a docs/fuentes/<fuente>.md
    responsable        TEXT,
    activa             BOOLEAN NOT NULL DEFAULT TRUE,
    ultima_actualizacion TIMESTAMPTZ,
    creado_en          TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE curated.fuentes IS 'Catálogo de fuentes con licencia, URL y última actualización (sección 7). La licencia se verifica fuente por fuente antes de integrarla (sección 3, punto 5).';

-- ============================================================
-- Dimensiones territoriales con versionado SCD tipo 2 (sección 7.2)
-- ============================================================
CREATE TABLE curated.departamento (
    departamento_id SERIAL PRIMARY KEY,
    codigo_divipola CHAR(2) NOT NULL UNIQUE,
    nombre          TEXT NOT NULL,
    valido_desde    DATE NOT NULL DEFAULT CURRENT_DATE,
    valido_hasta    DATE,                    -- NULL = vigente
    vigente         BOOLEAN GENERATED ALWAYS AS (valido_hasta IS NULL) STORED
);

CREATE TABLE curated.municipio (
    municipio_id    SERIAL PRIMARY KEY,
    codigo_divipola CHAR(5) NOT NULL,
    nombre          TEXT NOT NULL,
    departamento_id INTEGER NOT NULL REFERENCES curated.departamento (departamento_id),
    -- SCD tipo 2: un municipio puede aparecer varias veces si cambia de código/nombre
    valido_desde    DATE NOT NULL DEFAULT CURRENT_DATE,
    valido_hasta    DATE,
    vigente         BOOLEAN GENERATED ALWAYS AS (valido_hasta IS NULL) STORED,
    UNIQUE (codigo_divipola, valido_desde)
);

CREATE TABLE curated.vereda (
    vereda_id      SERIAL PRIMARY KEY,
    codigo_vereda  TEXT,
    nombre         TEXT NOT NULL,
    municipio_id   INTEGER REFERENCES curated.municipio (municipio_id),
    valido_desde   DATE NOT NULL DEFAULT CURRENT_DATE,
    valido_hasta   DATE,
    vigente        BOOLEAN GENERATED ALWAYS AS (valido_hasta IS NULL) STORED,
    UNIQUE (codigo_vereda, valido_desde)
);

COMMENT ON TABLE curated.municipio IS 'Dimensión de cambio lento (SCD tipo 2): conserva histórico ante creación de municipios o cambios de código DIVIPOLA (sección 7.2).';

-- ============================================================
-- Capas de contexto territorial (sección 5.1)
-- No son indicadores de conflicto; dan marco de interpretación.
-- ============================================================
CREATE TABLE curated.capa_contexto_territorial (
    capa_id        SERIAL PRIMARY KEY,
    tipo           TEXT NOT NULL CHECK (tipo IN ('resguardo_indigena', 'territorio_colectivo', 'zona_reserva_campesina', 'divipola')),
    nombre         TEXT NOT NULL,
    geometria      GEOMETRY(Geometry, 4326) NOT NULL,
    fuente_id      INTEGER REFERENCES curated.fuentes (fuente_id),
    url_origen     TEXT,
    valido_desde   DATE NOT NULL DEFAULT CURRENT_DATE,
    valido_hasta   DATE,
    vigente        BOOLEAN GENERATED ALWAYS AS (valido_hasta IS NULL) STORED
);

-- ============================================================
-- Catálogo de indicadores (sección 7: entidad Indicador)
-- ============================================================
CREATE TABLE curated.indicadores (
    indicador_id       SERIAL PRIMARY KEY,
    codigo             TEXT NOT NULL UNIQUE,       -- p. ej. 'homicidios', 'victimas_desplazamiento'
    nombre             TEXT NOT NULL,
    descripcion        TEXT,
    unidad             TEXT NOT NULL,
    granularidad_min   TEXT NOT NULL CHECK (granularidad_min IN ('municipio', 'departamento', 'pais')),
    fuente_primaria_id INTEGER REFERENCES curated.fuentes (fuente_id),
    periodicidad       TEXT NOT NULL,
    metodologia_doc    TEXT,                        -- ruta a docs/metodologia/
    limites_conocidos  TEXT,
    aprobado_comite    BOOLEAN NOT NULL DEFAULT FALSE,  -- sección 3, punto 6
    activo             BOOLEAN NOT NULL DEFAULT TRUE
);

-- ============================================================
-- Hechos (SerieHistorica): tabla genérica de hechos (sección 7)
-- Granularidad temporal flexible: periodo_inicio/fin (sección 7.1)
-- ============================================================
CREATE TABLE curated.serie_historica (
    serie_id        BIGSERIAL PRIMARY KEY,
    indicador_id    INTEGER NOT NULL REFERENCES curated.indicadores (indicador_id),
    municipio_id    INTEGER REFERENCES curated.municipio (municipio_id),
    departamento_id INTEGER REFERENCES curated.departamento (departamento_id),
    periodo_inicio  DATE NOT NULL,
    periodo_fin     DATE NOT NULL,
    valor           NUMERIC NOT NULL,
    -- Linaje obligatorio (sección 3, punto 4 y sección 7)
    fuente_id       INTEGER NOT NULL REFERENCES curated.fuentes (fuente_id),
    url_origen      TEXT,
    fecha_extraccion TIMESTAMPTZ NOT NULL,
    fecha_corte_dato DATE,
    hash_registro   TEXT NOT NULL,               -- detección de cambios/duplicados
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (periodo_fin >= periodo_inicio)
);

CREATE INDEX idx_serie_indicador_periodo ON curated.serie_historica (indicador_id, periodo_inicio DESC);
CREATE INDEX idx_serie_municipio ON curated.serie_historica (municipio_id);
CREATE INDEX idx_serie_hash ON curated.serie_historica (hash_registro);

COMMENT ON TABLE curated.serie_historica IS 'Hechos genéricos: indicador, territorio, periodo, valor, fuente (sección 7). La granularidad temporal se conserva (mes/año) y la de exposición se decide contra el checklist de privacidad (sección 3.1).';

-- ============================================================
-- Indicadores internacionales (secciones 5.2 y 7.6)
-- Deliberadamente separados de serie_historica: solo a nivel país.
-- ============================================================
CREATE TABLE curated.indicador_internacional (
    indicador_int_id BIGSERIAL PRIMARY KEY,
    fuente_id        INTEGER NOT NULL REFERENCES curated.fuentes (fuente_id),
    pais             TEXT NOT NULL DEFAULT 'Colombia',
    indicador        TEXT NOT NULL,           -- p. ej. 'PIB per cápita (US$ actuales)'
    periodo          DATE NOT NULL,
    valor            NUMERIC NOT NULL,
    unidad           TEXT,
    url_origen       TEXT,
    fecha_extraccion TIMESTAMPTZ NOT NULL,
    fecha_corte_dato DATE,
    hash_registro    TEXT NOT NULL,
    UNIQUE (fuente_id, pais, indicador, periodo)
);

CREATE INDEX idx_ind_int_fuente_periodo ON curated.indicador_internacional (fuente_id, periodo DESC);

COMMENT ON TABLE curated.indicador_internacional IS 'Indicadores de fuentes globales a nivel país/región (sección 7.6). No se combina con cifras municipales en el dashboard: solo se unen por país/año (sección 5.2).';

-- ============================================================
-- Vista unificada de fuentes divergentes (sección 7.5)
-- Ejemplo: homicidios según Policía Nacional vs. Medicina Legal.
-- ============================================================
CREATE OR REPLACE VIEW curated.vw_homicidios_reconciliado AS
SELECT
    s.municipio_id,
    m.nombre  AS municipio,
    d.nombre  AS departamento,
    date_trunc('year', s.periodo_inicio)::date AS anio,
    -- Valor de referencia según criterio metodológico público (p. ej. Medicina Legal)
    MAX(s.valor) FILTER (WHERE f.codigo = 'medicina_legal') AS homicidios_referencia,
    MAX(s.valor) FILTER (WHERE f.codigo = 'policia')        AS homicidios_policia,
    MAX(s.valor) FILTER (WHERE f.codigo = 'medicina_legal') AS homicidios_medicinalegal,
    STRING_AGG(DISTINCT f.nombre, ', ') AS fuentes
FROM curated.serie_historica s
JOIN curated.indicadores i  ON i.indicador_id = s.indicador_id
JOIN curated.fuentes f      ON f.fuente_id = s.fuente_id
LEFT JOIN curated.municipio m ON m.municipio_id = s.municipio_id
LEFT JOIN curated.departamento d ON d.departamento_id = s.departamento_id
WHERE i.codigo = 'homicidios'
GROUP BY s.municipio_id, m.nombre, d.nombre, date_trunc('year', s.periodo_inicio)::date;

COMMENT ON VIEW curated.vw_homicidios_reconciliado IS 'Vista unificada de reconciliación (sección 7.5): muestra ambas cifras originales y el valor de referencia, sin ocultar la discrepancia.';
