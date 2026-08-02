# Plan: centralizar configuración de fuentes (.env) sin tocar la lógica existente

## Contexto

El proyecto tiene hoy 4 pipelines reales funcionando (DANE, Víctimas, PDET, Banco
Mundial) y 4 esqueletos que lanzan `NotImplementedError` a propósito (Fiscalía,
Policía, IDEAM, memoria/CNMH) porque nadie había confirmado todavía un endpoint
real para ellos. Cada pipeline lee sus propias variables de entorno con
`os.getenv(...)` inline; no hay un punto central de configuración, y aunque
`python-dotenv` ya está en `requirements.txt`, **no se usa en ningún lugar del
código** (verificado con `grep -rn dotenv --include=*.py .` → 0 resultados) — hoy
`.env` solo funciona si Docker Compose o el shell ya exportaron esas variables.

El usuario propuso centralizar todo en un `.env`/`.env.example` con nomenclatura
`FUENTE_TIPO_DATOS` y un `etl/common/config.py`. La propuesta original inventaba
nombres de variables distintos a los que ya usan los pipelines reales (p. ej.
`VICTIMAS_DATOSPAZ_URL` en vez de `VICTIMAS_URL`, `WB_INDICATORS` en vez de
`WB_INDICADORES`) y varios resource-ids de ejemplo con placeholders falsos
(`xxxx-xxxx`, `yyyy-yyyy`...). Ese renombrado tocaría archivos que ya están
probados y funcionando end-to-end (auditoría 2026-08-02), así que este plan
**no renombra nada existente**: reutiliza los nombres reales tal cual están hoy,
y solo añade lo que falta.

Como parte de este plan ya investigué en vivo (no solo el código) qué fuentes de
las pendientes tienen realmente un endpoint público accesible — igual que se hizo
para DANE/PDET en la auditoría — para no rellenar `.env.example` con URLs
inventadas. Resultados abajo.

**Ronda 2:** se recibió una propuesta de mejoras adicional (Pydantic Settings,
catálogo YAML de fuentes, validación fail-fast, healthcheck, etc.). Es una
propuesta sólida y bien argumentada, pero dos de sus piezas centrales —tocar los
4 pipelines reales y validar todo de forma eager/obligatoria— chocan con la
decisión de diseño ya aprobada (no modificar lógica existente) y, en un caso,
reproducen exactamente el tipo de bug de comportamiento que ya costó una ronda
de auditoría encontrar (el default `"1"` para `DANE_POBLACION_HOJA`). La sección
"Revisión de la propuesta de mejoras" de abajo explica qué se adopta, qué se
ajusta y por qué, antes de tocar la Fase A.

## Decisión de diseño: dónde vive la centralización

**No se toca `etl/dane/pipeline.py`, `etl/pdet/pipeline.py`, `etl/victimas/pipeline.py`
ni `etl/internacional/world_bank.py`.** Sus `os.getenv(...)`, nombres de variable y
mensajes de error de validación quedan exactamente igual — son lógica ya probada
(31 tests, verificado contra fuentes reales en la auditoría, incluyendo una
corrida end-to-end real de DANE que cargó 17.952 filas a `curated`).

La pieza nueva y compartida es `etl/common/config.py`, con una clase `Settings`
tipada (Pydantic) **en vez de** una función suelta — ver la revisión de la
propuesta abajo para el porqué de cada ajuste respecto al diseño original:

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Todas las URLs de fuente son *opcionales* a nivel de Settings: la
    # obligatoriedad se sigue validando en el punto de uso (extraer()), igual
    # que hoy, para no acoplar el arranque de la API o de un pipeline al
    # resto de variables que no usa (ver punto 1 de la revisión).
    database_url: str = "postgresql://observatorio:observatorio_dev@localhost:5432/observatorio"

    dane_poblacion_xlsx_url: str | None = None
    # Sin default "1" ni similar: None preserva el comportamiento real ya
    # probado (sheet_name=hoja or 0 → primera hoja). Un default no-None aquí
    # rompería el Excel real de DANE (ver revisión, punto 1).
    dane_poblacion_hoja: str | None = None
    dane_poblacion_dataset: str | None = None  # legacy, eliminado del pipeline
    victimas_url: str | None = None
    pdet_url: str | None = None
    divipola_dept_dataset: str = "vcjz-niiq"
    divipola_mun_dataset: str = "gdxc-w37w"
    wb_indicadores: str = "NY.GDP.PCAP.PP.CD:PIB per cápita (PPA)"

    # Campos nuevos, solo para pipelines de Fase B (hoy esqueletos, sin
    # lógica que romper):
    unhcr_base_url: str = "https://api.unhcr.org/population/v1"
    hdx_base_url: str = "https://data.humdata.org/api/3"
    policia_hurto_url: str | None = None
    fiscalia_procesos_url: str | None = None
    cnmh_url: str | None = None  # variables específicas por hecho, ver Fase B

    socrata_app_token: str | None = None
    ucdp_api_token: str | None = None
    acled_email: str | None = None
    acled_key: str | None = None


settings = Settings()


def get_source_url(nombre_variable: str, *, ayuda: str = "") -> str:
    """Para pipelines nuevos (Fase B): valida en el punto de uso, no al importar."""
    val = getattr(settings, nombre_variable.lower(), None) or ""
    if not val:
        raise ValueError(f"Variable de entorno {nombre_variable} no definida. {ayuda}")
    return val
```

`etl/common/pipeline.py` (la clase base `PipelineETL` que **todos** los
pipelines ya importan, existentes y nuevos) gana una sola línea:
`from etl.common.config import settings  # noqa: F401 — dispara load_dotenv() al importar`.
Con eso, `.env` se carga automáticamente para cualquier pipeline sin tocar su
cuerpo — resuelve el hallazgo real (dotenv nunca se invoca) sin cambiar el
comportamiento de ningún pipeline existente. `settings`/`get_source_url()`
quedan disponibles para los pipelines **nuevos** (Fase B).

## Revisión de la propuesta de mejoras (ronda 2)

| # | Propuesta | Veredicto | Razón | Impacto en el grafo de arquitectura |
|---|---|---|---|---|
| 1 | Migrar a Pydantic Settings | 🟡 **Adoptar con ajuste** | La propuesta original reemplaza `os.getenv("VICTIMAS_URL")` **dentro de los pipelines reales** por `settings.victimas_url` — eso sí es tocar lógica ya probada, contradice la decisión ya aprobada. Además, `dane_poblacion_hoja: str = Field("1", ...)` **cambia el comportamiento real**: hoy `None` → pandas usa la primera hoja (`sheet_name=hoja or 0`); `"1"` le pediría a pandas la hoja *literalmente llamada* `"1"`, que no existe en el Excel real de DANE (verificado en la auditoría) — habría reventado el único pipeline que sí carga datos reales hoy. Y usar campos `Field(...)` **requeridos** en un único `Settings` singleton eager acopla el arranque de la API (que no usa `DANE_POBLACION_XLSX_URL` para nada) a que esa variable exista. Ajuste adoptado: `Settings` con todos los campos de fuente opcionales (`str \| None = None`), sin tocar los 4 pipelines existentes, y usada solo por `config.py`/pipelines nuevos. | Grafo regenerado 862 nodos/1.139 aristas: se añaden ~6 nodos nuevos (`Settings`, `FUENTES_ACTIVAS`, `get_source_url`, `_check`, módulo `config`) con una sola arista hacia `PipelineETL` (el hub de 26 aristas se mantiene intacto). La variante original (editar los 4 pipelines reales) habría añadido aristas desde los 2 hubs (`PipelineETL`/`Lineage`) a cada pipeline — churn innecesario en los componentes más conectados. |
| 2 | Catálogo YAML de fuentes (`config/fuentes.yaml`) | 🟢 **Adoptar, con alcance acotado** | Buena idea para documentar las fuentes de Fase B/C de forma estructurada. Ajuste: **no** se usa para alimentar `upsert_fuente()` de los 4 pipelines reales (cada uno ya llama `upsert_fuente()` con sus propios kwargs correctos y probados) — el YAML es la fuente de verdad solo para lo nuevo y para generar `.env.example`/docs, no para refactorizar lo que ya funciona. | 2 nodos nuevos de configuración (`config/fuentes.yaml`, `config/investigacion_fuentes.yaml`) sin aristas de código por ahora: son catálogos, no dependencias — aparecen como hojas del grafo, no engordan los hubs. |
| 3 | Validación fail-fast al importar | 🟡 **Adoptar, pero opt-in** | `run_all.py` hoy corre los 4 pipelines y **acumula** los que fallan (`fallidos.append(...)`) en vez de abortar en el primero — es diseño intencional (permite que DANE cargue aunque Víctimas no tenga `VICTIMAS_URL` configurada, por ejemplo). Un `raise RuntimeError` al importar `config.py` rompería eso para toda la aplicación (API incluida). Ajuste: fail-fast vive en un comando separado (`python -m etl.common.config --check`), no en el import. | Un nodo CLI nuevo (`_check`) colgado de `config.py`; cero aristas hacia las 8 pipelines ni hacia la API. La versión rechazada (raise al importar) habría creado aristas de dependencia desde *todas* las pipelines y la API hacia el singleton — reforzando un hub artificial. |
| 4 | Multi-entorno / secrets manager | ⚪ **Anotar, sin acción ahora** | Ya conceptualmente cubierto en la sección 14 del plan general (RDS/Cloud SQL, staging/prod separados). Pydantic Settings ya prioriza variables de entorno reales sobre `.env` por defecto, así que no requiere trabajo extra para eso. | Sin impacto: no introduce código ni nodos (configuración de despliegue, fuera del grafo de código). |
| 5 | Decorador `@needs_env` para que Graphify vea variables de entorno en el grafo | ⚪ **Idea futura, baja prioridad** | No bloquea nada, no toca lógica existente. Se deja anotado, no forma parte de las Fases A/B/C. | Futurible: añadiría un decorador con aristas hacia las 8 pipelines (todas leen variables de entorno), convirtiéndolo en un mini-hub — por eso queda fuera mientras no haya necesidad real. |
| 6 | Pipelines con múltiples datasets (CNMH, Fiscalía) | 🟢 **Adoptar** | Ya estaba implícito en la Fase B ("requiere decidir con qué tipo de hecho empezar"); esto lo hace explícito con una variable por tipo de hecho (`CNMH_MINAS_URL`, `CNMH_ATENTADOS_URL`, etc.) en vez de una sola `CNMH_URL` genérica. | En el grafo regenerado, `Settings` ya muestra los 8 campos URL nuevos (6 CNMH + 2 Fiscalía); cuando se implemente la Fase B cada pipeline nuevo aparecerá como un nodo hoja colgando de `PipelineETL`, sin alterar la estructura de los hubs. |
| 7 | `config/investigacion_fuentes.yaml` (registro de la investigación de endpoints) | 🟢 **Adoptar y poblar ya** | Directamente aprovechable: ya existe la investigación en vivo de esta sesión (Policía, Fiscalía, CNMH, IDEAM, UCDP, ACLED, HDX, UNHCR, IOM DTM) — se transcribe tal cual a este archivo en la Fase A, no como ejemplo sino con los resource-ids y hallazgos reales ya verificados. | Nuevo nodo hoja de configuración; su valor real es evitar futuros "dataset fantasma" que llegarían al grafo con aristas de código falsas (como pasó antes con los resource-ids inventados). |
| 8 | Generar `docs/fuentes/*.md` desde el YAML | 🟡 **Adoptar solo para lo nuevo** | Las 4 fichas ya escritas (`dane.md`, `art.md`, `victimas.md`, `internacional.md`) tienen prosa curada a mano con hallazgos específicos de auditoría (limitaciones conocidas, notas de gobernanza) — un generador automático simple las empobrecería. Se genera automáticamente solo para las fichas nuevas de Fase B; las 4 existentes no se tocan. | Nodos `doc` nuevos (uno por ficha `docs/fuentes/<fuente>.md`) sin aristas de código; las 4 fichas existentes no cambian, así que no hay churn sobre el grafo ya estabilizado. |
| 9 | `tests/test_config.py` + endpoint `/health` en la API | 🟢 **Adoptar** | Aditivo, bajo riesgo, no toca pipelines existentes. El healthcheck lee de `curated.fuentes`/`data_quality_metrics` (tablas que ya existen) más el catálogo YAML — no requiere cambios de esquema. | +1 nodo de ruta (`/api/v1/health`) en el router v1, +1 nodo de servicio (`api/services/health.py`) con arista al router y a la capa de datos; los 3 endpoints existentes no se tocan — el subgrafo de la API crece lateralmente, no en profundidad. |
| 10 | Recarga de configuración en caliente | ⚪ **Anotar como futuro lejano** | Fuera de alcance; no hay caso de uso actual que lo requiera. | Sin impacto: sin código, sin nodos, sin aristas. |

**Nueva dependencia:** `pydantic-settings` no está en `requirements.txt` hoy
(solo `pydantic>=2.6`, que trae los modelos pero no `BaseSettings`/carga de
`.env`) — se agrega en la Fase A.

## `.env.example`: qué se agrega, sin inventar nada

Se conservan intactas todas las variables actuales (`DATABASE_URL`,
`POSTGRES_*`, `DANE_POBLACION_XLSX_URL`, `DANE_POBLACION_HOJA`, `VICTIMAS_URL`,
`PDET_URL`, `DIVIPOLA_DEPT_DATASET`, `DIVIPOLA_MUN_DATASET`). Se agrega:

1. **`WB_INDICADORES`** — hallazgo real: `etl/internacional/world_bank.py` ya lee
   esta variable (`os.getenv("WB_INDICADORES")`) y `run_all.py` ya ejecuta ese
   pipeline, pero **`.env.example` nunca la documentó**. Se agrega con el mismo
   valor de ejemplo que usan los tests: `NY.GDP.PCAP.PP.CD:PIB per cápita (PPA)`.
2. Variables nuevas **solo para las fuentes con endpoint real verificado** (Fase B
   abajo), con el nombre real encontrado.
3. Para las fuentes sin acceso público confirmado (Fase C), **la variable se
   documenta vacía con un comentario explicando el bloqueo real** — nunca un
   resource-id inventado. Mismo criterio que ya usa `docs/fuentes/art.md` con
   "Verificar en ficha antes de integración productiva".

## Hallazgos de la investigación en vivo (2026-08-02)

| Fuente | Estado real verificado | Detalle |
|---|---|---|
| **Policía Nacional** | 🟢 Datasets reales en Socrata, por tipo de delito | `fpe5-yrmw` (delitos sexuales), `ha6j-pa2r` (homicidios en accidente de tránsito — **no** el homicidio intencional que necesita `vw_homicidios_reconciliado`), `vuyt-mqpw` (violencia intrafamiliar), `d4fr-sbn2` (hurto). Columnas reales incluyen `CODIGO DANE`, `MUNICIPIO`, `FECHA HECHO`, `CANTIDAD`. **No apareció un dataset de "homicidios" general** en la búsqueda — falta una ronda de búsqueda más específica antes de poder alimentar la vista de reconciliación con Policía. |
| **Fiscalía** | 🟢 Datasets reales en Socrata | `dbdv-iihs` (Procesos Fiscalía V3), `hr73-zqjf` (Víctimas Fiscalía V3), `piva-db2c` (Procesados Fiscalía V3). Falta inspeccionar columnas reales (siguiente paso de implementación). |
| **CNMH / memoria histórica** | 🟢 Datasets reales y ricos en Socrata | Sistema SIEVCAC con datasets específicos por tipo de hecho: minas antipersonal (`52eu-ic7d`), atentados terroristas (`yfd7-8c9d`), desaparición forzada (`c59y-p4sz`), daño a bienes civiles (`a2ga-ur2i`), reclutamiento NNA (`hzd2-7ea7`), acciones bélicas (`chb6-bfmq`). Mejor acceso encontrado hasta ahora para ninguna fuente nueva. |
| **IDEAM (deforestación)** | 🟡 Dataset existe pero es archivo, no API JSON | `39dh-rc72` ("Cambio en la superficie cubierta por bosque natural — Nacional") es tipo `file`, no `dataset` Socrata estándar — mismo patrón que DANE (descarga directa, no `resource/<id>.json`). Requiere el mismo tipo de conector "lector de archivo" que ya se construyó para el Excel de DANE. |
| **Defensoría (alertas tempranas)** | 🔴 Sin dato abierto público | Cero resultados en el catálogo de Socrata. Confirma lo que ya se sospechaba: el SAT se publica como informes PDF, no como dataset. El esqueleto (`NotImplementedError`) se queda como está; no hay nada que configurar todavía. |
| **UNHCR / ACNUR** | 🟢 API pública, **sin autenticación**, probada en vivo | `https://api.unhcr.org/population/v1/population/?coo=COL` responde JSON real con series de refugiados/desplazados de Colombia por año. Es la fuente internacional más lista para implementar después de World Bank. |
| **HDX** | 🟢 API pública (CKAN + HAPI), probada en vivo | `data.humdata.org/api/3/action/package_search?fq=groups:col` devuelve 541 datasets de Colombia, incluyendo `hdx-hapi-col` (HAPI dedicado a Colombia). Sin autenticación para lectura básica. |
| **UCDP** | 🟡 API real pero requiere token | `https://ucdpapi.pcr.uu.se/api/gedevents/25.1` responde `401 API token required` (header `x-ucdp-access-token`). Hay que registrarse en UCDP para obtener el token antes de poder configurar `UCDP_API_TOKEN`. |
| **ACLED** | 🔴 Requiere registro (email + key) | No probado en vivo porque exige cuenta registrada por diseño; se documenta la variable vacía (`ACLED_EMAIL`, `ACLED_KEY`) con instrucción de registro, igual que UCDP. |
| **IOM DTM** | 🔴 Sin resolver | `dtm.iom.int/api` devuelve el HTML del sitio (protección anti-bot), no un endpoint de datos. Necesita una ronda de investigación específica (probablemente un portal de descarga por país, no una API REST simple) — no incluido en la Fase B. |

## Fase A — infraestructura de configuración (bajo riesgo, primero)

1. Agregar `pydantic-settings` a `requirements.txt`.
2. Crear `etl/common/config.py` con la clase `Settings` (arriba) — todos los
   campos de fuente opcionales, sin defaults que cambien comportamiento real.
3. Añadir la línea de import en `etl/common/pipeline.py` para que `.env` se
   cargue automáticamente en cualquier ejecución (`run_all.py`, tests, pipelines
   individuales).
4. Reescribir `.env.example` agrupado en `# ─── Nacionales ───` / `# ─── Internacionales ───`,
   conservando cada variable real existente, agregando `WB_INDICADORES` (hallazgo
   de documentación faltante) y los placeholders vacíos y honestamente comentados
   de la tabla de hallazgos.
5. Crear `.env` real (gitignorado, ya cubierto por `.gitignore` actual) copiando
   `.env.example` para desarrollo local.
6. Crear `config/investigacion_fuentes.yaml` con los hallazgos reales de esta
   sesión (resource-ids, columnas observadas, estado de bloqueo) para las 10
   fuentes investigadas — evita repetir el rastreo cuando se implemente Fase B/C.
7. Crear `config/fuentes.yaml` como catálogo estructurado **solo de las fuentes
   nuevas** (Fase B/C) — no reemplaza los kwargs ya escritos a mano en los 4
   pipelines reales.
8. `python -m etl.common.config --check`: script opt-in que reporta qué
   variables de fuentes activas faltan, sin abortar nada por sí solo.
9. `tests/test_config.py`: `Settings()` carga sin red ni `.env` presente (todos
   los campos de fuente son opcionales, así que no debe fallar); valida que
   `config/fuentes.yaml` (cuando exista) referencia campos reales de `Settings`.
10. Endpoint `GET /api/v1/health` (nuevo, no modifica los 3 existentes): reporta
    por fuente si su variable está configurada y la fecha del último
    `data_quality_metrics` exitoso — lectura de tablas que ya existen.
11. Actualizar el README (sección de arranque) con `.env.example` → `.env` y que
    la carga ahora es automática vía `config.py`.

**No se tocan** `etl/dane/`, `etl/pdet/`, `etl/victimas/`, `etl/internacional/world_bank.py`,
ni el esquema de base de datos. `api/main.py` gana un router nuevo (`/health`),
no se modifican los 3 endpoints existentes.

## Fase B — nuevos pipelines con acceso real confirmado (esto sí es lógica nueva, no modificación)

Como estas fuentes hoy son esqueletos (`raise NotImplementedError`), implementarlas
es agregar lógica donde no había ninguna — no viola "sin modificar lo existente".
Se sigue el patrón ya probado en `etl/victimas/pipeline.py` / `etl/pdet/pipeline.py`:
alias de columnas + `Pandera` (`EsquemaSerieNormalizada`) + `Lineage.ahora(...)` +
`upsert_fuente`/`upsert_indicador`/`insertar_serie` de `etl/common/cargar.py`.

Orden recomendado por qué tan lista está cada fuente:

1. **UNHCR/ACNUR** (`etl/internacional/unhcr.py`) — API sin auth, ya probada; es
   la extensión más barata siguiendo exactamente el patrón de `world_bank.py`
   (mismo tipo de carga a `curated.indicador_internacional`, sección 7.6).
2. **CNMH/memoria histórica** (`etl/memoria/pipeline.py`, hoy esqueleto) — datasets
   SIEVCAC reales, uno por tipo de hecho (`CNMH_MINAS_URL`, `CNMH_ATENTADOS_URL`,
   `CNMH_DESAPARICION_URL`, ...); requiere decidir con cuál empezar y cómo
   modelarlo contra `HechoVictimizante`/`AlertaTemprana` (sección 7 del plan) —
   dado que es memoria histórica sensible, revisar el checklist de privacidad
   (sección 3.1) antes de cargar a `curated`, igual que se hizo para víctimas.
3. **Fiscalía** (`etl/fiscalia/pipeline.py`, hoy esqueleto) — datasets V3 reales;
   falta inspeccionar columnas (paso de implementación, no de este plan).
4. **HDX** (`etl/internacional/hdx.py`) — API real; definir qué dataset de los
   541 de Colombia es prioritario (probablemente empezar por `hdx-hapi-col`).
5. **Policía** (`etl/policia/pipeline.py`, hoy esqueleto) — empezar por un delito
   con dataset limpio ya identificado (p. ej. hurto `d4fr-sbn2`), y dejar
   pendiente la búsqueda del dataset general de homicidios necesario para
   `vw_homicidios_reconciliado`.

Cada una suma: entrada en `config/fuentes.yaml` + variable real en `.env.example`,
`docs/fuentes/<fuente>.md` generado desde el YAML (plantilla ya usada por
`dane.md`/`art.md`/`victimas.md`/`internacional.md`), y tests en
`tests/test_pipelines.py` o `test_internacional.py` con un DataFrame que replique
el shape real encontrado (mismo patrón que
`test_pdet_transformar_con_shape_real_de_iniciativas`).

### Estado de implementación (verificado en vivo 2026-08-02)

0. **DANE** ✅ — `etl/dane/pipeline.py` con URL real verificada en vivo:
   `https://www.dane.gov.co/files/censo2018/proyecciones-de-poblacion/Municipal/DCD-area-proypoblacion-Mun-2020-2035-ActPostCOVID-19.xlsx`
   (200 OK, 1,8 MB). 17.952 filas municipio-año (1.122 municipios × 2020-2035);
   total nacional 2025 = 53.110.609, coincide con la proyección oficial del
   DANE. Indicador `poblacion` en `serie_historica` + KPI y capa municipal en
   el dashboard. Sirve de denominador para tasas por 100 mil habitantes.
1. **UNHCR** ✅ — `etl/internacional/unhcr.py`; probe real: 344 filas → 301
   (año-columna). Ficha `docs/fuentes/unhcr.md`.
2. **CNMH SIEVCAC** ✅ — `etl/memoria/pipeline.py` reemplaza el esqueleto:
   `CNMH_Memoria(hecho)` parametrizado con 6 resource-ids reales. Dos shapes:
   "casos" (atentados/reclutamiento) y "víctimas" (minas/desaparición/bienes/
   acciones, dedupe por `id_persona`). Solo agregados municipio-año a
   `serie_historica`; la fila individual con PII nunca sale de raw (3.1).
   Probe real: ≈26.796 municipio-año. Ficha `docs/fuentes/cnmh.md`.
3. **Fiscalía** ⚠️ **inviable por volumen** — `etl/fiscalia/pipeline.py` escrito
   y probado (agregación SoQL server-side), pero NO activo: 23,2M procesos /
   17,5M víctimas; cada consulta agregada reescanea y tarda ~10 min por página
   de 50k combinaciones (~200k grupos en todo el rango → horas). Sin dataset
   agregado publicado ni token que acelere. Ficha `docs/fuentes/fiscalia.md`;
   detalle en `config/investigacion_fuentes.yaml`. Requiere nueva ronda de
   búsqueda o corrida programada fuera de `run_all`.
4. **HDX** ✅ — `etl/internacional/hdx.py`; recurso Conflict Events
   (`hdx-conflicto` `bbdfa1bf-...`), CSV firmado vía `resource_show`, 346.698
   filas → 20.178 municipio-año (eventos + fatalidades). Ficha
   `docs/fuentes/hdx.md`.
5. **Policía** ✅ — `etl/policia/pipeline.py` reemplaza el esqueleto: hurto
   (`d4fr-sbn2`), violencia intrafamiliar (`vuyt-mqpw`), sexuales (`fpe5-yrmw`);
   `codigo_dane` DIVIPOLA+"000" → recorte, fechas `dd/mm/aaaa`. Probe real
   hurto: 44.169 → 11.016 municipio-año-tipo. Homicidios ✅ resuelto con el
   Excel oficial SIEDCO (2026-08-02): indicador `homicidios` bajo fuente
   `policia` → `vw_homicidios_reconciliado` (ver Fase C).
6. **ACLED** ✅ — `etl/internacional/acled.py`; sin API key: agregados oficiales
   país-año descargados a `data/external/` (3 series, Colombia 2018–2026 →
   27 indicador-año). Capa departamental ✅ (2026-08-02): el agregado semanal
   admin1 se mapea ADMIN1→DIVIPOLA (33/33 departamentos) y se carga
   departamento-año (acled_eventos_departamento: 38.747 eventos 2017–2026;
   acled_fatalidades_departamento: 16.529). Atribución obligatoria. Ficha
   `docs/fuentes/acled.md`.
7. **PDET (ART)** ✅ — dataset de iniciativas activado (`PDET_URL`):
   `gmvf-t63e.json`, 33.007 filas → **965 proyectos en 170 municipios PDET**
   en `curated.pdet_proyectos`. Sin inversión/año en la fuente (documentado).
   Nuevo endpoint `GET /api/v1/pdet/proyectos` + KPI del dashboard (2026-08-02).

`etl/run_all.py` ejecuta: DANE, Víctimas, PDET, WB, UNHCR, HDX, ACLED, 6 CNMH,
3 Policía + homicidios, IDEAM. Nota verificada en la corrida completa: la
siembra del catálogo DIVIPOLA (`python -m etl.common.divipola`, 1.123
municipios) es prerrequisito de los cargadores municipales; sin ella las filas
se descartan con aviso. La estadística zonal del raster IDEAM requiere además
la capa geo municipal (`python -m etl.common.capas_geo`).

## Fase C — implementada (IDEAM); resto documentado

- **IDEAM** ✅ implementado y verificado en vivo (2026-08-02): el dataset
  `39dh-rc72` resultó ser un ZIP con raster Erdas Imagine (`.img`,
  `cambio_2021_2022_v8_230705.img`, EPSG:3116, ~30 m/píxel) y su archivo
  `Contenido_Cambio.txt`; el conector `etl/ideam/pipeline.py` descarga el ZIP
  (URL configurable o redirección pública de `/download/39dh-rc72`), extrae el
  raster, y calcula estadística zonal por municipio (clases 1-4 en ha) contra la
  capa geo `capa_contexto_territorial` (sembrada desde COD-AB vía
  `python -m etl.common.capas_geo`). Resultado en `serie_historica`: 4
  indicadores (bosque estable 59,1M ha, deforestación 123.445 ha 2021-2022,
  regeneración, no bosque) con 2.036 filas municipales. Prerrequisito: capa geo
  sembrada (1.122 municipios; el 27493 NUEVO BELÉN DE BAJIRÁ no está en COD-AB).
- **UCDP**: variable `UCDP_API_TOKEN` documentada vacía; requiere que alguien del
  equipo se registre en ucdp.uu.se primero.
- **Fiscalía**: pipeline listo pero inactivo por volumen de agregación (ver
  Fase B, punto 3) — candidato a reintentar si la Fiscalía publica datos
  agregados o con una corrida programada de horas.
- **IOM DTM**: sin endpoint identificado todavía; queda fuera de este plan.
- **Defensoría**: sin dato abierto encontrado; el esqueleto se queda igual.
- **Policía homicidios** ✅ — resuelto (2026-08-02): no hay dataset Socrata,
  pero la Policía publica el Excel oficial SIEDCO por año en
  `policia.gov.co/estadistica-delictiva/homicidios` ("Homicidio Intencional2025.xlsx",
  13.727 filas; cabecera variable por año → detección automática). `Policia_Homicidios`
  lo descarga y carga el indicador `homicidios` bajo la fuente `policia`, que
  alimenta `vw_homicidios_reconciliado` (815 municipios, 13.722 homicidios 2025).
  Ojo: "Homicidio Intencional2024.xlsx" es parcial (2024-12 + ene-abr 2025),
  no usar como serie anual.
- **IOM DTM**: resuelto como reportes PDF por ronda (`dtm_download_track`,
  verificado 2026-08-02) — no hay series consolidadas ni API JSON; queda
  documentado sin pipeline (scraping frágil por reporte).

Todas quedan registradas en `config/investigacion_fuentes.yaml` (Fase A, punto 6)
para no repetir el rastreo cuando alguien retome cada una.

## Verificación

- `pytest` debe seguir en verde (31 tests hoy) sin tocar los existentes; los
  nuevos tests de Fase B no dependen de red (mismo patrón `monkeypatch` ya usado).
  `tests/test_config.py` es nuevo y aditivo.
- Confirmar que `Settings()` no rompe nada: importar `etl.common.config` sin
  ningún `.env` presente y sin variables exportadas no debe lanzar ninguna
  excepción (todos los campos de fuente son opcionales) — a diferencia del
  diseño original de la propuesta (campos `Field(...)` obligatorios), que sí
  habría roto el arranque de la API.
- Levantar Postgres nativo (mismo procedimiento ya usado en la auditoría —
  `schema.sql` + migraciones) y correr `python -m etl.run_all` sin exportar
  variables manualmente en el shell, solo con `.env` — debe comportarse igual
  que hoy (dane/pdet/victimas/world_bank fallan igual de limpio si falta su
  variable, porque su código no cambió). Repetir además la corrida completa de
  DANE contra el Excel real (ya verificada: 17.952 filas a `curated`) para
  confirmar que `config.py` no interfiere con un pipeline que sí funciona.
- Para cada pipeline nuevo de Fase B: probar `extraer()` contra el endpoint real
  (como se hizo con el Excel de DANE) antes de darlo por terminado, no solo con
  datos sintéticos.
- Probar `GET /api/v1/health` contra la BD real sembrada y confirmar que refleja
  correctamente qué fuentes tienen variable configurada.
