-- 0017: el índice de deduplicación de serie_historica no protegía las series
-- departamentales.
--
-- Problema (detectado ejecutando la app, 2026-08-03):
--   `uq_serie_dedup` es UNIQUE sobre
--   (indicador_id, municipio_id, departamento_id, periodo_inicio, periodo_fin, fuente_id).
--   En un índice único normal, PostgreSQL considera **cada NULL distinto de
--   cualquier otro**, así que dos filas (10, NULL, 18, '2025-01-01', …) no
--   conflictúan nunca. Las series municipales llevan municipio_id y
--   departamento_id a la vez (156.944 filas) y sí estaban protegidas; las
--   **departamentales** llevan municipio_id NULL (1.770 filas) y no lo estaban.
--
--   Consecuencia medida: cada corrida del ETL reinsertaba las 295 filas de cada
--   indicador ACLED departamental. Con tres corridas acumuladas, la API
--   respondía **16.716 eventos ACLED en 2025 cuando la cifra real es 5.572** —
--   inflada exactamente ×3, y creciendo con cada ejecución. El `ON CONFLICT` de
--   insertar_serie() estaba bien escrito; el índice que debía dispararlo no
--   cubría el caso.
--
-- Corrección: NULLS NOT DISTINCT (PostgreSQL ≥ 15), que hace que dos NULL
-- cuenten como iguales a efectos de unicidad. Es la semántica que el índice
-- pretendía tener desde el principio.

-- Paso 1: conservar una sola fila por clave lógica. Se queda la de serie_id
-- mayor —la más reciente—, coherente con el ON CONFLICT DO UPDATE que ya
-- prefiere el último valor publicado por la fuente.
DELETE FROM curated.serie_historica s
USING (
    SELECT serie_id,
           row_number() OVER (
               PARTITION BY indicador_id, municipio_id, departamento_id,
                            periodo_inicio, periodo_fin, fuente_id
               ORDER BY serie_id DESC
           ) AS rn
    FROM curated.serie_historica
) d
WHERE s.serie_id = d.serie_id AND d.rn > 1;

-- Paso 2: reemplazar el índice por su versión con NULLS NOT DISTINCT.
DROP INDEX IF EXISTS curated.uq_serie_dedup;

CREATE UNIQUE INDEX IF NOT EXISTS uq_serie_dedup
    ON curated.serie_historica (
        indicador_id, municipio_id, departamento_id,
        periodo_inicio, periodo_fin, fuente_id
    ) NULLS NOT DISTINCT;

COMMENT ON INDEX curated.uq_serie_dedup IS
  'Clave lógica de la serie. NULLS NOT DISTINCT: sin ello las series '
  'departamentales (municipio_id NULL) se reinsertaban en cada corrida.';
