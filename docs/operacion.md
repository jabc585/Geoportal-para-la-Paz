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

## Acumulación continua y frescura de datos

Los pipelines **nunca borran**. Cada capa acumula con una regla distinta:

| Capa | Qué hace en cada corrida | Cómo |
|---|---|---|
| `curated.*` | Inserta periodos nuevos y **actualiza los valores que la fuente haya revisado**, contando solo los que cambian de verdad | `ON CONFLICT … DO UPDATE … WHERE valor IS DISTINCT FROM` |
| `raw.*` | Espejo inmutable: guarda **el contenido que no había visto antes** y descarta las copias idénticas | `ON CONFLICT (hash_fila, ocurrencia) DO NOTHING` (migración 0016) |

Si la fuente corrige una cifra, su `hash_fila` cambia y entra en `raw` como
registro nuevo: la versión anterior permanece, así que el histórico de
correcciones queda íntegro. La `ocurrencia` numera las filas que el origen sirve
repetidas dentro de un mismo extracto (HDX trae 300), para que deduplicar entre
corridas no las pierda.

Antes de la migración 0016 esto no era cierto para `raw`: cada corrida
reescribía el snapshot entero. Una sola jornada de pruebas dejó 3,6 M de filas
y 1.973 MB, de los cuales 1,86 M eran copias byte a byte. Con una corrida
diaria eso habrían sido ~200-300 GB al año. Si vuelves a ver crecer `raw` de
forma lineal con el número de ejecuciones, el índice único
`uq_<tabla>_hash_ocurrencia` es lo primero que hay que revisar.

En la salida del ETL, la línea `raw.<tabla>: N filas extraídas, M nuevas` es la
señal de que la deduplicación está actuando.

### Ejecución programada

Opción A — GitHub Actions (`.github/workflows/etl-programado.yml`): diario a las
07:00 UTC. Requiere que el runner alcance la base de datos; con un Postgres en
red privada hace falta un *self-hosted runner*.

Opción B — cron del servidor:

```cron
# ETL diario a las 02:00 hora Colombia
0 2 * * * cd /ruta/al/proyecto && .venv/bin/python -m etl.run_all >> /var/log/observatorio-etl.log 2>&1
# Validación de frescura una hora después
0 3 * * * cd /ruta/al/proyecto && .venv/bin/python -m etl.common.frescura >> /var/log/observatorio-frescura.log 2>&1
```

### Validar que los datos siguen vigentes

```bash
python -m etl.common.frescura   # exit 0 si todo al día; 1 si hay obsoletas o sin datos
```

Clasifica cada fuente comparando su última extracción contra la periodicidad que
ella misma declara en `curated.fuentes`:

| Estado | Criterio |
|---|---|
| `al_dia` | dentro del periodo esperado |
| `retrasada` | hasta 2× el periodo (avisa, no rompe) |
| `obsoleta` | más de 2× el periodo |
| `sin_datos` | nunca se ha extraído |

También disponible en la API (`GET /api/v1/frescura`) y visible en la tabla de
fuentes del dashboard, con dos fechas distintas que no deben confundirse:
**Extraída** (cuándo se consultó la fuente) y **Datos hasta** (hasta qué periodo
llegan las cifras). IDEAM, por ejemplo, se extrae hoy pero sus datos llegan a
2022: ambas cosas son ciertas y el usuario debe verlas.
