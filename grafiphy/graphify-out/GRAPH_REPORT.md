# Graph Report - grafiphy  (2026-08-02)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1323 nodes · 1922 edges · 74 communities (52 shown, 22 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 41 edges (avg confidence: 0.65)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3a73d077`
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
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- Community 48
- Community 49
- Community 50
- Community 54
- Community 55
- Community 61
- Community 62
- Community 63
- Community 64
- Community 65
- Community 66
- Community 67
- Community 68
- Community 69
- Community 71
- Community 72
- Community 73

## God Nodes (most connected - your core abstractions)
1. `PipelineETL` - 32 edges
2. `upsert_fuente()` - 29 edges
3. `insertar_serie()` - 27 edges
4. `Internacional_ACLED` - 23 edges
5. `transaccion()` - 22 edges
6. `validar()` - 22 edges
7. `upsert_indicador()` - 22 edges
8. `periodo_anual()` - 20 edges
9. `IDEAM_Ambiental` - 17 edges
10. `Policia_Homicidios` - 17 edges

## Surprising Connections (you probably didn't know these)
- `test_victimas_transformar_agrega_por_tipo()` --calls--> `Victimas_Hechos`  [EXTRACTED]
  tests/test_pipelines.py → etl/victimas/pipeline.py
- `_RespJson` --uses--> `Victimas_Hechos`  [INFERRED]
  tests/test_victimas.py → etl/victimas/pipeline.py
- `test_slugificar_empareja_tildes_y_puntos()` --calls--> `slugificar()`  [EXTRACTED]
  tests/test_acled.py → etl/common/cargar.py
- `test_hash_determinista()` --calls--> `hash_registro()`  [EXTRACTED]
  tests/test_lineage.py → etl/common/lineage.py
- `test_hash_sensible_al_orden_y_contenido()` --calls--> `hash_registro()`  [EXTRACTED]
  tests/test_lineage.py → etl/common/lineage.py

## Import Cycles
- None detected.

## Communities (74 total, 22 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.00
Nodes (22): "curated"."audit_log", "curated"."data_quality_metrics", "raw"."art_pdet", "raw"."cnmh_acciones", "raw"."cnmh_atentados", "raw"."cnmh_bienes", "raw"."cnmh_desaparicion", "raw"."cnmh_minas" (+14 more)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (33): descargarCSV(), Fuente, IndicadorTotal, MapaFeature, MapaIndicador, obtener(), obtenerFuentes(), obtenerMapa() (+25 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (17): IDEAM_Ambiental, DataFrame, Lineage, Path, fixture, archivos_acled(), Genera un XLSX mínimo por archivo esperado en un directorio temporal., Pruebas de la API v1 (sección 8) con servicios simulados — sin BD. (+9 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (40): allowScripts, esbuild@0.21.5, esbuild@0.28.1, fsevents@2.3.3, dependencies, maplibre-gl, react, react-dom (+32 more)

### Community 4 - "Community 4"
Cohesion: 0.07
Nodes (27): date, insertar_raw(), Registra métricas de calidad de la corrida (sección 7.4)., Convierte NaN/NaT/NA a None recursivamente (hallazgo de auditoría 2026-08-02).…, Inserta filas en raw.<tabla> conservando linaje (sección 7.3)., registrar_metricas(), sanear_json(), RuntimeError (+19 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (34): BytesIO, _leer_municipios(), Connection, Siembra la capa geo de municipios (tipo 'divipola') en…, _reportar_cobertura(), sembrar(), _url_firmada(), conectar() (+26 more)

### Community 6 - "Community 6"
Cohesion: 0.13
Nodes (22): ABC, insertar_indicador_internacional(), periodo_anual(), Carga a curated con resolución de catálogos y linaje (secciones 7 y 12).…, Inserta indicadores internacionales (país-año) en lote con executemany.…, Periodo flexible (sección 7.1): un año completo., Resuelve código DIVIPOLA a (municipio_id, departamento_id) vigentes (sección…, resolver_territorio() (+14 more)

### Community 7 - "Community 7"
Cohesion: 0.11
Nodes (22): Policia_Delitos, Policia_Homicidios, DataFrame, Lineage, Homicidios intencionales: Excel oficial SIEDCO de policia.gov.co. El Excel trae…, Variable configurada (URLs separadas por coma) o patrón por año., _df_homicidios(), _df_hurto() (+14 more)

### Community 8 - "Community 8"
Cohesion: 0.13
Nodes (17): Internacional_ACLED, DataFrame, Lineage, Capa departamental: admin1 semanal → departamento-año (EVENTS y FATALITIES)., nombre normalizado de departamento → código DIVIPOLA (2 dígitos)., Path, _df_admin1(), Tests del conector ACLED (agregados país-año y departamento-año). (+9 more)

### Community 9 - "Community 9"
Cohesion: 0.11
Nodes (15): Conector de comparabilidad internacional (sección 5.2). La capa de…, Internacional_UNHCR, DataFrame, Lineage, Internacional_WorldBank, DataFrame, Lineage, Devuelve {codigo_indicator: nombre} desde WB_INDICADORES. (+7 more)

### Community 10 - "Community 10"
Cohesion: 0.12
Nodes (16): _agregar_soql(), Fiscalia_Estadisticas, DataFrame, Lineage, Consulta agregada de SoQL ($select/$group) con paginación por offset., _df_agregado(), Pruebas del conector Fiscalía V3 (plan2.md Fase B, fuente 3). El pipeline usa…, Debe pedir count(*) + $group, no filas individuales (diseño por volumen). (+8 more)

### Community 11 - "Community 11"
Cohesion: 0.12
Nodes (13): Internacional_HDX, DataFrame, Lineage, Resuelve la URL de descarga (S3 firmada) vía resource_show de CKAN., _url_firmada(), _df_conflictos(), Pruebas del conector HDX HAPI (plan2.md Fase B, fuente 4). Replica el shape…, Debe resolver la URL de descarga (S3 firmada) con resource_show. (+5 more)

### Community 12 - "Community 12"
Cohesion: 0.08
Nodes (18): Pruebas del ciclo de transformación/carga de los pipelines piloto. Las…, Ejecuta extraer+transformar con un Excel que replica el layout real (metadata,…, Shape real de 'Iniciativas PDET' (datos.gov.co/gmvf-t63e, auditoría…, extraer() contra la forma de respuesta real del dataset Iniciativas PDET: las…, El suplemento de ANMs debe tener (codigo, nombre, codigo_depto) válidos., Formato verificado en auditoría: encabezado fila 9, columna MPIO, y 3 filas por…, Legacy Socrata sin columna de área: no se descarta nada., Replica el layout real: 9 filas de metadata antes del encabezado. (+10 more)

### Community 13 - "Community 13"
Cohesion: 0.19
Nodes (12): insertar_serie(), Connection, DataFrame, Inserta filas normalizadas en curated.serie_historica con deduplicación por…, Inserta o recupera el fuente_id del catálogo curated.fuentes. codigo (slug…, Inserta o recupera el indicador_id del catálogo curated.indicadores.…, upsert_fuente(), upsert_indicador() (+4 more)

### Community 14 - "Community 14"
Cohesion: 0.09
Nodes (21): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+13 more)

### Community 15 - "Community 15"
Cohesion: 0.13
Nodes (14): CNMH_Memoria, DataFrame, Lineage, _df_casos(), _df_victimas(), Pruebas del conector CNMH SIEVCAC (plan2.md Fase B, fuente 2). DataFrames que…, La paginación $limit/$offset debe cubrir datasets > 50.000 filas (desaparición…, _Resp (+6 more)

### Community 16 - "Community 16"
Cohesion: 0.12
Nodes (15): raw.cnmh_acciones, raw.cnmh_atentados, raw.cnmh_bienes, raw.cnmh_desaparicion, raw.cnmh_minas, raw.cnmh_reclutamiento, raw.fiscalia_procesos, raw.fiscalia_victimas (+7 more)

### Community 17 - "Community 17"
Cohesion: 0.24
Nodes (14): ErrorOut, FuenteEstadoOut, FuenteOut, HealthOut, IndicadorTotalOut, MapaFeatureOut, MapaOut, MunicipioOut (+6 more)

### Community 18 - "Community 18"
Cohesion: 0.18
Nodes (14): get_fuentes(), get_health(), get_indicador(), get_pdet_proyectos(), get, Rutas núcleo de la API v1 (sección 8)., contar_proyectos_pdet(), listar_fuentes() (+6 more)

### Community 19 - "Community 19"
Cohesion: 0.26
Nodes (11): Normaliza un texto a código seguro: minúsculas, sin acentos, guiones bajos., slugificar(), DANE_Poblacion, _detectar_fila_encabezado(), _leer_excel_dane(), _normalizar_columnas(), DataFrame, Lineage (+3 more)

### Community 20 - "Community 20"
Cohesion: 0.14
Nodes (5): Pruebas de la configuración centralizada de fuentes (plan2.md, Fase A). Sin red…, Crítico: un default no-None rompería el Excel real de DANE (NaN fix)., Los valores de `variable` deben ser campos reales de Settings, salvo plantillas…, test_dane_poblacion_hoja_por_defecto_es_none(), test_fuentes_yaml_referencian_campos_reales()

### Community 21 - "Community 21"
Cohesion: 0.18
Nodes (9): Instancia compartida de slowapi Limiter (Fase 0.3, plan3.md). Un solo limiter…, get, raiz(), Punto de entrada de la API (sección 8: FastAPI + OpenAPI en /docs). CORS…, FastAPI, _build_app(), Test de integración: el rate limiter global debe rechazar después de superar el…, 11 requests a /test con límite 10/min → al menos uno devuelve 429. (+1 more)

### Community 22 - "Community 22"
Cohesion: 0.31
Nodes (12): DataFrameModel, Valida un DataFrame contra el contrato y devuelve (datos válidos, rechazados).…, validar(), parametrize, _df_valido(), Pruebas de la validación con Pandera (secciones 7.4 y 12)., test_validar_acepta_serie_correcta(), test_validar_codigos_digitos_ok() (+4 more)

### Community 23 - "Community 23"
Cohesion: 0.21
Nodes (8): _nulos_columnas_criticas(), DataFrame, Lineage, Conteo de nulos por columna crítica del staging (hallazgo 14 auditoría…, Descarga los datos crudos y devuelve (dataframe, linaje)., Normaliza a staging (códigos DIVIPOLA, periodos, valores numéricos)., Promueve datos validados a curated.serie_historica., Corre la corrida completa con UNA conexión gestionada (auditoría 2026-08-02).…

### Community 24 - "Community 24"
Cohesion: 0.24
Nodes (9): _get_pool(), obtener_conexion(), Connection, Pool de conexiones para la API (plan3.md, Fase 1.8). Las funciones de servicio…, Devuelve una conexión del pool (ya con autocommit=True para solo lectura)., estado_fuentes(), Estado de configuración de fuentes para el healthcheck (plan2.md, Fase A punto…, Por fuente: variable configurada + último pipeline exitoso en la BD. (+1 more)

### Community 25 - "Community 25"
Cohesion: 0.44
Nodes (10): curated, curated.capa_contexto_territorial, curated.departamento, curated.fuentes, curated.indicador_internacional, curated.indicadores, curated.municipio, curated.serie_historica (+2 more)

### Community 26 - "Community 26"
Cohesion: 0.20
Nodes (9): BaseSettings, _check(), get_source_url(), _inyectar_al_entorno(), Configuración centralizada de fuentes (plan2.md, Fase A). Carga automática de…, Puente para los 4 pipelines legacy (DANE, Víctimas, PDET, World Bank): siguen…, Para pipelines nuevos (Fase B): valida en el punto de uso, no al importar., Comando opt-in (plan2.md, Fase A punto 8): reporta qué variables de fuentes… (+1 more)

### Community 27 - "Community 27"
Cohesion: 0.27
Nodes (8): hash_registro(), Lineage, date, Hash determinista del contenido de una fila para detección de…, Pruebas del módulo de linaje (sección 3, punto 4)., test_hash_determinista(), test_hash_sensible_al_orden_y_contenido(), test_lineage_completo()

### Community 28 - "Community 28"
Cohesion: 0.31
Nodes (10): "curated"."capa_contexto_territorial", "curated"."departamento", "curated"."fuentes", "curated"."indicador_internacional", "curated"."indicadores", "curated"."municipio", "curated"."pdet_proyectos", "curated"."serie_historica" (+2 more)

### Community 29 - "Community 29"
Cohesion: 0.31
Nodes (7): _JSONFormatter, obtener_logger_etl(), Logging estructurado para ETL y API (plan3.md, Fase 4.19). Reemplaza los…, Logger con ``run_id`` fijo para toda la corrida de un pipeline., _setup_logger(), Logger, LogRecord

### Community 30 - "Community 30"
Cohesion: 0.28
Nodes (7): Config, EsquemaBase, EsquemaSerieNormalizada, Validación de datos con contratos (sección 4.1 y 12). Los pipelines validan…, Contrato mínimo para toda serie: territorio, periodo y valor numérico. Nota: la…, Formato normalizado que consume insertar_serie (etl/common/cargar.py). Es el…, Conector de estadísticas judiciales: Fiscalía V3 (plan2.md Fase B, fuente 3).…

### Community 31 - "Community 31"
Cohesion: 0.25
Nodes (8): _cache_control(), Request, _rate_limit_exceeded(), exception_handler, JSONResponse, middleware, RateLimitExceeded, Response

### Community 32 - "Community 32"
Cohesion: 0.46
Nodes (3): ART_PDET, DataFrame, Lineage

### Community 33 - "Community 33"
Cohesion: 0.32
Nodes (4): DataFrame, Lineage, Fila "SIN DEFINIR" del RUV a nivel nacional (municipio_id NULL). Postgres no…, Agrega sujetos de atención (per_sa) por municipio y año de corte.

### Community 34 - "Community 34"
Cohesion: 0.32
Nodes (8): pg_attribute, pg_class, pg_namespace, pg_type, "public"."geography_columns", "public"."geometry_columns", "public"."spatial_ref_sys", "public"."updategeometrysrid"()

### Community 35 - "Community 35"
Cohesion: 0.57
Nodes (6): Victimas_Hechos, _fake_get_socrata(), Tests del conector de víctimas (UARIV vía Socrata municipal, dataset…, test_extraer_cae_a_socrata_cuando_victimas_url_no_responde(), test_extraer_socrata_conserva_sin_definir_como_nacional(), test_transformar_agrupa_por_municipio_anio()

### Community 36 - "Community 36"
Cohesion: 0.33
Nodes (6): get_indicador_csv(), Request, exportar_serie_csv(), Serie completa de un indicador para exportación CSV (sección 8 y 10). Mismos…, limit, StreamingResponse

### Community 37 - "Community 37"
Cohesion: 0.40
Nodes (6): datetime, _cortes_por_anio(), _parsear_corte(), Fecha de corte en formatos mixtos del dataset: '31/12/2025', '30/09/24',…, Último corte disponible de cada año (serie anual de acumulados RUV)., test_parsear_corte_formatos_mixtos()

### Community 38 - "Community 38"
Cohesion: 0.33
Nodes (5): encontrar_columna(), encontrar_columna_opcional(), DataFrame, Devuelve la primera columna que existe entre los aliases; falla si ninguna. Los…, Como encontrar_columna pero devuelve None si no hay coincidencia.

### Community 39 - "Community 39"
Cohesion: 0.50
Nodes (4): consultar_serie(), _cursor_payload(), Servicios de acceso a datos desde curated (solo lectura, sección 7.3)., Serie histórica con paginación basada en cursor (sección 8). El cursor codifica…

### Community 40 - "Community 40"
Cohesion: 0.50
Nodes (4): get_mapa(), consultar_mapa(), Capa coroplética municipal (fase 5): GeoJSON simplificado. Une el agregado…, MapaOut

### Community 41 - "Community 41"
Cohesion: 0.50
Nodes (4): get_indicador_total(), consultar_total(), Total nacional por año de un indicador (para KPIs del dashboard). Suma todas…, IndicadorTotalOut

### Community 42 - "Community 42"
Cohesion: 0.50
Nodes (4): get_territorio(), consultar_territorio(), ErrorOut, MunicipioOut

## Knowledge Gaps
- **73 isolated node(s):** `target`, `useDefineForClassFields`, `ES2020`, `DOM`, `DOM.Iterable` (+68 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PipelineETL` connect `Community 6` to `Community 32`, `Community 2`, `Community 35`, `Community 5`, `Community 7`, `Community 8`, `Community 9`, `Community 10`, `Community 11`, `Community 13`, `Community 15`, `Community 19`, `Community 23`, `Community 30`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Why does `IDEAM_Ambiental` connect `Community 2` to `Community 13`, `Community 6`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Why does `upsert_fuente()` connect `Community 13` to `Community 32`, `Community 5`, `Community 6`, `Community 9`, `Community 19`, `Community 30`?**
  _High betweenness centrality (0.010) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `PipelineETL` (e.g. with `DANE_Poblacion` and `Fiscalia_Estadisticas`) actually correct?**
  _`PipelineETL` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `target`, `useDefineForClassFields`, `ES2020` to the rest of the system?**
  _73 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.0036429872495446266 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.08405797101449275 - nodes in this community are weakly interconnected._