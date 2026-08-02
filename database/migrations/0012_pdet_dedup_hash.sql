-- Deduplicación de proyectos PDET por hash_registro (hallazgo 2026-08-02).
-- ON CONFLICT DO NOTHING sin columna solo usaba la PK serial proyecto_id, que
-- nunca colisiona: cada corrida del pipeline duplicaba los 965 proyectos.
-- Se limpian los duplicados existentes (se conserva el más reciente) y se fija
-- la unicidad por hash_registro para que el ON CONFLICT sea efectivo.

DELETE FROM curated.pdet_proyectos a
USING curated.pdet_proyectos b
WHERE a.hash_registro = b.hash_registro
  AND a.proyecto_id > b.proyecto_id;

CREATE UNIQUE INDEX IF NOT EXISTS uq_pdet_proyectos_hash
    ON curated.pdet_proyectos (hash_registro);
