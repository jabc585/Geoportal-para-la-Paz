-- 0015: frescura de datos y acumulación verificable.
--
-- Problemas que corrige (auditoría 2026-08-03):
--   1. curated.fuentes.ultima_actualizacion existía desde schema.sql pero NINGÚN
--      pipeline la escribía: la API la exponía siempre como NULL.
--   2. No había forma de saber si un dato es reciente o de hace cinco años:
--      `periodicidad` es texto libre ('mensual', 'anual'), no comparable.
--   3. No se registraba cuántas filas se actualizan por revisión de la fuente
--      frente a cuántas son nuevas.

-- Fecha del dato más reciente que aporta la fuente (distinta de la fecha de
-- extracción: una fuente puede consultarse hoy y publicar datos de 2023).
ALTER TABLE curated.fuentes
  ADD COLUMN IF NOT EXISTS fecha_corte_dato DATE;

-- Umbral de obsolescencia en días, derivado de la periodicidad declarada.
-- Permite comparar aritméticamente sin parsear texto en cada consulta.
ALTER TABLE curated.fuentes
  ADD COLUMN IF NOT EXISTS periodicidad_dias INTEGER;

COMMENT ON COLUMN curated.fuentes.fecha_corte_dato IS
  'Periodo más reciente cubierto por los datos de esta fuente (no la fecha de extracción).';
COMMENT ON COLUMN curated.fuentes.periodicidad_dias IS
  'Días esperados entre publicaciones; alimenta el cálculo de frescura.';

-- Derivar periodicidad_dias de la periodicidad textual ya declarada.
UPDATE curated.fuentes SET periodicidad_dias = CASE
    WHEN lower(periodicidad) LIKE '%diar%'     THEN 1
    WHEN lower(periodicidad) LIKE '%semanal%'  THEN 7
    WHEN lower(periodicidad) LIKE '%quincen%'  THEN 15
    WHEN lower(periodicidad) LIKE '%mensual%'  THEN 30
    WHEN lower(periodicidad) LIKE '%trimestr%' THEN 90
    WHEN lower(periodicidad) LIKE '%semestr%'  THEN 180
    WHEN lower(periodicidad) LIKE '%anual%'    THEN 365
    ELSE 365
  END
WHERE periodicidad_dias IS NULL;

-- Vista de frescura: clasifica cada fuente comparando su última extracción
-- contra la periodicidad que ella misma declara.
--   al_dia    : dentro del periodo esperado
--   retrasada : hasta 2x el periodo
--   obsoleta  : más de 2x el periodo
--   sin_datos : nunca se ha cargado
CREATE OR REPLACE VIEW curated.vw_frescura_fuentes AS
SELECT
    f.fuente_id,
    f.codigo,
    f.nombre,
    f.entidad,
    f.periodicidad,
    f.periodicidad_dias,
    f.ultima_actualizacion,
    f.fecha_corte_dato,
    CASE
        WHEN f.ultima_actualizacion IS NULL THEN NULL
        ELSE EXTRACT(DAY FROM (now() - f.ultima_actualizacion))::INTEGER
    END AS dias_desde_extraccion,
    CASE
        WHEN f.ultima_actualizacion IS NULL THEN 'sin_datos'
        WHEN now() - f.ultima_actualizacion
             <= make_interval(days => f.periodicidad_dias)        THEN 'al_dia'
        WHEN now() - f.ultima_actualizacion
             <= make_interval(days => f.periodicidad_dias * 2)    THEN 'retrasada'
        ELSE 'obsoleta'
    END AS frescura
FROM curated.fuentes f
WHERE f.activa;

COMMENT ON VIEW curated.vw_frescura_fuentes IS
  'Estado de frescura por fuente: compara la última extracción contra la periodicidad declarada.';

-- Índice para la consulta de frescura de la API.
CREATE INDEX IF NOT EXISTS idx_fuentes_ultima_actualizacion
  ON curated.fuentes (ultima_actualizacion DESC NULLS LAST);
