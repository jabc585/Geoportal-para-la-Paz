# Graph Report - grafiphy  (2026-08-03)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1494 nodes · 2432 edges · 73 communities (57 shown, 16 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 86 edges (avg confidence: 0.59)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e1558e43`
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
- Community 51
- Community 52
- Community 53
- Community 54
- Community 55
- Community 59
- Community 60
- Community 61

## God Nodes (most connected - your core abstractions)
1. `Lineage` - 45 edges
2. `PipelineETL` - 37 edges
3. `transaccion()` - 33 edges
4. `insertar_serie()` - 32 edges
5. `upsert_fuente()` - 29 edges
6. `validar()` - 29 edges
7. `Internacional_ACLED` - 26 edges
8. `upsert_indicador()` - 22 edges
9. `periodo_anual()` - 22 edges
10. `EsquemaSerieNormalizada` - 21 edges

## Surprising Connections (you probably didn't know these)
- `test_slugificar_empareja_tildes_y_puntos()` --calls--> `slugificar()`  [EXTRACTED]
  tests/test_acled.py → etl/common/cargar.py
- `test_slugificar()` --calls--> `slugificar()`  [EXTRACTED]
  tests/test_pipelines.py → etl/common/cargar.py
- `ConexionFake` --uses--> `Lineage`  [INFERRED]
  tests/test_ejecutar.py → etl/common/lineage.py
- `CursorFake` --uses--> `Lineage`  [INFERRED]
  tests/test_ejecutar.py → etl/common/lineage.py
- `FakePipeline` --uses--> `Lineage`  [INFERRED]
  tests/test_ejecutar.py → etl/common/lineage.py

## Import Cycles
- None detected.

## Communities (73 total, 16 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.00
Nodes (22): "curated"."audit_log", "curated"."data_quality_metrics", "raw"."art_pdet", "raw"."cnmh_acciones", "raw"."cnmh_atentados", "raw"."cnmh_bienes", "raw"."cnmh_desaparicion", "raw"."cnmh_minas" (+14 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (80): _get_pool(), obtener_conexion(), Connection, Pool de conexiones para la API (plan3.md, Fase 1.8). Las funciones de servicio…, Devuelve una conexión del pool (ya con autocommit=True para solo lectura)., Instancia compartida de slowapi Limiter (Fase 0.3, plan3.md). Un solo limiter…, _cabeceras_seguridad(), _cache_control() (+72 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (37): periodo_maximo(), Fecha de corte real de un lote: el periodo más reciente que trae la fuente. Se…, conectar(), Abre una conexión con semántica transaccional real (auditoría 2026-08-02).…, _descargar(), Connection, Seed del catálogo territorial DIVIPOLA (secciones 5.1 y 7.2). Descarga los…, sembrar_departamentos() (+29 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (36): DOCS_URL, Frescura, Fuente, healthcheck(), IndicadorTotal, MapaFeature, MapaIndicador, obtener() (+28 more)

### Community 4 - "Community 4"
Cohesion: 0.06
Nodes (35): insertar_raw(), ordinales_por_hash(), Connection, Inserta en raw.<tabla> el contenido no visto antes, conservando linaje.…, Registra métricas de calidad de la corrida (sección 7.4)., Convierte NaN/NaT/NA a None recursivamente (hallazgo de auditoría 2026-08-02).…, Numera 0,1,2… cada repetición del mismo `hash_fila` dentro del lote. Es la…, registrar_metricas() (+27 more)

### Community 5 - "Community 5"
Cohesion: 0.17
Nodes (20): DataFrameModel, insertar_serie(), Connection, Carga a curated con resolución de catálogos y linaje (secciones 7 y 12).…, Inserta filas normalizadas en curated.serie_historica con deduplicación por…, Normaliza un texto a código seguro: minúsculas, sin acentos, guiones bajos., Inserta o recupera el fuente_id del catálogo curated.fuentes. codigo (slug…, Inserta o recupera el indicador_id del catálogo curated.indicadores.… (+12 more)

### Community 6 - "Community 6"
Cohesion: 0.10
Nodes (21): Internacional_ACLED, DataFrame, Path, Corte real de los agregados, derivado de los datos que trae el export. Antes…, Capa departamental: admin1 semanal → departamento-año (EVENTS y FATALITIES)., Capa departamental: departamento-año → curated.serie_historica., nombre normalizado de departamento → código DIVIPOLA (2 dígitos)., archivos_acled() (+13 more)

### Community 7 - "Community 7"
Cohesion: 0.08
Nodes (35): periodo_anual(), Periodo flexible (sección 7.1): un año completo., DANE_Poblacion, _detectar_fila_encabezado(), _leer_excel_dane(), _normalizar_columnas(), DataFrame, Conector piloto DANE (población) - fuente de la fase 2 del plan. Acceso real… (+27 more)

### Community 8 - "Community 8"
Cohesion: 0.11
Nodes (18): _check(), get_source_url(), _inyectar_al_entorno(), Configuración centralizada de fuentes (plan2.md, Fase A). Carga automática de…, Puente para los 4 pipelines legacy (DANE, Víctimas, PDET, World Bank): siguen…, Para pipelines nuevos (Fase B): valida en el punto de uso, no al importar., Comando opt-in (plan2.md, Fase A punto 8): reporta qué variables de fuentes…, descargar_socrata_paginado() (+10 more)

### Community 9 - "Community 9"
Cohesion: 0.11
Nodes (21): Policia_Delitos, Policia_Homicidios, DataFrame, Homicidios intencionales: Excel oficial SIEDCO de policia.gov.co. El Excel trae…, Variable configurada (URLs separadas por coma) o patrón por año., _df_homicidios(), _df_hurto(), _excel_homicidios_bytes() (+13 more)

### Community 10 - "Community 10"
Cohesion: 0.13
Nodes (12): ConexionFake, CursorFake, FakePipeline, _mock_conexion(), Tests de PipelineETL.ejecutar(): los 6 caminos donde se introdujeron los bugs…, Pipeline sintético con parámetros inyectables para cada camino., test_ejecutar_canal_lateral_con_leidos(), test_ejecutar_exito_simple() (+4 more)

### Community 11 - "Community 11"
Cohesion: 0.14
Nodes (18): datetime, Conexión a base de datos y registro de métricas de calidad (secciones 7.3 y…, archivo_raw(), hash_registro(), Linaje de datos obligatorio (sección 3, punto 4 y sección 7). Todo registro…, Hash determinista del contenido de una fila para detección de…, Marca de inmutabilidad: los datos crudos se almacenan tal como se descargan., Plantilla base de pipeline ETL con trazabilidad y métricas (secciones 7.4 y… (+10 more)

### Community 12 - "Community 12"
Cohesion: 0.20
Nodes (12): Config, encontrar_columna(), encontrar_columna_opcional(), EsquemaBase, EsquemaSerieNormalizada, DataFrame, Validación de datos con contratos (sección 4.1 y 12). Los pipelines validan…, Contrato mínimo para toda serie: territorio, periodo y valor numérico. Nota: la… (+4 more)

### Community 13 - "Community 13"
Cohesion: 0.13
Nodes (12): IDEAM_Ambiental, DataFrame, Path, pipeline_sintetico(), fixture, _raster_sintetico(), Pruebas del conector IDEAM (raster de deforestación, plan2.md Fase C). Usan un…, 8x8 píxeles, 100 m (1 ha). Deforestación (2) en el bloque 2x2 superior… (+4 more)

### Community 14 - "Community 14"
Cohesion: 0.11
Nodes (18): BytesIO, DescargaDemasiadoGrande, descargar_a_buffer(), descargar_con_limite(), La respuesta excede el límite de tamaño configurado., Descarga con stream y verificación de tamaño antes de acumular en memoria.…, Variante que devuelve un BytesIO (consumo directo de pandas.read_csv)., Tests de la lógica de siembra geo (plan.md §F2.4). (+10 more)

### Community 15 - "Community 15"
Cohesion: 0.09
Nodes (5): FUENTES, MapaFalso, mockFetchOk(), PopupFalso, respuesta()

### Community 16 - "Community 16"
Cohesion: 0.09
Nodes (22): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+14 more)

### Community 17 - "Community 17"
Cohesion: 0.12
Nodes (15): _agregar_soql(), Fiscalia_Estadisticas, DataFrame, Consulta agregada de SoQL ($select/$group) con paginación por offset., _df_agregado(), Pruebas del conector Fiscalía V3 (plan2.md Fase B, fuente 3). El pipeline usa…, Debe pedir count(*) + $group, no filas individuales (diseño por volumen)., _Resp (+7 more)

### Community 18 - "Community 18"
Cohesion: 0.12
Nodes (12): Internacional_HDX, DataFrame, Resuelve la URL de descarga (S3 firmada) vía resource_show de CKAN., _url_firmada(), _df_conflictos(), Pruebas del conector HDX HAPI (plan2.md Fase B, fuente 4). Replica el shape…, Debe resolver la URL de descarga (S3 firmada) con resource_show., _Resp (+4 more)

### Community 19 - "Community 19"
Cohesion: 0.15
Nodes (12): DataFrame, Fila "SIN DEFINIR" del RUV a nivel nacional (municipio_id NULL). Postgres no…, Agrega sujetos de atención (per_sa) por municipio y año de corte., Victimas_Hechos, test_victimas_transformar_agrega_por_tipo(), _fake_get_socrata(), Tests del conector de víctimas (UARIV vía Socrata municipal, dataset…, _RespJson (+4 more)

### Community 20 - "Community 20"
Cohesion: 0.10
Nodes (3): fixture, Pruebas de la API v1 (sección 8) con servicios simulados — sin BD., simular_servicios()

### Community 21 - "Community 21"
Cohesion: 0.14
Nodes (11): Conector de comparabilidad internacional (sección 5.2). La capa de…, Internacional_WorldBank, DataFrame, Devuelve {codigo_indicator: nombre} desde WB_INDICADORES., Pruebas de los conectores internacionales (secciones 5.2, 7.6; plan2.md Fase B)., Replica el shape real de la API (verificado en vivo 2026-08-02)., Los 8 tipos que expone la API real deben estar mapeados., test_transformar_limpia_valores() (+3 more)

### Community 22 - "Community 22"
Cohesion: 0.16
Nodes (12): CNMH_Memoria, _df_casos(), _df_victimas(), Pruebas del conector CNMH SIEVCAC (plan2.md Fase B, fuente 2). DataFrames que…, La paginación $limit/$offset debe cubrir datasets > 50.000 filas (desaparición…, _Resp, test_extraer_paginacion_real(), test_hecho_desconocido_rechazado() (+4 more)

### Community 23 - "Community 23"
Cohesion: 0.15
Nodes (10): BaseSettings, Settings, Pruebas de la configuración centralizada de fuentes (plan2.md, Fase A). Sin red…, Crítico: un default no-None rompería el Excel real de DANE (NaN fix)., Los valores de `variable` deben ser campos reales de Settings, salvo plantillas…, test_dane_poblacion_hoja_por_defecto_es_none(), test_fuentes_yaml_referencian_campos_reales(), test_get_source_url_devuelve_valor() (+2 more)

### Community 24 - "Community 24"
Cohesion: 0.12
Nodes (15): raw.cnmh_acciones, raw.cnmh_atentados, raw.cnmh_bienes, raw.cnmh_desaparicion, raw.cnmh_minas, raw.cnmh_reclutamiento, raw.fiscalia_procesos, raw.fiscalia_victimas (+7 more)

### Community 25 - "Community 25"
Cohesion: 0.16
Nodes (15): _leer_municipios(), Connection, Siembra la capa geo de municipios (tipo 'divipola') en…, _reportar_cobertura(), sembrar(), _url_firmada(), insertar_indicador_internacional(), marcar_fuente_actualizada() (+7 more)

### Community 26 - "Community 26"
Cohesion: 0.19
Nodes (10): ABC, _nulos_columnas_criticas(), PipelineETL, DataFrame, Conteo de nulos por columna crítica del staging (hallazgo 14 auditoría…, Pipeline base: extrae, carga crudo con linaje y reporta métricas de calidad., Descarga los datos crudos y devuelve (dataframe, linaje)., Normaliza a staging (códigos DIVIPOLA, periodos, valores numéricos). (+2 more)

### Community 27 - "Community 27"
Cohesion: 0.13
Nodes (15): dependencies, @fontsource-variable/inter, @fontsource-variable/jetbrains-mono, lucide-react, maplibre-gl, react, react-dom, recharts (+7 more)

### Community 28 - "Community 28"
Cohesion: 0.15
Nodes (15): devDependencies, jsdom, tailwindcss, @testing-library/dom, @testing-library/jest-dom, @testing-library/react, @types/react-dom, @vitejs/plugin-react (+7 more)

### Community 29 - "Community 29"
Cohesion: 0.44
Nodes (10): curated, curated.capa_contexto_territorial, curated.departamento, curated.fuentes, curated.indicador_internacional, curated.indicadores, curated.municipio, curated.serie_historica (+2 more)

### Community 30 - "Community 30"
Cohesion: 0.27
Nodes (11): "curated"."capa_contexto_territorial", "curated"."departamento", "curated"."fuentes", "curated"."indicador_internacional", "curated"."indicadores", "curated"."municipio", "curated"."pdet_proyectos", "curated"."serie_historica" (+3 more)

### Community 31 - "Community 31"
Cohesion: 0.20
Nodes (9): allowScripts, esbuild@0.21.5, esbuild@0.28.1, fsevents@2.3.3, @tailwindcss/oxide@4.1.12, name, private, type (+1 more)

### Community 32 - "Community 32"
Cohesion: 0.31
Nodes (8): obtener_logger_etl(), Logging estructurado para ETL y API (plan3.md, Fase 4.19). Reemplaza los…, Logger con ``run_id`` fijo para toda la corrida de un pipeline., _setup_logger(), _presupuesto_duracion(), Ejecuta los 18 pipelines activos (sección 21, pasos 4 y 11). Activos: DANE,…, run_all(), Logger

### Community 33 - "Community 33"
Cohesion: 0.27
Nodes (7): _JSONFormatter, LogRecord, Tests del formateador JSON de logs (plan.md §F2.4)., test_formatter_incluye_error_en_excepcion(), test_formatter_produce_json_valido(), test_formatter_sin_exc_info_no_incluye_error(), test_obtener_logger_etl_tiene_run_id()

### Community 34 - "Community 34"
Cohesion: 0.27
Nodes (9): TestClient, _app_con_limite(), Test de integración: el rate limiter debe proteger la app real con…, 10 requests a /api/v1/fuentes con límite 5/min → al menos un 429., El endpoint /health también debe ser rate-limited., El decorador @limiter.limit('10/minute') de exportar.csv., test_rate_limiter_protege_health(), test_rate_limiter_protege_rutas() (+1 more)

### Community 35 - "Community 35"
Cohesion: 0.33
Nodes (9): _df_valido(), parametrize, Pruebas de la validación con Pandera (secciones 7.4 y 12)., test_validar_acepta_serie_correcta(), test_validar_codigos_digitos_ok(), test_validar_datos_vacios_no_falla(), test_validar_rechaza_codigo_divipola_invalido(), test_validar_rechaza_periodo_incoherente() (+1 more)

### Community 37 - "Community 37"
Cohesion: 0.32
Nodes (8): pg_attribute, pg_class, pg_namespace, pg_type, "public"."geography_columns", "public"."geometry_columns", "public"."spatial_ref_sys", "public"."updategeometrysrid"()

### Community 38 - "Community 38"
Cohesion: 0.29
Nodes (6): curated.indicadores, curated.serie_historica, curated.vw_homicidios_reconciliado, curated.departamento, curated.fuentes, curated.municipio

### Community 39 - "Community 39"
Cohesion: 0.33
Nodes (6): scripts, build, dev, preview, test, test:watch

### Community 40 - "Community 40"
Cohesion: 0.40
Nodes (4): curated.pdet_proyectos, curated.departamento, curated.fuentes, curated.municipio

### Community 41 - "Community 41"
Cohesion: 0.50
Nodes (3): raw.art_pdet, raw.dane_poblacion, raw.victimas_hechos

## Knowledge Gaps
- **83 isolated node(s):** `name`, `private`, `version`, `type`, `dev` (+78 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Lineage` connect `Community 8` to `Community 5`, `Community 6`, `Community 7`, `Community 9`, `Community 10`, `Community 11`, `Community 12`, `Community 13`, `Community 17`, `Community 18`, `Community 19`, `Community 21`, `Community 22`, `Community 26`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Why does `PipelineETL` connect `Community 26` to `Community 2`, `Community 5`, `Community 6`, `Community 7`, `Community 8`, `Community 9`, `Community 10`, `Community 11`, `Community 12`, `Community 13`, `Community 17`, `Community 18`, `Community 19`, `Community 21`, `Community 22`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Why does `transaccion()` connect `Community 5` to `Community 2`, `Community 4`, `Community 6`, `Community 7`, `Community 8`, `Community 11`, `Community 12`, `Community 21`, `Community 25`?**
  _High betweenness centrality (0.011) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `Lineage` (e.g. with `PipelineETL` and `DANE_Poblacion`) actually correct?**
  _`Lineage` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `PipelineETL` (e.g. with `Lineage` and `DANE_Poblacion`) actually correct?**
  _`PipelineETL` has 16 INFERRED edges - model-reasoned connections that need verification._
- **What connects `name`, `private`, `version` to the rest of the system?**
  _83 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.0036429872495446266 - nodes in this community are weakly interconnected._