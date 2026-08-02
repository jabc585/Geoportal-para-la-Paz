-- ============================================================
-- Migración 0003: Índices geográficos y funciones utilitarias
-- ============================================================

-- Índice espacial sobre capas de contexto (sección 5.1)
CREATE INDEX idx_capa_contexto_geometria ON curated.capa_contexto_territorial USING GIST (geometria);

-- Función: marcar versión SCD como cerrada (sección 7.2)
CREATE OR REPLACE FUNCTION curated.cerrar_version_scd(
    _tabla TEXT,
    _id_col TEXT,
    _id BIGINT,
    _valido_hasta DATE
) RETURNS VOID AS $$
BEGIN
    EXECUTE format(
        'UPDATE curated.%I SET valido_hasta = %L WHERE %I = %L AND valido_hasta IS NULL',
        _tabla, _valido_hasta, _id_col, _id
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION curated.cerrar_version_scd IS 'Cierra la versión vigente de una dimensión SCD tipo 2 (sección 7.2).';
