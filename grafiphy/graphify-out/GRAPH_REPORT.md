# Graph Report - /Users/robot/Documents/Observatorio/Geoportal-para-la-Paz/grafiphy  (2026-08-02)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1045 nodes · 1407 edges · 38 communities (32 shown, 6 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 25 edges (avg confidence: 0.54)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `aea95b0b`
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
- Community 31
- Community 34
- Community 35
- Community 37

## God Nodes (most connected - your core abstractions)
1. `PipelineETL` - 31 edges
2. `Lineage` - 18 edges
3. `validar()` - 17 edges
4. `compilerOptions` - 16 edges
5. `get_source_url()` - 15 edges
6. `Internacional_ACLED` - 15 edges
7. `Fiscalia_Estadisticas` - 14 edges
8. `CNMH_Memoria` - 14 edges
9. `Policia_Delitos` - 14 edges
10. `DANE_Poblacion` - 13 edges

## Surprising Connections (you probably didn't know these)
- `test_slugificar()` --calls--> `slugificar()`  [EXTRACTED]
  tests/test_pipelines.py → etl/common/cargar.py
- `listar_fuentes()` --calls--> `conectar()`  [EXTRACTED]
  api/services/consultas.py → etl/common/db.py
- `consultar_territorio()` --calls--> `conectar()`  [EXTRACTED]
  api/services/consultas.py → etl/common/db.py
- `test_periodo_anual()` --calls--> `periodo_anual()`  [EXTRACTED]
  tests/test_pipelines.py → etl/common/cargar.py
- `test_dict_anidado_sanea_recursivamente()` --calls--> `sanear_json()`  [EXTRACTED]
  tests/test_db.py → etl/common/db.py

## Import Cycles
- None detected.

## Communities (38 total, 6 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.00
Nodes (20): "curated"."audit_log", "curated"."data_quality_metrics", "raw"."art_pdet", "raw"."cnmh_acciones", "raw"."cnmh_atentados", "raw"."cnmh_bienes", "raw"."cnmh_desaparicion", "raw"."cnmh_minas" (+12 more)

### Community 1 - "Community 1"
Cohesion: 0.09
Nodes (24): get, raiz(), Punto de entrada de la API (sección 8: FastAPI + OpenAPI en /docs). CORS…, ErrorOut, FuenteEstadoOut, FuenteOut, HealthOut, MunicipioOut (+16 more)

### Community 2 - "Community 2"
Cohesion: 0.11
Nodes (27): consultar_serie(), consultar_territorio(), _cursor_payload(), listar_fuentes(), Servicios de acceso a datos desde curated (solo lectura, sección 7.3)., Serie histórica con paginación basada en cursor (sección 8). El cursor codifica…, conectar(), insertar_raw() (+19 more)

### Community 3 - "Community 3"
Cohesion: 0.20
Nodes (14): insertar_serie(), Connection, DataFrame, Carga a curated con resolución de catálogos y linaje (secciones 7 y 12).…, Inserta filas normalizadas en curated.serie_historica con deduplicación por…, Normaliza un texto a código seguro: minúsculas, sin acentos, guiones bajos., Inserta o recupera el fuente_id del catálogo curated.fuentes. codigo (slug…, Inserta o recupera el indicador_id del catálogo curated.indicadores.… (+6 more)

### Community 4 - "Community 4"
Cohesion: 0.11
Nodes (14): hash_registro(), Lineage, date, Hash determinista del contenido de una fila para detección de…, IDEAM_Ambiental, DataFrame, Conector de comparabilidad internacional (sección 5.2). La capa de…, Internacional_WorldBank (+6 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (26): dependencies, maplibre-gl, react, react-dom, devDependencies, @types/react, @types/react-dom, typescript (+18 more)

### Community 6 - "Community 6"
Cohesion: 0.11
Nodes (16): _agregar_soql(), Fiscalia_Estadisticas, DataFrame, Lineage, Consulta agregada de SoQL ($select/$group) con paginación por offset., _df_agregado(), Pruebas del conector Fiscalía V3 (plan2.md Fase B, fuente 3). El pipeline usa…, Debe pedir count(*) + $group, no filas individuales (diseño por volumen). (+8 more)

### Community 7 - "Community 7"
Cohesion: 0.11
Nodes (16): CNMH_Memoria, _descargar(), DataFrame, Lineage, Descarga paginada de Socrata ($limit/$offset, sin token)., _df_casos(), _df_victimas(), Pruebas del conector CNMH SIEVCAC (plan2.md Fase B, fuente 2). DataFrames que… (+8 more)

### Community 8 - "Community 8"
Cohesion: 0.13
Nodes (13): Internacional_HDX, DataFrame, Lineage, Resuelve la URL de descarga (S3 firmada) vía resource_show de CKAN., _url_firmada(), _df_conflictos(), Pruebas del conector HDX HAPI (plan2.md Fase B, fuente 4). Replica el shape…, Debe resolver la URL de descarga (S3 firmada) con resource_show. (+5 more)

### Community 9 - "Community 9"
Cohesion: 0.12
Nodes (13): ABC, archivo_raw(), Linaje de datos obligatorio (sección 3, punto 4 y sección 7). Todo registro…, Marca de inmutabilidad: los datos crudos se almacenan tal como se descargan., Plantilla base de pipeline ETL con trazabilidad y métricas (secciones 7.4 y…, Conector de estadísticas judiciales: Fiscalía V3 (plan2.md Fase B, fuente 3).…, Conector IDEAM (esqueleto - sección 21, paso 11). Fuente: variables ambientales…, Conector internacional: ACLED (agregados país-año, archivos locales). ACLED… (+5 more)

### Community 10 - "Community 10"
Cohesion: 0.09
Nodes (21): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+13 more)

### Community 11 - "Community 11"
Cohesion: 0.16
Nodes (13): Internacional_ACLED, DataFrame, Lineage, Path, archivos_acled(), fixture, Tests del conector ACLED (agregados país-año en archivos locales)., Genera un XLSX mínimo por archivo esperado en un directorio temporal. (+5 more)

### Community 12 - "Community 12"
Cohesion: 0.16
Nodes (9): Internacional_UNHCR, DataFrame, Lineage, Pruebas de los conectores internacionales (secciones 5.2, 7.6; plan2.md Fase B)., Replica el shape real de la API (verificado en vivo 2026-08-02)., Los 8 tipos que expone la API real deben estar mapeados., test_unhcr_extraer_shape_real(), test_unhcr_tipos_poblacion_completos() (+1 more)

### Community 13 - "Community 13"
Cohesion: 0.16
Nodes (13): _descargar(), Policia_Delitos, DataFrame, Lineage, Descarga paginada de Socrata ($limit/$offset, sin token)., _df_hurto(), Pruebas del conector Policía Nacional (plan2.md Fase B, fuente 5). Replica los…, test_delito_desconocido_rechazado() (+5 more)

### Community 14 - "Community 14"
Cohesion: 0.14
Nodes (12): BaseSettings, get_source_url(), Para pipelines nuevos (Fase B): valida en el punto de uso, no al importar., Settings, Pruebas de la configuración centralizada de fuentes (plan2.md, Fase A). Sin red…, Crítico: un default no-None rompería el Excel real de DANE (NaN fix)., Los valores de `variable` deben ser campos reales de Settings, salvo plantillas…, test_dane_poblacion_hoja_por_defecto_es_none() (+4 more)

### Community 15 - "Community 15"
Cohesion: 0.17
Nodes (15): DANE_Poblacion, Victimas_Hechos, Pruebas del ciclo de transformación/carga de los pipelines piloto. Las…, Ejecuta extraer+transformar con un Excel que replica el layout real (metadata,…, El suplemento de ANMs debe tener (codigo, nombre, codigo_depto) válidos., Formato verificado en auditoría: encabezado fila 9, columna MPIO, y 3 filas por…, Legacy Socrata sin columna de área: no se descarta nada., test_dane_pipeline_completo_contra_excel_con_footer() (+7 more)

### Community 16 - "Community 16"
Cohesion: 0.19
Nodes (9): Fuente, obtener(), obtenerFuentes(), App(), Footer(), KPIFuentes(), MapaNacional(), Inicio() (+1 more)

### Community 17 - "Community 17"
Cohesion: 0.12
Nodes (15): raw.cnmh_acciones, raw.cnmh_atentados, raw.cnmh_bienes, raw.cnmh_desaparicion, raw.cnmh_minas, raw.cnmh_reclutamiento, raw.fiscalia_procesos, raw.fiscalia_victimas (+7 more)

### Community 18 - "Community 18"
Cohesion: 0.18
Nodes (9): Connection, PipelineETL, DataFrame, Lineage, Pipeline base: extrae, carga crudo con linaje y reporta métricas de calidad., Conexión perezosa: solo se abre al ejecutar el pipeline., Descarga los datos crudos y devuelve (dataframe, linaje)., Normaliza a staging (códigos DIVIPOLA, periodos, valores numéricos). (+1 more)

### Community 19 - "Community 19"
Cohesion: 0.27
Nodes (13): DataFrameModel, DataFrame, Valida un DataFrame contra el contrato y devuelve (datos válidos, rechazados).…, validar(), parametrize, _df_valido(), Pruebas de la validación con Pandera (secciones 7.4 y 12)., test_validar_acepta_serie_correcta() (+5 more)

### Community 20 - "Community 20"
Cohesion: 0.21
Nodes (14): _columna(), _detectar_fila_encabezado(), _leer_excel_dane(), _normalizar(), _normalizar_columnas(), DataFrame, Conector piloto DANE (población) - fuente de la fase 2 del plan. Acceso real…, Minúsculas, sin acentos y espacios a guion bajo (p. ej. 'ÁREA GEOGRÁFICA'). (+6 more)

### Community 21 - "Community 21"
Cohesion: 0.22
Nodes (10): ART_PDET, _columna(), _columna_opcional(), DataFrame, Conector piloto ART/PDET - fuente de la fase 2 del plan. Acceso: datos abiertos…, Shape real de 'Iniciativas PDET' (datos.gov.co/gmvf-t63e, auditoría…, extraer() contra la forma de respuesta real del dataset Iniciativas PDET: las…, test_pdet_pipeline_completo_con_respuesta_real() (+2 more)

### Community 22 - "Community 22"
Cohesion: 0.31
Nodes (10): "curated"."capa_contexto_territorial", "curated"."departamento", "curated"."fuentes", "curated"."indicador_internacional", "curated"."indicadores", "curated"."municipio", "curated"."pdet_proyectos", "curated"."serie_historica" (+2 more)

### Community 23 - "Community 23"
Cohesion: 0.25
Nodes (6): _check(), _inyectar_al_entorno(), Configuración centralizada de fuentes (plan2.md, Fase A). Carga automática de…, Puente para los 4 pipelines legacy (DANE, Víctimas, PDET, World Bank): siguen…, Comando opt-in (plan2.md, Fase A punto 8): reporta qué variables de fuentes…, Conector internacional: UNHCR/ACNUR (plan2.md Fase B, fuente 1). API pública de…

### Community 24 - "Community 24"
Cohesion: 0.32
Nodes (8): pg_attribute, pg_class, pg_namespace, pg_type, "public"."geography_columns", "public"."geometry_columns", "public"."spatial_ref_sys", "public"."updategeometrysrid"()

### Community 25 - "Community 25"
Cohesion: 0.33
Nodes (6): Config, EsquemaBase, EsquemaSerieNormalizada, Validación de datos con contratos (sección 4.1 y 12). Los pipelines validan…, Contrato mínimo para toda serie: territorio, periodo y valor numérico. Nota: la…, Formato normalizado que consume insertar_serie (etl/common/cargar.py). Es el…

### Community 37 - "Community 37"
Cohesion: 0.33
Nodes (6): periodo_anual(), date, Periodo flexible (sección 7.1): un año completo., _columna(), DataFrame, test_periodo_anual()

## Knowledge Gaps
- **50 isolated node(s):** `name`, `private`, `version`, `type`, `dev` (+45 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PipelineETL` connect `Community 18` to `Community 3`, `Community 4`, `Community 6`, `Community 7`, `Community 8`, `Community 9`, `Community 11`, `Community 12`, `Community 13`, `Community 15`, `Community 20`, `Community 21`, `Community 23`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `Internacional_HDX` connect `Community 8` to `Community 9`, `Community 18`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Why does `Internacional_ACLED` connect `Community 11` to `Community 9`, `Community 18`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `PipelineETL` (e.g. with `DANE_Poblacion` and `Fiscalia_Estadisticas`) actually correct?**
  _`PipelineETL` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `Lineage` (e.g. with `DANE_Poblacion` and `IDEAM_Ambiental`) actually correct?**
  _`Lineage` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `name`, `private`, `version` to the rest of the system?**
  _50 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.003656307129798903 - nodes in this community are weakly interconnected._