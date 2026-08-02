# Auditoría vía grafiphy — 2026-08-02 (regenerado)

> Regenerado contra el árbol de trabajo actual (incluye cambios sin commitear:
> rediseño de `dashboard/`, `plan2.md`) + esquema real de PostgreSQL 17/PostGIS
> levantado nativamente para esta corrida (`schema.sql` + 7 migraciones, 0
> errores). Grafo: **862 nodos, 1139 aristas, 19 comunidades** — ver
> `graphify-out/GRAPH_REPORT.md` para el reporte completo y `README.md` para
> cómo regenerar.

## Lo más importante: el pipeline de DANE ya cierra el ciclo completo

Aprovechando la BD real levantada para este grafo, corrí `python -m etl.dane.pipeline`
de punta a punta contra el Excel oficial (`DCD-area-proypoblacion-Mun-2020-2035-ActPostCOVID-19.xlsx`):

```
[dane] filas cargadas a serie_historica: 17952
```

**Es la primera vez en toda la auditoría que un pipeline piloto llega a `curated`
con datos reales**, sin ningún parche manual. Esto confirma que las dos correcciones
más recientes (`etl/dane/pipeline.py` para el layout del Excel, y `sanear_json()`
en `etl/common/db.py` para el bug de `NaN`→`jsonb`) quedaron bien resueltas —
verificado en vivo, no solo por lectura de código. 17.952 = 1123 municipios × 16 años,
exacto (1122 del dataset DIVIPOLA de Socrata + Mapiripana, el ANM que ya se
suplementa en `etl/common/divipola.py::ANMS_FALTANTES`).

## Lectura del grafo (estructura real, no diseño teórico)

**God nodes (los núcleos reales del sistema, por conexiones):**

| Nodo | Aristas | Rol |
|---|---|---|
| `Lineage` | 30 | Todo pipeline pasa por aquí — trazabilidad es literalmente el nodo más central del código, coherente con que sea un requisito de diseño (sección 3) y no un añadido. |
| `PipelineETL` | 26 | Clase base de los 8 pipelines (4 reales + 4 esqueleto). |
| `validar()` | 17 | Pandera, usado en todos los pipelines que cargan a `curated`. |
| `DANE_Poblacion`, `ART_PDET`, `Internacional_WorldBank` | 14/14/12 | Los tres pipelines más "conectados" del código — coincide con ser los más maduros. |
| `hash_registro()`, `upsert_fuente()`, `insertar_serie()` | 13/12/12 | Utilidades de `etl/common/cargar.py` — el punto de paso obligado hacia `curated`. |

Esto confirma estructuralmente algo que las auditorías manuales ya habían encontrado
por otro camino: la arquitectura ETL está bien centralizada alrededor de
`Lineage`/`PipelineETL`/`cargar.py` — no hay lógica de carga duplicada por pipeline.

**Comunidades del grafo** (`GRAPH_REPORT.md` completo tiene el detalle de las 19):

- Comunidad 9: las 8 tablas `curated.*` — aisladas del resto del código como un
  bloque propio, esperado en un esquema bien normalizado.
- Comunidad 10: `pg_attribute`/`pg_class`/PostGIS internals — ruido de sistema de
  Postgres que se coló en la introspección por `--postgres`; no es información
  del proyecto, se puede ignorar al leer el grafo.
- Comunidad 8: `App()`, `Footer()`, `KPIFuentes()`, `MapaNacional()`, `Inicio()` —
  el dashboard aparece como su propia comunidad bien separada del backend,
  conectada solo a través de `obtenerFuentes()`/fetch — consistente con que el
  frontend consume el API y no tiene acoplamiento directo a la BD.

**Ciclos de importación:** ninguno detectado — señal sana.

**Conexiones "sorprendentes" que señaló el grafo:** son solo los tests llamando a
las funciones que prueban (`test_slugificar()` → `slugificar()`, etc.) — el grafo
las marca como sorprendentes por ser aristas test→código, no un hallazgo real.

**Gaps de conocimiento:** 35 nodos "aislados" (≤1 conexión) — en su mayoría son
claves de `package.json`/`tsconfig.json` (`name`, `private`, `version`, `devDependencies`...)
que el extractor AST trata como nodos propios; no son código huérfano real.

## Relación con las auditorías manuales anteriores (`auditoria.md`)

El grafo no reemplaza `auditoria.md` (ese documento tiene los hallazgos de
comportamiento en tiempo de ejecución: bugs de Docker/TCC, fuentes sin acceso
real, etc. — cosas que un grafo estático de AST no puede ver). Lo que aporta
grafiphy es la vista estructural: confirma que la arquitectura ETL es coherente
(un solo camino hacia `curated`, sin duplicación) y ahora, con esta corrida,
que ese camino **funciona de punta a punta para DANE con datos reales**.

## Cómo se regeneró esta corrida

Igual que documenta `README.md`, con la diferencia de que el esquema de Postgres
se introspectó contra una instancia **nativa** (Homebrew `postgresql@17` +
PostGIS), no contra Docker — Docker sigue bloqueado en esta máquina por el
permiso de macOS sobre `~/Documents` (ver `auditoria.md`). Postgres quedó
detenido al terminar esta corrida.
