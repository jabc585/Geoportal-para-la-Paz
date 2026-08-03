# Observatorio para la Paz en Colombia

Plataforma de datos abiertos sobre paz, conflicto y desarrollo territorial en
Colombia. 18 pipelines ETL ingieren datos de fuentes oficiales (DANE, UARIV,
Policía Nacional, CNMH, ART/PDET, IDEAM, HDX, ACLED, UNHCR, Banco Mundial) con
trazabilidad completa por registro: cada cifra conserva su fuente, URL de origen,
fecha de extracción y licencia.

**Stack**: Python (FastAPI + Pandera + psycopg), PostgreSQL/PostGIS, React +
TypeScript + MapLibre GL + Tailwind.

**Estado**: 1494 nodos en grafo de arquitectura (Graphify), 165 tests backend,
API con 10 rutas GET de solo lectura, rate limiting verificado, mapa coroplético
de 1122 municipios, 157K filas en `serie_historica`, 31K proyectos PDET.

**Uso previsto**: consulta pública por ciudadanos, periodistas, ONGs, academia y
organismos de derechos humanos. Los datos agregados (sin PII) permiten análisis
territorial de indicadores de violencia, desplazamiento y construcción de paz,
con distinción explícita entre fuentes oficiales y de memoria histórica.

---

## Estado actual

- **18 pipelines ETL** contra fuentes oficiales reales: DANE (población),
  UARIV (víctimas RUV), Policía Nacional (homicidios, hurto, violencia
  intrafamiliar, delitos sexuales), CNMH SIEVCAC (6 hechos: minas, atentados,
  desaparición, reclutamiento, bienes, acciones), ART/PDET, IDEAM
  (deforestación), HDX (eventos de conflicto), ACLED (violencia política),
  UNHCR (población desplazada), Banco Mundial.
- **Esquema PostgreSQL/PostGIS** con separación `raw`/`staging`/`curated`,
  versionado SCD tipo 2, 16 migraciones, vista de reconciliación multi-fuente.
- **API FastAPI v1**: 10 rutas GET de solo lectura, paginación por cursor,
  exportación CSV/GeoJSON, `?modo=tasa` (×100.000 hab.), ficha de territorio,
  healthcheck de frescura de fuentes. Rate limiting verificado (120/min global,
  10/min CSV).
- **Dashboard React + TypeScript + MapLibre GL**: mapa coroplético por
  quintiles (paleta viridis, apta para daltonismo), 6 indicadores en selector,
  KPIs con datos reales, exportación CSV/GeoJSON, diseño oscuro con Tailwind 4.
- **165 tests backend** (pytest, deterministas, <2s), **22 tests frontend**
  (vitest + testing-library), 68% cobertura, ruff limpio, 0 CVEs producción.
- **CI honesto**: ruff + pip-audit + pytest + npm build + npm test + migraciones
  sincronizadas. Gobernanza mensual automática (schedule).
- **Seguridad**: CSP estricta, cabeceras de hardening, CORS explícito en
  producción, Docker no-root + imagen por digest, 0 endpoints de escritura,
  0 datos personales, umbral-k (k ≥ 5) en capa de consulta.

Ver `auditoria_ronda5.md` para la auditoría integral más reciente (8.1/10).

## Requisitos

- Docker + Docker Compose (recomendado)
- Python 3.12+
- PostgreSQL 17 con PostGIS (o el contenedor incluido)
- Node.js 20+ (para el dashboard)

## Arranque rápido (Docker)

```bash
cp .env.example .env
docker compose -f docker/docker-compose.yml up -d postgres   # BD con esquema + semilla
docker compose -f docker/docker-compose.yml exec postgres psql -U observatorio -d observatorio -c \
  "SELECT count(*) FROM curated.departamento"                 # 33 departamentos sembrados
# Siembra de municipios (catálogo DIVIPOLA, requiere red):
.venv/bin/python -m etl.common.divipola
docker compose -f docker/docker-compose.yml up api           # API en http://localhost:8000
docker compose -f docker/docker-compose.yml up etl           # ejecuta pipelines piloto
```

> **Seguridad (sección 13):** `POSTGRES_PASSWORD` usa `observatorio_dev` solo como fallback de desarrollo. **No usar ese valor en staging/producción** — definir una contraseña fuerte vía variable de entorno en todos los entornos expuestos.

Documentación interactiva de la API: http://localhost:8000/docs

## Arranque local (sin Docker)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# BD PostgreSQL+PostGIS disponible en DATABASE_URL (ver .env.example)
psql -d observatorio -f database/schema.sql
for f in database/migrations/*.sql; do psql -d observatorio -f "$f"; done
.venv/bin/python -m etl.common.divipola
.venv/bin/python -m etl.common.capas_geo
uvicorn api.main:app --reload
# En otra terminal:
python -m etl.run_all
```

## Dashboard

```bash
cd dashboard
npm ci
npm run dev        # http://localhost:5173
npm run build      # compilación de producción
npm test           # 22 tests
```

## Estructura

```
data/          raw (inmutable) → processed → curated → external
etl/           pipelines por fuente + common (linaje, validación, calidad)
database/      schema.sql + 16 migraciones + views
api/           FastAPI v1: routes / models / services
dashboard/     React + TypeScript + MapLibre GL + Tailwind
docs/          fuentes (ficha por fuente) + runbook + operaciones
config/        catálogo de fuentes + investigación de endpoints
tests/         165 tests backend + tests/load (k6)
```

## Principios clave

- **Sin PII**: solo datos agregados por municipio/departamento, sin microdatos.
- **Trazabilidad**: cada cifra conserva fuente, URL, fecha de extracción y licencia.
- **Neutralidad**: fuentes oficiales + memoria histórica, mostrando ambas cuando discrepan.
- **No daño**: umbral-k (k ≥ 5) en capa de consulta, sin exposición de territorios vulnerables.
- **Licencias**: código MIT; datos curados CC BY 4.0; datos crudos conservan licencia de su fuente.

## Pruebas

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/ -v                     # 165 tests, sin BD real
pytest tests/ -q --cov=api --cov=etl --cov-fail-under=65
ruff check api/ etl/ tests/
```

## Auditoría de arquitectura (Graphify)

El grafo de dependencias se genera con [Graphify](https://graphify.com/) a partir
del código fuente + esquema real de PostgreSQL/PostGIS.

| Métrica | Valor |
|---|---|
| Nodos | 1494 (código + BD) |
| Aristas | 2432 |
| Comunidades | 73 |
| Ciclos de importación | 0 |
| God node #1 | `Lineage` (45 aristas) — trazabilidad |

### Regenerar

```bash
python3 -m venv /tmp/graphify-venv
/tmp/graphify-venv/bin/pip install "graphifyy[sql]"
/tmp/graphify-venv/bin/graphify extract . --code-only \
  --postgres "postgresql://observatorio:observatorio_dev@localhost:5432/observatorio" \
  --out grafiphy
/tmp/graphify-venv/bin/graphify cluster-only grafiphy --no-label
```

Los artefactos quedan en `grafiphy/`. Ver `grafiphy/README.md` para consultas y
diagnóstico.

## Auditorías

El proyecto se audita con verificación en vivo desde la ronda 1:

| Ronda | Fecha | Puntuación | Documento |
|---|---|---|---|
| 5 | 2026-08-03 | **8.1/10** | `auditoria_ronda5.md` |
| 4 | 2026-08-03 | 7.9/10 | `auditoria2.md` |
| 1–3 | 2026-08-02 | 6.4→7.4→7.8 | `auditoria2.md` (histórico) |

Cada ronda ejecuta la plataforma de punta a punta contra fuentes reales y
regenera el grafo de arquitectura.
