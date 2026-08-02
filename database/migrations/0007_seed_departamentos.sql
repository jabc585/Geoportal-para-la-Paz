-- ============================================================
-- Migración 0007: Seed de departamentos DIVIPOLA (sección 5.1 y 7.2)
-- Los municipios se siembran con `python -m etl.common.divipola`
-- (dataset oficial de datos.gov.co); aquí quedan garantizados los
-- 33 departamentos incluso sin red.
-- ============================================================

INSERT INTO curated.departamento (codigo_divipola, nombre, valido_desde)
VALUES
    ('05', 'ANTIOQUIA', CURRENT_DATE),
    ('08', 'ATLÁNTICO', CURRENT_DATE),
    ('11', 'BOGOTÁ, D.C.', CURRENT_DATE),
    ('13', 'BOLÍVAR', CURRENT_DATE),
    ('15', 'BOYACÁ', CURRENT_DATE),
    ('17', 'CALDAS', CURRENT_DATE),
    ('18', 'CAQUETÁ', CURRENT_DATE),
    ('19', 'CAUCA', CURRENT_DATE),
    ('20', 'CESAR', CURRENT_DATE),
    ('23', 'CÓRDOBA', CURRENT_DATE),
    ('25', 'CUNDINAMARCA', CURRENT_DATE),
    ('27', 'CHOCÓ', CURRENT_DATE),
    ('41', 'HUILA', CURRENT_DATE),
    ('44', 'LA GUAJIRA', CURRENT_DATE),
    ('47', 'MAGDALENA', CURRENT_DATE),
    ('50', 'META', CURRENT_DATE),
    ('52', 'NARIÑO', CURRENT_DATE),
    ('54', 'NORTE DE SANTANDER', CURRENT_DATE),
    ('63', 'QUINDÍO', CURRENT_DATE),
    ('66', 'RISARALDA', CURRENT_DATE),
    ('68', 'SANTANDER', CURRENT_DATE),
    ('70', 'SUCRE', CURRENT_DATE),
    ('73', 'TOLIMA', CURRENT_DATE),
    ('76', 'VALLE DEL CAUCA', CURRENT_DATE),
    ('81', 'ARAUCA', CURRENT_DATE),
    ('85', 'CASANARE', CURRENT_DATE),
    ('86', 'PUTUMAYO', CURRENT_DATE),
    ('88', 'SAN ANDRÉS Y PROVIDENCIA', CURRENT_DATE),
    ('91', 'AMAZONAS', CURRENT_DATE),
    ('94', 'GUAINÍA', CURRENT_DATE),
    ('95', 'GUAVIARE', CURRENT_DATE),
    ('97', 'VAUPÉS', CURRENT_DATE),
    ('99', 'VICHADA', CURRENT_DATE)
ON CONFLICT (codigo_divipola) DO NOTHING;
