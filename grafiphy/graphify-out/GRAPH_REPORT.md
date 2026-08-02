# Graph Report - grafiphy  (2026-08-02)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1279 nodes · 1890 edges · 62 communities (43 shown, 19 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 45 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7b0ff002`
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
- Community 44
- Community 45
- Community 50
- Community 51
- Community 52
- Community 53
- Community 54
- Community 55
- Community 56
- Community 57
- Community 58
- Community 60
- Community 61

## God Nodes (most connected - your core abstractions)
1. `transaccion()` - 33 edges
2. `PipelineETL` - 32 edges
3. `upsert_fuente()` - 29 edges
4. `validar()` - 28 edges
5. `insertar_serie()` - 27 edges
6. `Internacional_ACLED` - 23 edges
7. `upsert_indicador()` - 22 edges
8. `EsquemaSerieNormalizada` - 21 edges
9. `periodo_anual()` - 20 edges
10. `conectar()` - 19 edges

## Surprising Connections (you probably didn't know these)
- `test_hash_determinista()` --calls--> `hash_registro()`  [EXTRACTED]
  tests/test_lineage.py → etl/common/lineage.py
- `test_hash_sensible_al_orden_y_contenido()` --calls--> `hash_registro()`  [EXTRACTED]
  tests/test_lineage.py → etl/common/lineage.py
- `test_nan_float_escala_a_none()` --calls--> `sanear_json()`  [EXTRACTED]
  tests/test_db.py → etl/common/db.py
- `test_numpy_nan_a_none()` --calls--> `sanear_json()`  [EXTRACTED]
  tests/test_db.py → etl/common/db.py
- `test_pandas_na_y_nat_a_none()` --calls--> `sanear_json()`  [EXTRACTED]
  tests/test_db.py → etl/common/db.py

## Import Cycles
- None detected.

## Communities (62 total, 19 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.00
Nodes (22): "curated"."audit_log", "curated"."data_quality_metrics", "raw"."art_pdet", "raw"."cnmh_acciones", "raw"."cnmh_atentados", "raw"."cnmh_bienes", "raw"."cnmh_desaparicion", "raw"."cnmh_minas" (+14 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (34): _cortes_por_anio(), _parsear_corte(), DataFrame, Lineage, Fila "SIN DEFINIR" del RUV a nivel nacional (municipio_id NULL). Postgres no…, Fecha de corte en formatos mixtos del dataset: '31/12/2025', '30/09/24',…, Último corte disponible de cada año (serie anual de acumulados RUV)., Agrega sujetos de atención (per_sa) por municipio y año de corte. (+26 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (27): date, insertar_raw(), Connection, Registra métricas de calidad de la corrida (sección 7.4)., Inserta filas en raw.<tabla> conservando linaje (sección 7.3)., registrar_metricas(), _nulos_columnas_criticas(), DataFrame (+19 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (26): ABC, BaseSettings, datetime, _check(), get_source_url(), _inyectar_al_entorno(), Configuración centralizada de fuentes (plan2.md, Fase A). Carga automática de…, Puente para los 4 pipelines legacy (DANE, Víctimas, PDET, World Bank): siguen… (+18 more)

### Community 4 - "Community 4"
Cohesion: 0.09
Nodes (30): descargarCSV(), Fuente, IndicadorTotal, MapaFeature, MapaIndicador, obtener(), obtenerFuentes(), obtenerMapa() (+22 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (29): descargar_socrata_paginado(), Descarga paginada de Socrata ($limit/$offset, sin token). Usada por Policía…, _descargar(), Connection, Seed del catálogo territorial DIVIPOLA (secciones 5.1 y 7.2). Descarga los…, sembrar_departamentos(), sembrar_municipios(), Policia_Delitos (+21 more)

### Community 6 - "Community 6"
Cohesion: 0.15
Nodes (19): insertar_serie(), Connection, DataFrame, Carga a curated con resolución de catálogos y linaje (secciones 7 y 12).…, Inserta filas normalizadas en curated.serie_historica con deduplicación por…, Normaliza un texto a código seguro: minúsculas, sin acentos, guiones bajos., Inserta o recupera el fuente_id del catálogo curated.fuentes. codigo (slug…, Inserta o recupera el indicador_id del catálogo curated.indicadores.… (+11 more)

### Community 7 - "Community 7"
Cohesion: 0.07
Nodes (12): _cache_control_y_etag(), get, Request, raiz(), _rate_limit_exceeded(), Punto de entrada de la API (sección 8: FastAPI + OpenAPI en /docs). CORS…, exception_handler, JSONResponse (+4 more)

### Community 8 - "Community 8"
Cohesion: 0.12
Nodes (21): Internacional_ACLED, _normalizar(), Lineage, Path, Capa departamental: admin1 semanal → departamento-año (EVENTS y FATALITIES)., Sin tildes, minúsculas, no alfanumérico → '_' (para emparejar nombres)., nombre normalizado de departamento → código DIVIPOLA (2 dígitos)., archivos_acled() (+13 more)

### Community 9 - "Community 9"
Cohesion: 0.07
Nodes (26): dependencies, maplibre-gl, react, react-dom, devDependencies, @types/react, @types/react-dom, typescript (+18 more)

### Community 10 - "Community 10"
Cohesion: 0.11
Nodes (15): Conector de comparabilidad internacional (sección 5.2). La capa de…, Internacional_UNHCR, DataFrame, Lineage, Internacional_WorldBank, DataFrame, Lineage, Devuelve {codigo_indicator: nombre} desde WB_INDICADORES. (+7 more)

### Community 11 - "Community 11"
Cohesion: 0.11
Nodes (14): IDEAM_Ambiental, DataFrame, Lineage, Path, fixture, simular_servicios(), pipeline_sintetico(), _raster_sintetico() (+6 more)

### Community 12 - "Community 12"
Cohesion: 0.12
Nodes (16): _agregar_soql(), Fiscalia_Estadisticas, DataFrame, Lineage, Consulta agregada de SoQL ($select/$group) con paginación por offset., _df_agregado(), Pruebas del conector Fiscalía V3 (plan2.md Fase B, fuente 3). El pipeline usa…, Debe pedir count(*) + $group, no filas individuales (diseño por volumen). (+8 more)

### Community 13 - "Community 13"
Cohesion: 0.12
Nodes (13): Internacional_HDX, DataFrame, Lineage, Resuelve la URL de descarga (S3 firmada) vía resource_show de CKAN., _url_firmada(), _df_conflictos(), Pruebas del conector HDX HAPI (plan2.md Fase B, fuente 4). Replica el shape…, Debe resolver la URL de descarga (S3 firmada) con resource_show. (+5 more)

### Community 14 - "Community 14"
Cohesion: 0.09
Nodes (21): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+13 more)

### Community 15 - "Community 15"
Cohesion: 0.13
Nodes (14): CNMH_Memoria, DataFrame, Lineage, _df_casos(), _df_victimas(), Pruebas del conector CNMH SIEVCAC (plan2.md Fase B, fuente 2). DataFrames que…, La paginación $limit/$offset debe cubrir datasets > 50.000 filas (desaparición…, _Resp (+6 more)

### Community 16 - "Community 16"
Cohesion: 0.15
Nodes (18): get_fuentes(), get_health(), get_indicador(), get_indicador_total(), get_pdet_proyectos(), get_territorio(), get, Rutas núcleo de la API v1 (sección 8). (+10 more)

### Community 17 - "Community 17"
Cohesion: 0.19
Nodes (15): periodo_anual(), Periodo flexible (sección 7.1): un año completo., encontrar_columna(), Devuelve la primera columna que existe entre los aliases; falla si ninguna. Los…, DANE_Poblacion, _detectar_fila_encabezado(), _leer_excel_dane(), _normalizar() (+7 more)

### Community 18 - "Community 18"
Cohesion: 0.18
Nodes (15): BytesIO, DescargaDemasiadoGrande, descargar_a_buffer(), descargar_con_limite(), Descargas HTTP con límite de tamaño (auditoría 2026-08-02). Los pipelines traen…, La respuesta excede el límite de tamaño configurado., Descarga con stream y verificación de tamaño antes de acumular en memoria.…, Variante que devuelve un BytesIO (consumo directo de pandas.read_csv). (+7 more)

### Community 19 - "Community 19"
Cohesion: 0.12
Nodes (15): raw.cnmh_acciones, raw.cnmh_atentados, raw.cnmh_bienes, raw.cnmh_desaparicion, raw.cnmh_minas, raw.cnmh_reclutamiento, raw.fiscalia_procesos, raw.fiscalia_victimas (+7 more)

### Community 20 - "Community 20"
Cohesion: 0.24
Nodes (14): ErrorOut, FuenteEstadoOut, FuenteOut, HealthOut, IndicadorTotalOut, MapaFeatureOut, MapaOut, MunicipioOut (+6 more)

### Community 21 - "Community 21"
Cohesion: 0.14
Nodes (5): Pruebas de la configuración centralizada de fuentes (plan2.md, Fase A). Sin red…, Crítico: un default no-None rompería el Excel real de DANE (NaN fix)., Los valores de `variable` deben ser campos reales de Settings, salvo plantillas…, test_dane_poblacion_hoja_por_defecto_es_none(), test_fuentes_yaml_referencian_campos_reales()

### Community 22 - "Community 22"
Cohesion: 0.22
Nodes (12): consultar_serie(), consultar_total(), contar_proyectos_pdet(), _cursor_payload(), exportar_serie_csv(), Servicios de acceso a datos desde curated (solo lectura, sección 7.3)., Conteos del módulo PDET (sección 11 del plan): proyectos, municipios PDET y…, Total nacional por año de un indicador (para KPIs del dashboard). Suma todas… (+4 more)

### Community 23 - "Community 23"
Cohesion: 0.31
Nodes (12): DataFrameModel, Valida un DataFrame contra el contrato y devuelve (datos válidos, rechazados).…, validar(), parametrize, _df_valido(), Pruebas de la validación con Pandera (secciones 7.4 y 12)., test_validar_acepta_serie_correcta(), test_validar_codigos_digitos_ok() (+4 more)

### Community 24 - "Community 24"
Cohesion: 0.21
Nodes (10): Config, encontrar_columna_opcional(), EsquemaBase, EsquemaSerieNormalizada, DataFrame, Validación de datos con contratos (sección 4.1 y 12). Los pipelines validan…, Contrato mínimo para toda serie: territorio, periodo y valor numérico. Nota: la…, Formato normalizado que consume insertar_serie (etl/common/cargar.py). Es el… (+2 more)

### Community 25 - "Community 25"
Cohesion: 0.44
Nodes (10): curated, curated.capa_contexto_territorial, curated.departamento, curated.fuentes, curated.indicador_internacional, curated.indicadores, curated.municipio, curated.serie_historica (+2 more)

### Community 26 - "Community 26"
Cohesion: 0.24
Nodes (9): _leer_municipios(), Connection, Siembra la capa geo de municipios (tipo 'divipola') en…, _reportar_cobertura(), sembrar(), _url_firmada(), Connection, Conexión perezosa: solo se abre al ejecutar el pipeline. (+1 more)

### Community 27 - "Community 27"
Cohesion: 0.33
Nodes (9): Convierte NaN/NaT/NA a None recursivamente (hallazgo de auditoría 2026-08-02).…, sanear_json(), Pruebas del saneo NaN→None en la frontera jsonb (hallazgo de auditoría…, test_dict_anidado_sanea_recursivamente(), test_fecha_se_conserva(), test_nan_float_escala_a_none(), test_numpy_nan_a_none(), test_pandas_na_y_nat_a_none() (+1 more)

### Community 28 - "Community 28"
Cohesion: 0.27
Nodes (8): hash_registro(), Lineage, date, Hash determinista del contenido de una fila para detección de…, Pruebas del módulo de linaje (sección 3, punto 4)., test_hash_determinista(), test_hash_sensible_al_orden_y_contenido(), test_lineage_completo()

### Community 29 - "Community 29"
Cohesion: 0.31
Nodes (10): "curated"."capa_contexto_territorial", "curated"."departamento", "curated"."fuentes", "curated"."indicador_internacional", "curated"."indicadores", "curated"."municipio", "curated"."pdet_proyectos", "curated"."serie_historica" (+2 more)

### Community 30 - "Community 30"
Cohesion: 0.46
Nodes (3): ART_PDET, DataFrame, Lineage

### Community 31 - "Community 31"
Cohesion: 0.32
Nodes (8): pg_attribute, pg_class, pg_namespace, pg_type, "public"."geography_columns", "public"."geometry_columns", "public"."spatial_ref_sys", "public"."updategeometrysrid"()

### Community 32 - "Community 32"
Cohesion: 0.50
Nodes (4): get_indicador_csv(), Request, limit, StreamingResponse

### Community 33 - "Community 33"
Cohesion: 0.50
Nodes (4): get_mapa(), consultar_mapa(), Capa coroplética municipal (fase 5): GeoJSON simplificado. Une el agregado…, MapaOut

### Community 34 - "Community 34"
Cohesion: 0.50
Nodes (3): estado_fuentes(), Estado de configuración de fuentes para el healthcheck (plan2.md, Fase A punto…, Por fuente: variable configurada + último pipeline exitoso en la BD.

## Knowledge Gaps
- **62 isolated node(s):** `name`, `private`, `version`, `type`, `dev` (+57 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PipelineETL` connect `Community 3` to `Community 1`, `Community 2`, `Community 5`, `Community 6`, `Community 8`, `Community 10`, `Community 11`, `Community 12`, `Community 13`, `Community 15`, `Community 17`, `Community 24`, `Community 26`, `Community 30`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `Internacional_ACLED` connect `Community 8` to `Community 24`, `Community 3`, `Community 6`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Why does `transaccion()` connect `Community 6` to `Community 2`, `Community 3`, `Community 5`, `Community 10`, `Community 17`, `Community 24`, `Community 26`, `Community 30`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `PipelineETL` (e.g. with `DANE_Poblacion` and `Fiscalia_Estadisticas`) actually correct?**
  _`PipelineETL` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `name`, `private`, `version` to the rest of the system?**
  _62 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.0036429872495446266 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.05442176870748299 - nodes in this community are weakly interconnected._