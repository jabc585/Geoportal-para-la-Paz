# Operaciones — Observatorio para la Paz

Documento operativo. Comandos de backup, restore y re-derivación de datos.

---

## Backup de la base de datos

```bash
pg_dump -U observatorio -h localhost -d observatorio \
  --format=custom --file=backups/observatorio_$(date +%Y%m%d).dump
```

**Tiempo estimado**: <30 s con 157K filas en `serie_historica`.

## Restore desde backup

```bash
# BD limpia (pierde los datos actuales):
psql -U observatorio -d observatorio -c "DROP SCHEMA IF EXISTS raw, staging, curated CASCADE;"
psql -U observatorio -d observatorio -f database/schema.sql
for f in database/migrations/*.sql; do
  psql -U observatorio -d observatorio -v ON_ERROR_STOP=1 -f "$f"
done
pg_restore -U observatorio -h localhost -d observatorio --clean backups/observatorio_YYYYMMDD.dump
```

## Re-derivación desde fuentes (sin backup)

Si no hay backup disponible, los datos se re-derivan completamente de las fuentes
oficiales. **RPO = 0** (nada se pierde porque todo es re-derivable).

```bash
# Recrear BD desde cero y sembrar catálogos:
psql -U observatorio -d observatorio -f database/schema.sql
for f in database/migrations/*.sql; do
  psql -U observatorio -d observatorio -v ON_ERROR_STOP=1 -f "$f"
done
.venv/bin/python -m etl.common.divipola       # catálogo DIVIPOLA (~30 s)
.venv/bin/python -m etl.common.capas_geo      # capa geo municipal (~60 s)
.venv/bin/python -m etl.run_all               # 18 pipelines (~7 min)
```

**Tiempo total de re-derivación**: ~9 minutos (dominado por descargas externas).

## Verificación post-restore

```bash
.venv/bin/python -m pytest tests/ -q          # debe pasar 146 tests
psql -U observatorio -d observatorio -c \
  "SELECT count(*) FROM curated.serie_historica;"  # debe ser > 0
.venv/bin/python -m etl.estado                 # sin fallidos
```

## Pool de conexiones

La API usa `psycopg-pool` (configurado en `api/db.py`). Tamaño por defecto: min 1, max 10.
Si `max_connections` de PostgreSQL es 100, el pool puede manejar hasta 10 requests
concurrentes sin agotar conexiones.
