# Observatorio para la Paz en Colombia
## Plan de Desarrollo

---

## Tabla de contenidos

1. [Resumen ejecutivo](#1-resumen-ejecutivo)
2. [Objetivo y alcance](#2-objetivo-y-alcance)
3. [Principios de gobernanza y ética de datos](#3-principios-de-gobernanza-y-ética-de-datos)
4. [Arquitectura de la plataforma](#4-arquitectura-de-la-plataforma)
5. [Fuentes de datos oficiales](#5-fuentes-de-datos-oficiales)
6. [Estructura del proyecto](#6-estructura-del-proyecto)
7. [Modelo de datos y almacenamiento](#7-modelo-de-datos-y-almacenamiento)
8. [API](#8-api)
9. [Dashboard / Frontend](#9-dashboard--frontend)
10. [Sistema de diseño](#10-sistema-de-diseño)
11. [Módulos funcionales](#11-módulos-funcionales)
12. [Calidad de datos y trazabilidad](#12-calidad-de-datos-y-trazabilidad)
13. [Seguridad y privacidad](#13-seguridad-y-privacidad)
14. [Infraestructura y DevOps](#14-infraestructura-y-devops)
15. [Equipo y roles](#15-equipo-y-roles)
16. [Fases de desarrollo](#16-fases-de-desarrollo)
17. [Riesgos y mitigación](#17-riesgos-y-mitigación)
18. [Métricas de éxito](#18-métricas-de-éxito)
19. [Sostenibilidad](#19-sostenibilidad)
20. [Retroalimentación, co-creación y extensiones futuras](#20-retroalimentación-co-creación-y-extensiones-futuras)
21. [Próximos pasos inmediatos](#21-próximos-pasos-inmediatos)

---

## 1. Resumen ejecutivo

El **Observatorio para la Paz en Colombia** es una plataforma de datos (Data Platform), no un dashboard estático. Integra, valida y publica de forma trazable información oficial sobre conflicto armado, violencia, derechos humanos, implementación del Acuerdo de Paz, desarrollo territorial, población, economía, justicia y medio ambiente, georreferenciada a nivel de departamento, municipio y — cuando exista— vereda.

El diseño como plataforma (en lugar de un tablero fijo) permite:

- Incorporar nuevas fuentes sin rediseñar el sistema.
- Automatizar actualizaciones periódicas mediante pipelines ETL.
- Mantener linaje y trazabilidad de cada dato (de dónde viene, cuándo se actualizó, qué transformación sufrió).
- Servir los mismos datos a múltiples consumidores: dashboard web, API pública, reportes, modelos de IA.

Dado que la plataforma trabaja con datos sensibles (víctimas del conflicto, alertas tempranas, homicidios, desplazamiento forzado), la gobernanza ética y la protección de datos personales son un **requisito de diseño**, no un añadido posterior (ver sección 3 y 13).

La diferencia entre un MVP técnico y una plataforma con impacto real a largo plazo no está solo en el código: está en la robustez metodológica, la sostenibilidad institucional y la adopción real por parte de periodistas, organizaciones sociales y entidades públicas. Este plan incorpora esas tres capas desde el diseño inicial.

---

## 2. Objetivo y alcance

### 2.1 Objetivo general

Construir una plataforma pública, confiable y actualizable que centralice datos oficiales sobre paz, conflicto y desarrollo territorial en Colombia, para apoyar la toma de decisiones de entidades públicas, organizaciones sociales, academia, periodistas y ciudadanía.

### 2.2 Objetivos específicos

- Integrar de forma automatizada fuentes oficiales dispersas en un modelo de datos unificado y georreferenciado.
- Garantizar trazabilidad: cada cifra debe poder rastrearse hasta su fuente original y fecha de extracción.
- Exponer los datos vía API pública documentada, además del dashboard.
- Ofrecer visualizaciones claras (mapas, series temporales, rankings) con filtros territoriales y temporales.
- Incorporar análisis complementarios (resúmenes, detección de tendencias) de forma responsable, siempre distinguibles del dato oficial crudo.
- Complementar los datos oficiales colombianos con fuentes internacionales de datos abiertos (Banco Mundial, UN Data, HDX, UCDP, UNHCR), para dar contexto de comparabilidad global sin sustituir la granularidad municipal/veredal que solo las fuentes nacionales ofrecen (ver sección 5.2).
- Generar adopción real: que periodistas, organizaciones sociales y entidades locales usen la plataforma y el API, no solo que existan.

### 2.3 Fuera de alcance (fase inicial)

- Recolección de datos primarios (encuestas propias, verificación de campo).
- Predicciones judicializables o con valor probatorio.
- Publicación de datos con nivel de detalle que permita identificar víctimas individuales (ver sección 3).

---

## 3. Principios de gobernanza y ética de datos

Este es el punto más crítico del proyecto y debe definirse **antes** de escribir código.

1. **Solo fuentes oficiales y públicas.** No se scrapean redes sociales ni se infieren datos de terceros no verificados.
2. **Nivel mínimo de agregación.** Los datos de víctimas, alertas tempranas y hechos victimizantes se publican agregados (municipio/año como mínimo), nunca a nivel individual, siguiendo el principio de "no daño" (*do no harm*) usado por la Unidad de Víctimas y el CICR.
3. **Neutralidad y verificabilidad.** El observatorio no atribuye responsabilidad penal ni política a actores armados; reporta cifras oficiales con su fuente. Cualquier análisis interpretativo se etiqueta claramente como tal.
4. **Trazabilidad obligatoria.** Todo registro almacenado debe conservar: `fuente`, `url_origen`, `fecha_extraccion`, `fecha_corte_dato`, `licencia`.
5. **Revisión de licencias.** Antes de integrar cada fuente, se documenta su licencia de uso (Datos Abiertos Colombia usa licencia CC BY 4.0 por defecto, pero debe verificarse fuente por fuente). Esto aplica también a las fuentes internacionales de la sección 5.2: algunas (Banco Mundial, UN Data, HDX, UNHCR) son abiertas sin restricción; otras (p. ej. ACLED) exigen atribución y tienen condiciones de uso distintas para fines comerciales — se verifica y documenta caso por caso antes de integrarlas.
6. **Comité asesor con representación plural.** No es un acompañamiento genérico: se define una composición mínima de cuatro tipos de actor para fortalecer la neutralidad percibida y la legitimidad pública:
   - Una organización de víctimas.
   - Un centro académico o de investigación (p. ej. universidad con línea de estudios sobre conflicto).
   - Una entidad del Estado (p. ej. DNP o CNMH).
   - Una ONG de derechos humanos.

   El comité valida metodología de indicadores, revisa criterios de agregación y debe aprobar explícitamente cualquier módulo de análisis automatizado antes de su publicación.
7. **Corrección y actualización.** Mecanismo público para reportar errores o solicitar corrección/retiro de un dato (ver también sección 20).

### 3.1 Checklist de privacidad previo a publicación

Antes de publicar cualquier dataset o vista nuevos, se ejecuta una lista de comprobación formal (adaptada de guías públicas del CICR/ICRC y HRDAG sobre protección de datos en contextos de conflicto):

- [ ] ¿El registro más pequeño (municipio/vereda + año + tipo de hecho) tiene un número de casos suficiente para no ser reidentificable? (umbral mínimo de casos a definir con el comité asesor, p. ej. *k*-anonimato ≥ 5).
- [ ] ¿La combinación de esta vista con otra tabla pública del observatorio permite acotar un hecho a un grupo de personas muy pequeño (ataque de correlación)?
- [ ] ¿La granularidad temporal (día/mes) combinada con la geográfica (vereda) reduce demasiado el universo de personas posibles?
- [ ] ¿Existen zonas con población total muy baja (municipios/veredas pequeñas) donde cualquier cifra distinta de cero ya es identificable?
- [ ] ¿La fuente original ya publica el dato a este nivel de detalle, o el observatorio estaría añadiendo granularidad que la fuente no expone?

Esta checklist se documenta como plantilla en `docs/metodologia/checklist_privacidad.md` y su resultado se anexa como evidencia antes de habilitar un nuevo dataset en `curated/`.

---

## 4. Arquitectura de la plataforma

```
                         Fuentes de Datos Abiertos
                                    │
        ┌──────────────┬───────────┼───────────┬──────────────┐
        │              │           │            │              │
      DANE       Datos.gov.co  Unidad        ARN/ART      Fiscalía/
                  (Socrata)    Víctimas                   Policía/
        │              │           │            │         Med. Legal
        └──────────────┴───────────┼────────────┴──────────────┘
                                    │
                          ┌─────────▼─────────┐
                          │   ETL (Python)     │
                          │  Extract-Validate  │
                          │  -Transform-Load   │
                          │  (Airflow/Dagster) │
                          └─────────┬─────────┘
                                    │
                          ┌─────────▼─────────┐
                          │  PostgreSQL +      │
                          │  PostGIS           │
                          │  esquemas: raw →   │
                          │  staging → curated │
                          └─────────┬─────────┘
                                    │
                    ┌───────────────┼────────────────┐
                    │                                │
          ┌─────────▼─────────┐          ┌───────────▼──────────┐
          │   API (FastAPI)   │          │  Tile server          │
          │  REST + OpenAPI   │          │  (pg_tileserv /       │
          │                   │          │  tippecanoe)          │
          └─────────┬─────────┘          └───────────┬──────────┘
                    │                                │
                    └───────────────┬────────────────┘
                                    │
                    ┌───────────────┼────────────────┐
                    │               │                │
             Dashboard (React)   Reportes PDF    Consumo por
             + Mapas (MapLibre)  automatizados   terceros (API)
                    │
              Usuarios finales
```

### 4.1 Stack tecnológico propuesto

| Capa | Tecnología | Justificación |
|---|---|---|
| Orquestación ETL | Python + Dagster (o Airflow) | Manejo de dependencias, reintentos, versionado de pipelines |
| Validación de datos | Great Expectations / Pandera | Contratos de calidad de datos automatizados |
| Base de datos | PostgreSQL + PostGIS | Estándar para datos geoespaciales, robusto y open source |
| Teselas vectoriales para mapas | pg_tileserv (MVP) / tippecanoe (pre-generación) | Sirve tiles directamente desde PostGIS sin infraestructura adicional pesada |
| API | FastAPI + Pydantic | Tipado, documentación automática (OpenAPI/Swagger) |
| Cacheo/consultas agregadas | Redis (opcional, fase 2) | Acelerar consultas frecuentes del dashboard |
| Frontend | React + TypeScript | Ecosistema maduro, componentes reutilizables |
| Mapas | MapLibre GL JS + tiles vectoriales | Evita dependencia de licencias privativas (vs. Google Maps) |
| Gráficas | Recharts / Observable Plot | Consistencia visual, accesibilidad |
| Contenedores | Docker + docker-compose (dev) | Reproducibilidad en desarrollo |
| Cómputo en la nube (staging/prod) | Cloud Run / ECS (contenedores gestionados) | Evita administrar servidores; escala con demanda |
| Base de datos gestionada | RDS / Cloud SQL (PostgreSQL + PostGIS) | Backups automatizados, alta disponibilidad, menor carga operativa |
| CI/CD | GitHub Actions | Pruebas automáticas de ETL y despliegue |
| Monitoreo | Prometheus + Grafana (opcional) | Salud de pipelines y API |

El servicio de teselas se incorpora explícitamente al diagrama de arquitectura y a la estimación de costos (sección 14), ya que el frontend depende de él para renderizar mapas y suele omitirse en la planeación inicial.

---

## 5. Fuentes de datos oficiales

| Fuente | Entidad | Datos principales | URL |
|---|---|---|---|
| Portal Nacional de Datos Abiertos | Gobierno de Colombia | Miles de datasets vía API Socrata | https://www.datos.gov.co/ |
| DANE | DANE | Población, pobreza, empleo, educación | https://www.dane.gov.co/ |
| Datos Paz | Unidad para las Víctimas | Víctimas, desplazamiento, retornos, reparación | https://datospaz.unidadvictimas.gov.co/ |
| ARN | Agencia para la Reincorporación | Excombatientes, reincorporación | https://www.reincorporacion.gov.co/ |
| ART | Agencia de Renovación del Territorio | PDET, obras, proyectos | https://www.renovacionterritorio.gov.co/ |
| Fondo Colombia en Paz | FCP | Financiación de la paz | https://fcp.gov.co/ |
| DNP | Departamento Nacional de Planeación | Indicadores territoriales | https://www.dnp.gov.co/ |
| IDEAM | IDEAM | Variables ambientales | https://www.ideam.gov.co/ |
| Fiscalía General | Fiscalía | Estadísticas judiciales | https://www.fiscalia.gov.co/ |
| Policía Nacional | Policía Nacional | Delitos | https://www.policia.gov.co/ |
| Medicina Legal | INMLCF | Muertes violentas | https://www.medicinalegal.gov.co/ |
| Defensoría del Pueblo | Defensoría | Alertas tempranas | https://www.defensoria.gov.co/ |
| JEP | Jurisdicción Especial para la Paz | Información judicial del conflicto | https://www.jep.gov.co/ |
| Comisión de la Verdad | CEV (repositorio histórico) | Informe final, archivos | https://www.comisiondelaverdad.co/ |
| CNMH | Centro Nacional de Memoria Histórica | Memoria histórica, bases documentales | https://centrodememoriahistorica.gov.co/ |

**Nota metodológica:** cada fuente debe documentarse en `docs/fuentes/<fuente>.md` con: método de acceso (API/descarga manual/scraping autorizado), periodicidad de actualización, formato, licencia y responsable de mantenimiento del conector.

### 5.1 Capas de contexto territorial (no son indicadores de conflicto)

Para que los análisis territoriales tengan marco de interpretación, se incorporan capas geoespaciales estáticas que no miden conflicto pero son indispensables para leerlo correctamente:

| Capa | Fuente | Uso |
|---|---|---|
| Resguardos indígenas | ANT / IGAC | Contexto étnico-territorial |
| Territorios colectivos de comunidades negras | ANT | Contexto étnico-territorial |
| Zonas de reserva campesina (ZRC) | ANT | Contexto de tenencia de la tierra |
| División político-administrativa (DIVIPOLA) | DANE / IGAC | Base geográfica de todo el sistema |

Estas capas se actualizan con mucha menor frecuencia que los indicadores dinámicos y se versionan igual que las dimensiones lentas descritas en la sección 7.2.

### 5.2 Fuentes de datos abiertos internacionales (capa de comparabilidad global)

Las fuentes colombianas (sección 5) siguen siendo la base del observatorio porque son las únicas con desagregación por municipio y vereda. Se añade una capa complementaria de repositorios internacionales de datos abiertos, útil para comparar a Colombia con estándares y promedios globales/regionales, y para cruzar series de conflicto armado con metodologías internacionales reconocidas:

| Fuente | Alcance | Datos principales | URL |
|---|---|---|---|
| World Bank Open Data | Nacional (Colombia dentro de series globales) | PIB, pobreza, indicadores sociales y de desarrollo | https://data.worldbank.org/ |
| UN Data | Nacional | Estadísticas oficiales de agencias de Naciones Unidas | https://data.un.org/ |
| Humanitarian Data Exchange (HDX) | Nacional/subnacional según dataset | Datasets humanitarios, muchos específicos de Colombia (desplazamiento, respuesta humanitaria) | https://data.humdata.org/ |
| UCDP (Uppsala Conflict Data Program) | Eventos georreferenciados | Conflicto armado, eventos de violencia organizada con coordenadas | https://ucdp.uu.se/ |
| ACLED (Armed Conflict Location & Event Data) | Eventos georreferenciados | Eventos de conflicto y protesta; licencia con condiciones de atribución, revisar antes de integrar | https://acleddata.com/ |
| UNHCR / ACNUR | Nacional | Desplazamiento forzado, refugio, población de interés | https://www.unhcr.org/refugee-statistics/ |
| IOM DTM (Displacement Tracking Matrix) | Nacional/subnacional | Movilidad y desplazamiento | https://dtm.iom.int/ |

**Nota metodológica clave:** la mayoría de estas fuentes reportan a nivel **nacional**, no municipal. No se combinan directamente con las tablas de hechos por municipio (sección 7): se modelan como una entidad separada (`IndicadorInternacional`, sección 7.6) y se presentan en el dashboard como panel de contexto/comparabilidad, nunca mezcladas visualmente con cifras municipales de forma que sugieran una granularidad que no tienen.

---

## 6. Estructura del proyecto

```
observatorio-paz/
│
├── data/
│   ├── raw/              # Datos crudos, inmutables, tal como se descargan
│   ├── processed/        # Datos limpios/normalizados
│   ├── curated/          # Datos listos para consumo (API/dashboard)
│   └── external/         # Referencias externas (shapefiles DIVIPOLA, ANT, IGAC)
│
├── etl/
│   ├── dane/
│   ├── victimas/
│   ├── pdet/
│   ├── fiscalia/
│   ├── policia/
│   ├── ideam/
│   ├── memoria/
│   ├── internacional/     # World Bank, UN Data, HDX, UCDP, ACLED, UNHCR, IOM DTM
│   └── common/           # Utilidades compartidas: geocodificación, validación
│
├── database/
│   ├── schema.sql         # Define esquemas raw / staging / curated (ver sección 7.2)
│   ├── migrations/
│   ├── views/
│   └── functions/
│
├── api/
│   ├── routes/
│   ├── models/
│   └── services/
│
├── dashboard/
│   ├── pages/
│   ├── components/
│   ├── charts/
│   ├── maps/
│   └── filters/
│
├── notebooks/             # Exploración y validación de datos
├── docs/
│   ├── fuentes/           # Ficha metodológica por fuente
│   └── metodologia/       # Definiciones de indicadores, checklist de privacidad
├── reports/                # Reportes generados automáticamente
├── tests/                  # Pruebas unitarias, integración y carga (ETL + API)
└── docker/
```

---

## 7. Modelo de datos y almacenamiento

Entidades principales (esquema conceptual):

- **Territorio**: `Departamento`, `Municipio`, `Vereda` (jerarquía DIVIPOLA), con vigencia versionada (ver 7.2).
- **Indicador**: catálogo de métricas con metadatos (unidad, fuente, periodicidad).
- **HechoVictimizante**: víctimas, agregado por municipio/periodo/tipo de hecho.
- **Violencia**: homicidios, masacres, desplazamiento (Medicina Legal, Policía, Unidad Víctimas).
- **PDET**: proyectos, avance, inversión.
- **Reincorporación**: datos ARN agregados.
- **DesarrolloTerritorial**: educación, salud, economía, infraestructura.
- **MedioAmbiente**: deforestación, cultivos ilícitos (IDEAM/UNODC).
- **AlertaTemprana**: alertas de la Defensoría, agregadas y anonimizadas.
- **CapaContextoTerritorial**: resguardos, territorios colectivos, ZRC (sección 5.1).
- **SerieHistorica**: tabla de hechos genérica (indicador, territorio, periodo, valor, fuente_id).
- **IndicadorInternacional**: indicadores de fuentes globales (Banco Mundial, UN Data, HDX, UCDP, ACLED, UNHCR, IOM DTM), a nivel país/región — sección 5.2 y 7.6.
- **Fuente**: catálogo de fuentes con licencia, URL, última actualización (incluye fuentes nacionales e internacionales).

Todas las tablas de hechos incluyen columnas de linaje: `fuente_id`, `fecha_extraccion`, `fecha_corte`, `hash_registro` (para detectar cambios/duplicados).

### 7.1 Granularidad temporal flexible

En lugar de fijar la granularidad a municipio/año, cada tabla de hechos usa un campo `periodo` con `periodo_inicio` y `periodo_fin` (tipo `DATE`), o una columna `fecha` truncable según el indicador. Esto permite que indicadores que sí se reportan a nivel mensual (homicidios, alertas tempranas) conserven esa resolución, mientras que otros con reporte anual (pobreza, PDET) simplemente usan un periodo de un año. La decisión de a qué nivel *exponer* el dato en el dashboard (mes vs. año) queda separada de a qué nivel se *almacena*, y siempre se resuelve primero contra el checklist de privacidad (sección 3.1) antes de habilitar una granularidad más fina.

### 7.2 Versionado de dimensiones que cambian lentamente

Los códigos DIVIPOLA de municipios se actualizan periódicamente (creación de municipios, cambios de código). Las tablas de `Territorio` y `CapaContextoTerritorial` implementan un patrón de dimensión de cambio lento (SCD tipo 2) con columnas `valido_desde` y `valido_hasta`, de forma que:

- Se conserva el histórico completo aunque un municipio cambie de código o se cree uno nuevo.
- Las series históricas pueden reconciliarse contra el código vigente en cada punto del tiempo sin perder trazabilidad.

### 7.3 Esquemas de base de datos alineados con las capas de archivos

La separación `raw/ → processed/ → curated/` en el sistema de archivos se replica como esquemas separados dentro de PostgreSQL: `raw`, `staging`, `curated`. Esto permite:

- Aplicar permisos distintos por esquema (p. ej. solo el proceso ETL escribe en `raw`; la API solo lee de `curated`).
- Limpiar o reprocesar `staging` sin afectar lo ya publicado en `curated`.
- Mantener la misma separación lógica end-to-end, de archivo a tabla.

### 7.4 Tabla de métricas de calidad de datos

Además del registro de auditoría de ejecuciones ETL, se define una tabla `data_quality_metrics` donde cada corrida de pipeline inserta: `pipeline_id`, `timestamp_ejecucion`, `registros_leidos`, `registros_validos`, `registros_rechazados`, `nulos_por_columna_critica` (JSON), `duracion_segundos`. Esto convierte la calidad de datos en una métrica graficable en el tiempo (panel interno) y alertable (p. ej. si `registros_rechazados` supera un umbral, se dispara una alerta antes de promover a `curated`).

### 7.5 Reconciliación de fuentes divergentes

Cuando dos fuentes oficiales reportan cifras distintas para el mismo hecho (ejemplo típico: homicidios según Policía Nacional vs. Medicina Legal), no basta con documentar la diferencia. Se construye una **vista unificada** (`vw_homicidios_reconciliado`, por ejemplo) que:

1. Selecciona un valor de referencia según un criterio metodológico público y documentado (p. ej. "se usa Medicina Legal como fuente primaria de homicidios por ser la entidad forense oficial"), definido junto con el comité asesor.
2. Muestra igualmente ambas cifras originales, con una nota aclaratoria visible en el dashboard.

Así el usuario final no tiene que navegar entre fuentes para entender la discrepancia, pero tampoco se oculta la existencia de datos divergentes.

### 7.6 Modelado de indicadores internacionales

La tabla `IndicadorInternacional` se mantiene deliberadamente separada de `SerieHistorica` (que es por territorio colombiano): sus claves son `fuente_id`, `pais` (siempre Colombia en el MVP, pero extensible), `indicador`, `periodo`, `valor`, sin columna de municipio/vereda. Las vistas del dashboard que combinan ambas capas (p. ej. "homicidios en Colombia vs. promedio regional") lo hacen mediante un `JOIN` explícito a nivel de país/año, nunca infiriendo un valor municipal a partir de un promedio nacional o global.

---

## 8. API

- **Framework:** FastAPI, documentación automática vía OpenAPI/Swagger en `/docs`.
- **Versionado:** `/api/v1/...` desde el inicio, para no romper consumidores externos al evolucionar.
- **Endpoints núcleo:**
  - `GET /territorios/{codigo_divipola}`
  - `GET /indicadores/{indicador}?territorio=&desde=&hasta=`
  - `GET /series/{territorio}`
  - `GET /fuentes` (catálogo con metadatos de linaje)
- **Paginación obligatoria desde el día uno.** Endpoints como `/series/{territorio}` pueden devolver millones de filas; se implementa paginación basada en cursores (o al menos `offset`/`limit`) con un tamaño máximo de página documentado en `/docs`. Sin esto, cualquier consumidor externo — o el propio dashboard — se enfrenta a timeouts.
- **CORS.** Configurado explícitamente desde el inicio para permitir consumo desde dashboards de terceros (medios, universidades), con la política documentada en `/docs`.
- **Cacheo HTTP.** Además de Redis en el backend, se agregan cabeceras `Cache-Control` y `ETag` en respuestas de solo lectura, para que los clientes puedan hacer *caching* condicional y reducir carga sobre la API.
- **Autenticación:** lectura pública sin autenticación; endpoints de escritura/administración protegidos con API key/OAuth.
- **Límites:** rate limiting para uso justo (evitar abuso de scraping masivo del propio API).
- **Formatos:** JSON por defecto; GeoJSON para endpoints con geometría.

---

## 9. Dashboard / Frontend

### 9.1 Página principal (wireframe conceptual)

```
──────────────────────────────────────────────────
 Observatorio para la Paz en Colombia
──────────────────────────────────────────────────
 KPIs:  Municipios monitoreados · Víctimas ·
        Homicidios · Desplazados · Proyectos PDET ·
        Alertas tempranas
──────────────────────────────────────────────────
 Mapa interactivo (coroplético, filtrable)
──────────────────────────────────────────────────
 Gráfico de series temporales
──────────────────────────────────────────────────
 Ranking de municipios (indicador seleccionable)
──────────────────────────────────────────────────
 Noticias / actualizaciones del observatorio
──────────────────────────────────────────────────
```

### 9.2 Menú de navegación

Inicio · Mapa Nacional · Violencia · Víctimas · Desplazamiento · PDET · Economía · Educación · Salud · ODS · Alertas · Análisis · Reportes · Datos (descarga masiva) · Metodología

> Se agrega explícitamente una sección **"Metodología"**, visible desde el menú principal, con la ficha técnica de cada indicador y su fuente — estándar de transparencia usado por Our World in Data y HDX.

### 9.3 Transparencia metodológica al alcance de un clic

Cada KPI o gráfico del dashboard incluye un enlace directo ("¿Cómo se calcula?") que despliega, sin salir de la vista: definición del indicador, fuente, periodicidad de actualización y limitaciones conocidas. Esto evita que la ficha metodológica quede aislada en una sección separada que nadie visita.

### 9.4 Descarga masiva de datos

Página dedicada de **"Datos"** (o botón en cada visualización) que permite descargar el dataset subyacente en CSV/GeoJSON, con la misma información de linaje que se almacena internamente. Esto convierte el dashboard en una herramienta real de trabajo para investigadores y periodistas, no solo en una vitrina visual.

### 9.5 Optimización para dispositivos móviles

Organizaciones de base y periodistas en terreno acceden frecuentemente desde celular con conectividad limitada. Mapas, gráficos y navegación deben ser responsivos desde el primer sprint de frontend, no como ajuste posterior — el sistema de diseño (sección 10) define los breakpoints desde el inicio.

---

## 10. Sistema de diseño

Inspirado en plataformas de referencia (Banco Mundial, Our World in Data, UN Data), priorizando claridad y neutralidad visual dado lo sensible de los datos.

| Uso | Color | Hex |
|---|---|---|
| Fondo | Blanco | `#FFFFFF` |
| Institucional / primario | Azul | `#0B5394` |
| Indicadores positivos | Verde | `#2E7D32` |
| Alertas / precaución | Naranja | `#FB8C00` |
| Eventos críticos | Rojo | `#D32F2F` |
| Fondo secundario | Gris claro | `#F4F6F8` |

- **Tipografía:** Inter o Source Sans Pro.
- **Accesibilidad:** contraste AA mínimo (WCAG 2.1), paletas de mapas verificadas para daltonismo.
- **Responsive / breakpoints:** definidos desde el inicio (móvil, tablet, escritorio); mapas y series temporales deben degradar a interacciones táctiles sin perder legibilidad (ver 9.5).
- **Componentes:** mapas coropléticos, series temporales, barras comparativas, todos con filtros por año, departamento y municipio, y **exportación de datos** (CSV/GeoJSON) desde cada visualización.

---

## 11. Módulos funcionales

1. **Mapa de Paz** — visión territorial general, capas superpuestas (incluye capas de contexto de la sección 5.1).
2. **Víctimas** — hechos victimizantes agregados, series históricas.
3. **Violencia** — homicidios, masacres, acciones armadas.
4. **Desarrollo Territorial** — educación, salud, economía, infraestructura, PDET.
5. **Acuerdo de Paz** — seguimiento a puntos del acuerdo, reincorporación.
6. **Análisis complementario** (antes "Análisis con IA") — estrategia en dos fases:

   **Fase A — resúmenes basados en plantillas (sin LLM).** Texto generado con reglas deterministas que rellenan valores directamente desde la base de datos ("El municipio X registró Y hechos victimizantes en el periodo Z, una variación de W% respecto al periodo anterior"). Cero riesgo de alucinación porque no hay generación libre de texto.

   **Fase B — asistencia de LLM, con humano en el ciclo.** Si en una fase posterior se incorpora un modelo de lenguaje para redactar resúmenes más naturales o detectar patrones, el texto generado **nunca se publica automáticamente**: un analista revisa y aprueba cada resumen antes de publicarlo, y el contenido se etiqueta siempre como *"análisis automatizado en revisión"* hasta su aprobación, y como *"análisis automatizado, no dato oficial"* una vez publicado, con enlace a la metodología usada.

   **Transparencia del modelo.** Si en el futuro se usan modelos de machine learning para detección de tendencias (no solo LLM de redacción), se publica en una página específica: arquitectura del modelo, datos de entrenamiento usados y métricas de rendimiento/error. El objetivo es que ninguna cifra "salga de una caja negra" sin poder auditarse.

7. **Comparabilidad internacional** — panel con indicadores nacionales de Colombia frente a promedios regionales/globales (Banco Mundial, UN Data, UCDP, UNHCR), construido sobre `IndicadorInternacional` (sección 7.6). Se presenta visualmente separado de los mapas y series por municipio, para no sugerir una granularidad territorial que estas fuentes no tienen.

---

## 12. Calidad de datos y trazabilidad

- Cada pipeline ETL corre validaciones automáticas (rangos esperados, tipos, duplicados, completitud) antes de promover datos de `staging` a `curated` (sección 7.3), registrando resultados en `data_quality_metrics` (sección 7.4).
- Registro de auditoría: qué pipeline corrió, cuándo, cuántos registros insertó/actualizó/rechazó.
- Página pública `/fuentes` en el dashboard que muestra fecha de última actualización por fuente — transparencia sobre qué tan "fresco" está cada dato.
- Discrepancias entre fuentes oficiales (p. ej. homicidios de Policía vs. Medicina Legal) se resuelven mediante una vista de reconciliación pública, no eligiendo arbitrariamente una fuente ni ocultando la diferencia (ver sección 7.5).

---

## 13. Seguridad y privacidad

- **Sin PII (información personal identificable).** Ningún pipeline debe ingerir ni almacenar datos a nivel de individuo identificable.
- Revisión previa a publicar cualquier dataset nueva mediante el checklist de privacidad (sección 3.1), con especial atención a combinaciones vereda + hecho + fecha muy específicas en municipios pequeños.
- Gestión de secretos (API keys, credenciales de BD) vía variables de entorno / vault, nunca en el repositorio.
- HTTPS obligatorio en todos los entornos expuestos.
- Backups periódicos de la base de datos con retención definida (procedimiento de restauración documentado en sección 14).
- Plan de respuesta ante reporte de error/dato sensible mal publicado (canal de contacto visible en el sitio, ver sección 20).

---

## 14. Infraestructura y DevOps

- **Entornos:** desarrollo, staging, producción — separados.
- **Desarrollo local:** Docker Compose.
- **Staging/producción:** contenedores gestionados (Cloud Run o ECS) + base de datos PostgreSQL/PostGIS administrada (RDS o Cloud SQL), para reducir carga operativa y obtener backups automatizados y alta disponibilidad sin gestionar servidores propios.
- **Servicio de teselas (tiles):** desplegado junto a la API; para el MVP, pg_tileserv sobre la misma instancia de PostGIS es suficiente; a mayor escala, migrar a teselas pre-generadas con tippecanoe servidas desde almacenamiento estático/CDN.
- **CI/CD:** pruebas automáticas de ETL y API en cada PR (incluye pruebas de carga, ver sección 20.3); despliegue automático a staging al hacer merge a `main`.
- **Infraestructura como código** (Terraform u otro) para reproducibilidad del entorno cloud.
- **Backup y recuperación probados.** Un backup sin restauración verificada no es una copia de seguridad real: se documenta un procedimiento de restauración paso a paso y se ejecuta una prueba de recuperación completa **trimestral**, registrando tiempo de restauración (RTO) y punto de recuperación (RPO) obtenidos.
- **Costos:** estimación mensual explícita de cómputo (API + tile server), base de datos gestionada, frontend (hosting estático/CDN) y almacenamiento de datos crudos, con el proveedor de nube preferido documentado — esta decisión afecta directamente la sostenibilidad del proyecto (sección 19).

---

## 15. Equipo y roles

| Rol | Responsabilidad |
|---|---|
| Líder de proyecto / Product Owner | Prioriza indicadores, valida con stakeholders |
| Ingeniero de datos (ETL) | Construye y mantiene pipelines |
| Ingeniero backend | API, base de datos |
| Ingeniero frontend | Dashboard, visualizaciones |
| Analista de datos / metodólogo | Define indicadores, valida cifras, redacta metodología |
| Asesor en gobernanza/ética de datos | Revisa nivel de agregación, principio de no daño, checklist de privacidad |
| DevOps (parcial) | CI/CD, infraestructura, backups |
| Comité asesor externo | Ver composición mínima en sección 3, punto 6 |

En una fase inicial (MVP), varios de estos roles pueden ser asumidos por 1-2 personas; se listan para dimensionar el esfuerzo real del proyecto.

---

## 16. Fases de desarrollo

| Fase | Objetivo | Entregable clave | Duración estimada |
|---|---|---|---|
| 0 | Gobernanza y metodología | Documento de principios éticos, composición del comité asesor, catálogo inicial de indicadores validado con al menos dos organizaciones aliadas | 2–3 semanas |
| 1 | Levantamiento de requerimientos | Lista priorizada de indicadores y fuentes | 2 semanas |
| 2 | Inventario de fuentes + ETL inicial | Pipelines para 3-5 fuentes prioritarias | 3–4 semanas |
| 3 | Diseño de base de datos y modelo geoespacial | Esquemas `raw/staging/curated`, `schema.sql` + migraciones | 2 semanas |
| 4 | Desarrollo de API y automatización | API v1 documentada (con paginación/CORS/cache) + jobs programados | 3 semanas |
| 5 | Diseño e implementación del dashboard | Dashboard con módulos 1-5 funcionales, responsivo | 4 semanas |
| 6 | Módulo de análisis complementario | Resúmenes basados en plantillas (Fase A), con metodología publicada | 3 semanas |
| 7 | Pruebas, documentación y despliegue | QA, pruebas de carga, docs de usuario, lanzamiento en producción | 2 semanas |
| 8 | Adopción y capacitación | Talleres con periodistas, organizaciones sociales y entidades locales | 2 semanas (transversal, inicia en fase 6) |

**Duración total estimada:** ~23–24 semanas (~5.5 meses) para un MVP funcional con módulos núcleo. Las fases 2, 5 y 6 pueden solaparse parcialmente con equipos separados. La fase 0 se amplía respecto a la estimación original porque validar principios éticos y el catálogo de indicadores con actores externos reales toma más tiempo que redactarlos internamente.

---

## 17. Riesgos y mitigación

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Cambios en APIs/formatos de fuentes oficiales | Alto | Pipelines desacoplados, tests de contrato, alertas de fallo |
| Datos sensibles mal agregados exponen individuos | Muy alto | Checklist de privacidad obligatorio (3.1), principio de agregación mínima (sección 3) |
| Inconsistencia entre fuentes (mismo indicador, cifras distintas) | Medio | Vista de reconciliación pública, no ocultar (sección 7.5) |
| Percepción de sesgo político | Alto | Neutralidad estricta, solo fuentes oficiales, metodología pública, comité asesor plural |
| Baja disponibilidad de datos a nivel vereda | Medio | Diseñar UI que degrade a nivel municipio sin errores |
| Alucinaciones o texto no verificado en módulo de análisis | Alto | Fase A basada en plantillas deterministas; Fase B con humano en el ciclo antes de publicar (sección 11) |
| Degradación de rendimiento bajo tráfico alto (API/mapa con muchos polígonos) | Medio | Pruebas de carga programadas antes de cada lanzamiento mayor (sección 20.3) |
| Dependencia de una sola persona (bus factor) | Medio | Documentación, code review, IaC |
| Costos de infraestructura crecientes | Medio | Monitoreo de uso, cacheo HTTP, límites de rate, estimación de costos explícita (sección 14) |
| Baja adopción real (plataforma existe pero nadie la usa) | Alto | Fase de capacitación dedicada (fase 8), mecanismo de retroalimentación (sección 20) |

---

## 18. Métricas de éxito

- Número de fuentes oficiales integradas y actualizadas automáticamente.
- Frecuencia de actualización real vs. objetivo por fuente.
- Cobertura territorial (% de municipios con datos en cada módulo).
- Uso del API por terceros (organizaciones, medios, investigadores).
- Tiempo de disponibilidad (uptime) del dashboard y API.
- Reportes de error recibidos y tiempo de resolución.
- Número de personas/organizaciones capacitadas en talleres de adopción (fase 8).
- Propuestas de nuevos indicadores/fuentes recibidas vía el mecanismo de co-creación (sección 20).

---

## 19. Sostenibilidad

- **Anfitrión institucional concreto.** Definir desde el inicio quién mantiene el proyecto después del MVP no como categoría abstracta ("una universidad", "una ONG") sino como conversación temprana con candidatos identificados: por ejemplo una universidad pública con centro de estudios sobre conflicto, el DNP o la Defensoría del Pueblo. Se recomienda iniciar estas conversaciones desde la fase 0, en paralelo a la conformación del comité asesor, con miras a un convenio formal de transferencia o alojamiento institucional.
- **Gobernanza comunitaria (si el proyecto se abre como open source).** Definir una hoja de ruta de gobernanza: cómo se aceptan contribuciones externas, quién tiene permisos de mantenedor, cómo se resuelven desacuerdos metodológicos entre contribuidores.
- **Licenciamiento diferenciado:**
  - Código: open source, recomendado MIT o Apache 2.0.
  - Datos derivados/curados publicados por el observatorio: CC BY 4.0, coherente con Datos Abiertos Colombia.
  - **Datos crudos originales:** conservan la licencia de su fuente original; el observatorio no reemplaza ni reinterpreta la licencia de un dataset de terceros al replicarlo, solo la documenta junto al dato (evita malentendidos legales al reutilizar información de DANE, Fiscalía, etc.).
- Documentar el proceso de "onboarding" de una nueva fuente de datos para que el proyecto pueda crecer sin depender de una sola persona.

---

## 20. Retroalimentación, co-creación y extensiones futuras

### 20.1 Mecanismo de retroalimentación y co-creación

Más allá del canal de corrección de errores (sección 3, punto 7), se habilita un formulario estructurado donde usuarios —periodistas, organizaciones sociales, entidades locales— pueden proponer nuevos indicadores o fuentes de datos. Estas propuestas alimentan directamente el backlog/roadmap del observatorio con necesidades reales del territorio, en lugar de que las prioridades las defina únicamente el equipo técnico.

### 20.2 Integración futura con sistemas de alerta en tiempo casi real

Si en el futuro se conecta con el Sistema de Alertas Tempranas de la Defensoría del Pueblo para ofrecer un módulo de "Alertas en tiempo casi real", esta integración requiere cuidado extremo en dos dimensiones:

- **Nivel de agregación**, para no comprometer la seguridad de comunidades o personas mencionadas indirectamente.
- **Retardo deliberado en la publicación**, para no interferir con procesos de protección o investigación en curso.

Esta extensión pasa obligatoriamente por revisión del comité asesor antes de habilitarse, no es una decisión unilateral del equipo técnico.

### 20.3 Pruebas de carga

Se incorpora una etapa de pruebas de estrés sobre la API y sobre el mapa (particularmente con capas de muchos polígonos, como veredas a nivel nacional) antes de cada lanzamiento mayor, para asegurar que el rendimiento no se degrade con el tráfico esperado en momentos de alta demanda (p. ej. cobertura mediática de un evento relevante).

---

## 21. Próximos pasos inmediatos

1. Validar y priorizar la lista de indicadores del catálogo (sección 7) con al menos un experto de dominio y dos organizaciones aliadas.
2. Redactar el documento de gobernanza y ética de datos (sección 3) como artefacto formal, incluyendo el checklist de privacidad (3.1) y la conformación inicial del comité asesor plural.
3. Iniciar conversaciones tempranas con posibles anfitriones institucionales a largo plazo (sección 19).
4. Elegir 3 fuentes piloto (recomendado: DANE, Datos Paz, ART/PDET) y construir el primer pipeline ETL de extremo a extremo, incluyendo los esquemas `raw/staging/curated` (sección 7.3).
5. Levantar el esqueleto del repositorio (estructura de la sección 6) y el entorno Docker de desarrollo.
6. Diseñar el esquema inicial de base de datos (sección 7), incluyendo versionado de dimensiones (7.2) y la tabla `data_quality_metrics` (7.4), y correr la primera migración.
