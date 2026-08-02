# Observatorio para la Paz en Colombia

Plataforma de datos sobre paz, conflicto y desarrollo territorial en Colombia, basada en fuentes oficiales con trazabilidad completa. Ver `plan.md` para el plan de desarrollo completo.

## Estado actual

Esqueleto técnico inicial (secciones 6 y 21 del plan):

- Estructura de directorios (`data/`, `etl/`, `database/`, `api/`, `dashboard/`, `docs/`)
- Esquema PostgreSQL con separación `raw/staging/curated` (sección 7.3), versionado SCD tipo 2 (7.2), `data_quality_metrics` (7.4) y vista de reconciliación (7.5)
- Entorno Docker de desarrollo (PostgreSQL + PostGIS, ETL, API)
- Esqueleto ETL con 3 conectores piloto: DANE, Unidad de Víctimas, ART/PDET (sección 21, paso 4)
- API FastAPI v1 con paginación por cursor, CORS y OpenAPI en `/docs` (sección 8)
- Documentación de gobernanza y checklist de privacidad (secciones 3 y 3.1)

## Requisitos

- Docker + Docker Compose (recomendado)
- Python 3.12+
- PostgreSQL 16 con PostGIS (o el contenedor incluido)

## Arranque rápido (Docker)

```bash
cp .env.example .env
docker compose -f docker/docker-compose.yml up -d postgres   # BD con esquema inicial
docker compose -f docker/docker-compose.yml up api           # API en http://localhost:8000
docker compose -f docker/docker-compose.yml up etl           # ejecuta pipelines piloto
```

Documentación interactiva de la API: http://localhost:8000/docs

## Arranque local (sin Docker)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# BD PostgreSQL+PostGIS disponible en DATABASE_URL (ver .env.example)
psql -d observatorio -f database/schema.sql
uvicorn api.main:app --reload
python -m etl.run_all
```

## Configuración de fuentes piloto

Los conectores requieren variables de entorno (documentadas en `docs/fuentes/`):

- `DANE_POBLACION_DATASET` — identificador del dataset en datos.gov.co
- `VICTIMAS_URL` — endpoint de Datos Paz (por defecto https://datospaz.unidadvictimas.gov.co/api/v1/)
- `PDET_URL` — endpoint de proyectos PDET de la ART

## Estructura (sección 6 del plan)

```
data/          raw (inmutable) -> processed -> curated -> external (shapefiles)
etl/           pipelines por fuente + common (linaje, validación, calidad)
database/      schema.sql + migrations + views + functions
api/           FastAPI v1: routes / models / services
dashboard/     React + MapLibre (pendiente de fase 5)
docs/          fuentes (ficha por fuente) + metodologia (indicadores, privacidad)
tests/         pruebas de ETL y API
```

## Principios clave

- **Sin PII**: datos agregados, checklist de privacidad obligatorio antes de publicar (sección 3.1).
- **Trazabilidad**: cada cifra rastrea hasta su fuente y fecha de extracción (sección 3, punto 4).
- **Neutralidad**: solo fuentes oficiales, metodología pública, comité asesor plural (sección 3, punto 6).
- **Licencias**: código open source; datos curados CC BY 4.0; datos crudos conservan licencia de su fuente (sección 19).

## Próximos pasos (sección 21)

1. Validar catálogo de indicadores con expertos y organizaciones aliadas
2. Conformar comité asesor y aprobar documento de gobernanza (`docs/metodologia/gobernanza_datos.md`)
3. Configurar los endpoints reales de los 3 conectores piloto y completar el mapeo a `curated`
4. Iniciar conversaciones con anfitriones institucionales potenciales
