-- Privilegios reales para los roles etl/api (auditoría 2026-08-02).
-- Antes: schema.sql creaba roles NOLOGIN con solo USAGE ON SCHEMA y ninguna
-- conexión los usaba ("security theater"). Ahora:
--   - rol etl: LOGIN, escribe en raw/staging/curated (INSERT/SELECT/UPDATE/DELETE)
--   - rol api: LOGIN, solo SELECT en curated (mínimo privilegio, API de solo lectura)
-- Las contraseñas son de desarrollo (patrón existente observatorio_dev); en
-- producción se rotan con ALTER ROLE ... PASSWORD fuera de migraciones.

ALTER ROLE etl LOGIN;
ALTER ROLE api LOGIN;

ALTER ROLE etl PASSWORD 'etl_dev';
ALTER ROLE api PASSWORD 'api_dev';

-- etl: escribe en las tres capas (pipeline completo + seeds).
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA raw TO etl;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA staging TO etl;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA curated TO etl;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA raw TO etl;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA staging TO etl;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA curated TO etl;

-- api: solo lectura de datos publicados.
GRANT SELECT ON ALL TABLES IN SCHEMA curated TO api;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA curated TO api;

-- Tablas/sequencias futuras: heredan el mismo régimen.
ALTER DEFAULT PRIVILEGES IN SCHEMA raw GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO etl;
ALTER DEFAULT PRIVILEGES IN SCHEMA staging GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO etl;
ALTER DEFAULT PRIVILEGES IN SCHEMA curated GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO etl;
ALTER DEFAULT PRIVILEGES IN SCHEMA raw GRANT USAGE, SELECT ON SEQUENCES TO etl;
ALTER DEFAULT PRIVILEGES IN SCHEMA staging GRANT USAGE, SELECT ON SEQUENCES TO etl;
ALTER DEFAULT PRIVILEGES IN SCHEMA curated GRANT USAGE, SELECT ON SEQUENCES TO etl;
ALTER DEFAULT PRIVILEGES IN SCHEMA curated GRANT SELECT ON TABLES TO api;
