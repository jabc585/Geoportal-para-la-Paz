-- ============================================================
-- Migración 0006: columna codigo en curated.fuentes (hallazgo de auditoría)
-- Idempotente: aplica también sobre BD creadas con la versión anterior de
-- schema.sql (la vista vw_homicidios_reconciliado referenciaba f.codigo
-- sin que la columna existiera).
-- ============================================================

ALTER TABLE curated.fuentes ADD COLUMN IF NOT EXISTS codigo TEXT;

-- Poblado para BD existentes (los slug deben coincidir con los de 0004_seed_catalog)
UPDATE curated.fuentes SET codigo = 'dane'
    WHERE nombre = 'DANE' AND (codigo IS NULL OR codigo = '');
UPDATE curated.fuentes SET codigo = 'victimas'
    WHERE nombre = 'Unidad para las Víctimas' AND (codigo IS NULL OR codigo = '');
UPDATE curated.fuentes SET codigo = 'art_pdet'
    WHERE nombre = 'Agencia de Renovación del Territorio' AND (codigo IS NULL OR codigo = '');
UPDATE curated.fuentes SET codigo = 'banco_mundial'
    WHERE nombre = 'Banco Mundial' AND (codigo IS NULL OR codigo = '');

-- Se requiere codigo para toda fuente; si quedara alguna sin slug se marca como pendiente
UPDATE curated.fuentes SET codigo = 'pendiente_' || fuente_id
    WHERE codigo IS NULL OR codigo = '';

-- Vista de reconciliación corregida (sección 7.5): usa f.codigo con los slugs
-- 'medicina_legal' y 'policia'. Las fuentes de homicidios se dan de alta con
-- esos slugs al integrarse (Policía Nacional, Medicina Legal).
CREATE OR REPLACE VIEW curated.vw_homicidios_reconciliado AS
SELECT
    s.municipio_id,
    m.nombre  AS municipio,
    d.nombre  AS departamento,
    date_trunc('year', s.periodo_inicio)::date AS anio,
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
