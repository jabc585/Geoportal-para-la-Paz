# Graph Report - /Users/robot/Documents/Observatorio/Geoportal-para-la-Paz/grafiphy  (2026-08-02)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 309 nodes · 568 edges · 19 communities (16 shown, 3 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 25 edges (avg confidence: 0.54)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6a0e5a2b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13

## God Nodes (most connected - your core abstractions)
1. `Lineage` - 30 edges
2. `PipelineETL` - 26 edges
3. `validar()` - 17 edges
4. `compilerOptions` - 16 edges
5. `DANE_Poblacion` - 14 edges
6. `ART_PDET` - 14 edges
7. `hash_registro()` - 13 edges
8. `upsert_fuente()` - 12 edges
9. `insertar_serie()` - 12 edges
10. `Internacional_WorldBank` - 12 edges

## Surprising Connections (you probably didn't know these)
- `test_slugificar()` --calls--> `slugificar()`  [EXTRACTED]
  tests/test_pipelines.py → etl/common/cargar.py
- `test_periodo_anual()` --calls--> `periodo_anual()`  [EXTRACTED]
  tests/test_pipelines.py → etl/common/cargar.py
- `test_dict_anidado_sanea_recursivamente()` --calls--> `sanear_json()`  [EXTRACTED]
  tests/test_db.py → etl/common/db.py
- `test_fecha_se_conserva()` --calls--> `sanear_json()`  [EXTRACTED]
  tests/test_db.py → etl/common/db.py
- `test_nan_float_escala_a_none()` --calls--> `sanear_json()`  [EXTRACTED]
  tests/test_db.py → etl/common/db.py

## Import Cycles
- None detected.

## Communities (19 total, 3 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.07
Nodes (48): insertar_serie(), periodo_anual(), Connection, DataFrame, date, Carga a curated con resolución de catálogos y linaje (secciones 7 y 12).…, Inserta filas normalizadas en curated.serie_historica con deduplicación por…, Periodo flexible (sección 7.1): un año completo. (+40 more)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (28): ABC, archivo_raw(), hash_registro(), Lineage, Linaje de datos obligatorio (sección 3, punto 4 y sección 7). Todo registro…, Hash determinista del contenido de una fila para detección de…, Marca de inmutabilidad: los datos crudos se almacenan tal como se descargan., PipelineETL (+20 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (26): dependencies, maplibre-gl, react, react-dom, devDependencies, @types/react, @types/react-dom, typescript (+18 more)

### Community 3 - "Community 3"
Cohesion: 0.17
Nodes (21): ErrorOut, FuenteOut, MunicipioOut, Pagina, Modelos Pydantic de la API (sección 8: tipado y documentación automática)., SerieOut, get_fuentes(), get_indicador() (+13 more)

### Community 4 - "Community 4"
Cohesion: 0.13
Nodes (20): insertar_raw(), Connection, Conexión a base de datos y registro de métricas de calidad (secciones 7.3 y…, Convierte NaN/NaT/NA a None recursivamente (hallazgo de auditoría 2026-08-02).…, Inserta filas en raw.<tabla> conservando linaje (sección 7.3)., Registra métricas de calidad de la corrida (sección 7.4)., registrar_metricas(), sanear_json() (+12 more)

### Community 5 - "Community 5"
Cohesion: 0.12
Nodes (11): date, Fiscalia_Estadisticas, DataFrame, Conector de comparabilidad internacional (sección 5.2). La capa de…, Internacional_WorldBank, DataFrame, Devuelve {codigo_indicator: nombre} desde WB_INDICADORES., Pruebas del conector internacional World Bank (sección 5.2 y 7.6). (+3 more)

### Community 6 - "Community 6"
Cohesion: 0.09
Nodes (21): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+13 more)

### Community 7 - "Community 7"
Cohesion: 0.18
Nodes (17): DataFrameModel, Config, EsquemaBase, DataFrame, Validación de datos con contratos (sección 4.1 y 12). Los pipelines validan…, Contrato mínimo para toda serie: territorio, periodo y valor numérico. Nota: la…, Valida un DataFrame contra el contrato y devuelve (datos válidos, rechazados).…, validar() (+9 more)

### Community 8 - "Community 8"
Cohesion: 0.12
Nodes (6): get, raiz(), Punto de entrada de la API (sección 8: FastAPI + OpenAPI en /docs). CORS…, fixture, Pruebas de la API v1 (sección 8) con servicios simulados — sin BD., simular_servicios()

### Community 9 - "Community 9"
Cohesion: 0.20
Nodes (14): _columna(), _detectar_fila_encabezado(), _leer_excel_dane(), _normalizar(), _normalizar_columnas(), DataFrame, Conector piloto DANE (población) - fuente de la fase 2 del plan. Acceso real…, Minúsculas, sin acentos y espacios a guion bajo (p. ej. 'ÁREA GEOGRÁFICA'). (+6 more)

### Community 10 - "Community 10"
Cohesion: 0.26
Nodes (7): Fuente, obtener(), obtenerFuentes(), App(), KPIFuentes(), MapaNacional(), Inicio()

## Knowledge Gaps
- **34 isolated node(s):** `name`, `private`, `version`, `type`, `dev` (+29 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `conectar()` connect `Community 3` to `Community 1`, `Community 4`?**
  _High betweenness centrality (0.136) - this node is a cross-community bridge._
- **Why does `Lineage` connect `Community 1` to `Community 0`, `Community 9`, `Community 5`?**
  _High betweenness centrality (0.119) - this node is a cross-community bridge._
- **Why does `PipelineETL` connect `Community 1` to `Community 0`, `Community 9`, `Community 3`, `Community 5`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `Lineage` (e.g. with `PipelineETL` and `DANE_Poblacion`) actually correct?**
  _`Lineage` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `PipelineETL` (e.g. with `Lineage` and `DANE_Poblacion`) actually correct?**
  _`PipelineETL` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `DANE_Poblacion` (e.g. with `Lineage` and `PipelineETL`) actually correct?**
  _`DANE_Poblacion` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `name`, `private`, `version` to the rest of the system?**
  _34 weakly-connected nodes found - possible documentation gaps or missing edges._