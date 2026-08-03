# Runbook de incidentes — Observatorio para la Paz

Documento operativo. Cada escenario describe diagnóstico, comandos y criterio
de escalada. Basado en 4 rondas de auditoría con ejecución end-to-end real.

---

## A. La API no responde (HTTP 5xx o timeout)

**Diagnóstico**:
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health
pg_isready -h localhost -p 5432
```

**Causa más probable**: PostgreSQL caído o sin conexiones disponibles.

**Comandos**:
```bash
brew services restart postgresql@17      # macOS
# o: systemctl restart postgresql         # Linux
.venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 &
```

**Escalar si**: no responde tras reiniciar ambos servicios. Verificar `max_connections` vs el pool (`psycopg_pool` en `api/db.py`).

---

## B. Un pipeline falla en la corrida programada

**Diagnóstico**:
```bash
.venv/bin/python -m etl.estado            # lista fallidos y parciales
psql -U observatorio -d observatorio -c \
  "SELECT pipeline_id, mensaje_error FROM curated.data_quality_metrics
   WHERE estado='fallido' ORDER BY timestamp_ejecucion DESC LIMIT 5;"
```

**Causas frecuentes** (por orden de ocurrencia en 4 rondas):
1. **Fuente oficial cambió de esquema** (nuevo nombre de columna, URL rota).
2. **Variable de entorno faltante** (`.env` incompleto tras deploy).
3. **Límite de Socrata** (>1000 req/hora sin `SOCRATA_APP_TOKEN`).

**Comandos**:
```bash
# Revisar si la fuente sigue respondiendo:
curl -s -o /dev/null -w "%{http_code}" "$(grep POLICIA_HURTO_URL .env | cut -d= -f2)"

# Re-ejecutar el pipeline específico:
.venv/bin/python -m etl.policia.pipeline
```

**Escalar si**: mismo pipeline falla 3 corridas seguidas → investigar la fuente (ver `config/investigacion_fuentes.yaml`).

---

## C. Una fuente oficial cambió de esquema

**Diagnóstico**: el mensaje de error suele mencionar una columna faltante (`KeyError: 'nombre_columna'`) o un código HTTP 404 de la fuente.

**Comandos**:
```bash
# Inspeccionar el shape actual de la fuente:
curl -s "<URL>" | python -m json.tool | head -50   # JSON
curl -s -o /tmp/fuente.xlsx "<URL>"                 # Excel
```

**Acción**: actualizar los `ALIASES` del pipeline correspondiente (buscar `ALIASES` en `etl/*/pipeline.py`) y documentar el cambio en `config/investigacion_fuentes.yaml`. Si el cambio es estructural (nuevos campos, granularidad distinta), actualizar también la ficha en `docs/fuentes/` y el esquema de validación Pandera.

---

## D. Revertir una migración

**Precaución**: las migraciones son acumulativas y solo añaden estructura (nunca destruyen datos). Una reversión se hace con DROP + re-aplicación de las anteriores.

**Comandos**:
```bash
# Listar migraciones aplicadas y su orden:
ls database/migrations/

# Si la migración N es la problemática, recrear desde schema.sql y re-aplicar hasta N-1:
psql -U observatorio -d observatorio -c "DROP SCHEMA raw, staging, curated CASCADE;"
psql -U observatorio -d observatorio -f database/schema.sql
for f in database/migrations/0001_*.sql ... database/migrations/$(printf '%04d' $((N-1)))_*.sql; do
  psql -U observatorio -d observatorio -v ON_ERROR_STOP=1 -f "$f"
done
```

**Escalar si**: la migración ya está en producción con datos cargados → evaluar forward-fix (nueva migración correctiva) en vez de reversión.
