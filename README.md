# Observatorio para la Paz en Colombia

Plataforma de datos sobre paz, conflicto y desarrollo territorial en Colombia, basada en fuentes oficiales con trazabilidad completa. Ver `plan.md` para el plan de desarrollo completo.

## Estado actual

Esqueleto técnico en construcción (auditoría: sección 6.1 del plan):

- Estructura de directorios (`data/`, `etl/`, `database/`, `api/`, `dashboard/`, `docs/`)
- Esquema PostgreSQL con separación `raw/staging/curated` (sección 7.3), versionado SCD tipo 2 (7.2), `data_quality_metrics` (7.4) y vista de reconciliación (7.5)
- Entorno Docker de desarrollo (PostgreSQL + PostGIS, ETL, API)
- **ETL piloto completo end-to-end**: DANE, Unidad de Víctimas y ART/PDET con extracción → validación Pandera → carga a `curated` con linaje (sección 21, paso 1 cerrado); catálogo DIVIPOLA con seed real desde datos.gov.co y logs de filas descartadas por territorio no resuelto
- Conectores internacionales activos: World Bank, UNHCR, HDX (eventos de conflicto por municipio) y ACLED (agregados país-año desde archivos locales) — ver `docs/fuentes/`
- Memoria histórica (CNMH SIEVCAC, 6 datasets) y Policía Nacional (3 delitos) implementados y verificados en vivo; Fiscalía documentada como inviable por volumen (ficha y `config/investigacion_fuentes.yaml`)
- API FastAPI v1 con paginación por cursor, CORS y OpenAPI en `/docs` (sección 8); `GET /api/v1/health` con estado por fuente
- Frontend React + TypeScript + MapLibre inicializado con KPI contra `/api/v1/fuentes` (paso 5)
- Tests: 88 pruebas pasando (linaje, validación, pipelines, API, internacional, configuración)
- Documentación: gobernanza, checklist de privacidad ejecutado para víctimas, fichas de fuente (pasos 3 y 4)

## Requisitos

- Docker + Docker Compose (recomendado)
- Python 3.12+
- PostgreSQL 16 con PostGIS (o el contenedor incluido)

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
uvicorn api.main:app --reload
python -m etl.run_all
```

## Configuración de fuentes piloto

Los conectores requieren variables de entorno (documentadas en `docs/fuentes/`; método de acceso verificado en auditoría 2026-08-02):

- `DANE_POBLACION_XLSX_URL` — URL del Excel oficial de proyecciones de población (DANE distribuye esta serie en XLSX, no vía API; `DANE_POBLACION_DATASET` Socrata solo para datasets locales)
- `VICTIMAS_URL` — endpoint de Datos Paz (obligatoria, sin default: el path anterior responde 404)
- `PDET_URL` — endpoint de proyectos PDET (obligatoria: la ART no tiene API JSON pública documentada; gestionar con `mesa.go@renovacionterritorio.gov.co`)
- `DIVIPOLA_DEPT_DATASET` / `DIVIPOLA_MUN_DATASET` — datasets DIVIPOLA en datos.gov.co (opcional; defaults: `vcjz-niiq`, `gdxc-w37w`)

## Configuración centralizada (plan2.md, Fase A)

El `.env` se carga automáticamente al importar `etl.common.config` (vía
pydantic-settings, disparado desde `etl/common/pipeline.py`) — ya no hace falta
exportar variables a mano ni depender de que Compose las inyecte.

- `python -m etl.common.config --check` — reporta qué variables de fuentes
  activas faltan (fail-fast opt-in; nada falla al importar).
- `GET /api/v1/health` — estado por fuente: variable configurada + última
  corrida `data_quality_metrics` exitosa.
- `config/fuentes.yaml` — catálogo estructurado de las fuentes nuevas (Fase B/C).
- `config/investigacion_fuentes.yaml` — registro de la investigación en vivo de
  endpoints (resource-ids y bloqueos reales, para no repetir el rastreo).

Los 4 pipelines reales (DANE, Víctimas, PDET, World Bank) siguen leyendo sus
variables con `os.getenv(...)`: no fueron tocados. `etl/common/config.py`
inyecta los valores no vacíos del `.env` al entorno al importarse, así esos
pipelines leen el `.env` sin cambios (las variables ya exportadas en el shell
tienen prioridad).

## Fuentes de Fase B (plan2.md)

Pipelines implementados y verificados en vivo (2026-08-02):

| Fuente | Pipeline | Cobertura cargada |
|---|---|---|
| UNHCR | `etl/internacional/unhcr.py` | país, 8 tipos de población, 1981–2025 |
| CNMH SIEVCAC | `etl/memoria/pipeline.py` (6 hechos) | municipio-año, 1980–2027 |
| HDX Conflict Events | `etl/internacional/hdx.py` | municipio-año, eventos y fatalidades, 2018–2026 |
| Policía | `etl/policia/pipeline.py` (3 delitos) | municipio-año-tipo, 2010–2025 |
| ACLED | `etl/internacional/acled.py` | país-año, 3 series, 1997–2026 (archivos en `data/external/`) |
| Fiscalía | `etl/fiscalia/pipeline.py` | **no activa**: agregación inviable por volumen (23M filas) — ver ficha |

`etl/run_all.py` ejecuta los conectores activos; los pendientes se suman al
confirmar su viabilidad (`config/investigacion_fuentes.yaml` documenta qué
falta y por qué).

## Estructura (sección 6 del plan)

```
data/          raw (inmutable) -> processed -> curated -> external (ACLED, shapefiles)
etl/           pipelines por fuente + common (linaje, validación, calidad)
database/      schema.sql + migrations + views + functions
api/           FastAPI v1: routes / models / services
dashboard/     React + MapLibre (pendiente de fase 5)
docs/          fuentes (ficha por fuente) + metodologia (indicadores, privacidad)
config/        catálogo de fuentes (fuentes.yaml) + investigación de endpoints
tests/         pruebas de ETL y API
```

## Principios clave

- **Sin PII**: datos agregados, checklist de privacidad obligatorio antes de publicar (sección 3.1).
- **Trazabilidad**: cada cifra rastrea hasta su fuente y fecha de extracción (sección 3, punto 4).
- **Neutralidad**: solo fuentes oficiales, metodología pública, comité asesor plural (sección 3, punto 6).
- **Licencias**: código open source; datos curados CC BY 4.0; datos crudos conservan licencia de su fuente (sección 19).

## Pruebas

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest tests/ -v
```

## Próximos pasos (sección 21)

1. Sembrar municipios con `python -m etl.common.divipola` y verificar carga end-to-end contra una BD real
2. Confirmar umbral de supresión k ≥ 5 con el comité asesor (checklist de víctimas)
3. Inicializar el frontend con `npm install` y conectar más KPIs
4. Validar catálogo de indicadores con organizaciones aliadas
5. Gestionar acceso real a la ART (PDET) y confirmar endpoint de Datos Paz
6. Añadir paginación de teselas y capas coropléticas al mapa (fase 5)
