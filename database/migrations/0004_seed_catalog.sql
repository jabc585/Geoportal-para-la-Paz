-- ============================================================
-- Migración 0004: Catálogo semilla (fuentes + indicadores piloto)
-- y constraint de deduplicación en serie_historica.
-- ============================================================

-- Deduplicación por (indicador, territorio, periodo, fuente): misma fuente y
-- mismo periodo no deben duplicar la serie (hash_registro para detectar cambios).
CREATE UNIQUE INDEX IF NOT EXISTS uq_serie_dedup
    ON curated.serie_historica (indicador_id, municipio_id, departamento_id, periodo_inicio, periodo_fin, fuente_id);

-- --- Fuentes piloto (sección 21, paso 4) ---
INSERT INTO curated.fuentes
    (codigo, nombre, entidad, tipo, descripcion, url_base, metodo_acceso, periodicidad, formato, licencia, ficha_doc, activa)
VALUES
    ('dane', 'DANE', 'Departamento Administrativo Nacional de Estadística', 'nacional',
     'Población, pobreza, empleo, educación (sección 5 del plan)',
     'https://www.dane.gov.co/', 'descarga', 'anual', 'XLSX',
     'CC BY 4.0 (Datos Abiertos Colombia, verificar)', 'docs/fuentes/dane.md', TRUE),
    ('victimas', 'Unidad para las Víctimas', 'Unidad Administrativa Especial para la Atención y Reparación a las Víctimas', 'nacional',
     'Víctimas, desplazamiento, retornos, reparación (sección 5)',
     'https://datospaz.unidadvictimas.gov.co/', 'api', 'trimestral', 'JSON',
     'Verificar en ficha (sección 3, punto 5)', 'docs/fuentes/victimas.md', TRUE),
    ('art_pdet', 'Agencia de Renovación del Territorio', 'ART', 'nacional',
     'PDET, obras, proyectos (sección 5)',
     'https://www.renovacionterritorio.gov.co/', 'descarga', 'mensual', 'JSON/CSV',
     'Verificar en ficha (sección 3, punto 5)', 'docs/fuentes/art.md', TRUE),
    ('banco_mundial', 'Banco Mundial', 'World Bank Open Data', 'internacional',
     'PIB, pobreza, indicadores sociales y de desarrollo (sección 5.2)',
     'https://data.worldbank.org/', 'api', 'anual', 'JSON',
     'Open Data (CC BY 4.0)', 'docs/fuentes/internacional.md', TRUE);

-- --- Indicadores piloto ---
INSERT INTO curated.indicadores
    (codigo, nombre, descripcion, unidad, granularidad_min, periodicidad, metodologia_doc, activo)
VALUES
    ('poblacion', 'Población', 'Proyecciones de población por municipio', 'personas', 'municipio', 'anual', 'docs/metodologia/indicadores.md', TRUE),
    ('victimas_ruv', 'Personas incluidas en el Registro Único de Víctimas (RUV)', 'Sujetos de atención (per_sa): personas incluidas en el RUV, acumulado a corte, agregadas por municipio/año (sin PII). Fuente: UARIV vía datos.gov.co (dataset municipal de hechos victimizantes)', 'personas', 'municipio', 'anual', 'docs/metodologia/indicadores.md', TRUE),
    ('pdet_inversion', 'Inversión PDET', 'Inversión en proyectos PDET por municipio/año', 'COP', 'municipio', 'mensual', 'docs/metodologia/indicadores.md', TRUE);

-- --- Indicadores internacionales de la capa de comparabilidad (sección 5.2) ---
INSERT INTO curated.indicadores
    (codigo, nombre, descripcion, unidad, granularidad_min, periodicidad, metodologia_doc, activo)
VALUES
    ('pib_pc_ppp', 'PIB per cápita (PPA)', 'PIB per cápita en paridad de poder adquisitivo (Banco Mundial)', 'USD PPA', 'pais', 'anual', 'docs/metodologia/indicadores.md', TRUE),
    ('indice_gini', 'Índice de Gini', 'Desigualdad de ingresos (Banco Mundial)', 'índice', 'pais', 'anual', 'docs/metodologia/indicadores.md', TRUE);
