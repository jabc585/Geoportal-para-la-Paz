-- 0016: deduplicación de raw.* por contenido.
--
-- Problema que corrige (auditoría 2026-08-03, §2.7 de auditoria_completa.md):
--   insertar_raw() hacía un INSERT plano sin restricción de unicidad, así que
--   cada corrida reescribía el snapshot ENTERO, idéntico. Medido antes de esta
--   migración: raw.dane_poblacion con 215.424 filas y solo 53.856 hashes
--   únicos (cuatro copias byte a byte del mismo extracto, todas del mismo día);
--   el esquema raw completo pesaba 1.973 MB tras las corridas de un solo día.
--   Con el cron diario de .github/workflows/etl-programado.yml, ese crecimiento
--   pasa a ser de ~200-300 GB al año casi enteramente duplicados.
--
-- Diseño: clave de unicidad (hash_fila, ocurrencia).
--   `hash_fila` ya existía y es sha256 del contenido de la fila (lineage.py);
--   se guardaba pero no se usaba para nada.
--   `ocurrencia` es el índice de repetición del MISMO contenido dentro de un
--   mismo snapshot. Sin ella, un UNIQUE(hash_fila) a secas perdería filas
--   legítimamente repetidas en el origen: raw.internacional_hdx queda con
--   346.698 filas y 346.398 hashes distintos, es decir 300 filas duplicadas que
--   SÍ vienen así de la fuente y que el espejo debe conservar (26 de ellas en un
--   solo archivo). Medido antes de elegir el diseño, no supuesto.
--
-- Semántica resultante: raw sigue siendo un espejo inmutable y acumulativo,
-- pero acumula CONTENIDO NUEVO en vez de copias. Si la fuente corrige una fila,
-- su hash cambia y entra como registro nuevo; la versión anterior permanece.

-- La deduplicación y el índice se aplican a todas las tablas de raw.* mediante
-- un recorrido del catálogo: son 20 tablas creadas en 0001/0009/0010/0011 y
-- todas comparten la misma forma (archivo, contenido, url_origen,
-- fecha_extraccion, hash_fila). Cualquier tabla raw que se añada en el futuro
-- debe incluir la columna `ocurrencia` y este índice único.
DO $$
DECLARE
    t TEXT;
    indice TEXT;
    borradas BIGINT;
    total_borradas BIGINT := 0;
BEGIN
    FOR t IN
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'raw'
        ORDER BY tablename
    LOOP
        indice := 'uq_' || t || '_hash_ocurrencia';

        EXECUTE format(
            'ALTER TABLE raw.%I ADD COLUMN IF NOT EXISTS ocurrencia SMALLINT NOT NULL DEFAULT 0', t
        );

        -- La renumeración solo puede correr sobre una tabla aún sin deduplicar.
        -- Reaplicarla después violaría el índice único: tras el paso 2, las
        -- filas supervivientes de un mismo hash pueden venir de snapshots
        -- distintos (una de A con ocurrencia 0, otra de B con ocurrencia 1), y
        -- renumerar por `archivo` devolvería ambas a 0. De ahí el guardia:
        -- la existencia del índice marca que la tabla ya está deduplicada.
        CONTINUE WHEN EXISTS (
            SELECT 1 FROM pg_indexes
            WHERE schemaname = 'raw' AND indexname = indice
        );

        -- Paso 1: numerar cada fila por su repetición dentro de su propio
        -- snapshot (`archivo`), que es la multiplicidad real del origen.
        EXECUTE format($f$
            UPDATE raw.%I d SET ocurrencia = n.ocu
            FROM (
                SELECT id_raw,
                       (row_number() OVER (PARTITION BY archivo, hash_fila
                                           ORDER BY id_raw) - 1)::SMALLINT AS ocu
                FROM raw.%I
            ) n
            WHERE d.id_raw = n.id_raw AND d.ocurrencia IS DISTINCT FROM n.ocu
        $f$, t, t);

        -- Paso 2: de las copias del mismo (contenido, ocurrencia) repetidas
        -- entre snapshots, conservar la más antigua — la fecha de extracción
        -- que interesa es la de la PRIMERA vez que la fuente sirvió ese dato.
        EXECUTE format($f$
            DELETE FROM raw.%I d
            USING (
                SELECT id_raw,
                       row_number() OVER (PARTITION BY hash_fila, ocurrencia
                                          ORDER BY id_raw) AS rn
                FROM raw.%I
            ) r
            WHERE d.id_raw = r.id_raw AND r.rn > 1
        $f$, t, t);
        GET DIAGNOSTICS borradas = ROW_COUNT;
        total_borradas := total_borradas + borradas;

        -- Paso 3: la restricción que impide que vuelva a ocurrir. Es también
        -- el índice que necesita el ON CONFLICT de insertar_raw().
        EXECUTE format(
            'CREATE UNIQUE INDEX IF NOT EXISTS %I ON raw.%I (hash_fila, ocurrencia)',
            'uq_' || t || '_hash_ocurrencia', t
        );

        EXECUTE format(
            'COMMENT ON COLUMN raw.%I.ocurrencia IS %L', t,
            'Índice de repetición del mismo contenido dentro de un snapshot; '
            '(hash_fila, ocurrencia) es la clave de deduplicación entre corridas.'
        );
    END LOOP;

    RAISE NOTICE '0016: % filas duplicadas eliminadas de raw.*', total_borradas;
END $$;
