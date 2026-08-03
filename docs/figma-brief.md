# Frontend del Observatorio para la Paz en Colombia

Documento descriptivo del dashboard. Cada sección detalla qué componente existe,
qué hace, cómo se comunica con el backend y qué decisiones de diseño lo respaldan.

---

## 1. Arquitectura general

El dashboard es una **SPA (Single Page Application)** construida con
**React 18 + TypeScript 5.5 + Vite 8**. Consume exclusivamente la API REST del
backend (`/api/v1`) y no tiene estado propio persistente: cada cifra que muestra
proviene de una llamada HTTP a la API, que a su vez lee de `curated.*` en
PostgreSQL.

### Stack tecnológico

| Capa | Tecnología | Versión |
|---|---|---|
| Runtime | React | 18.3.1 |
| Lenguaje | TypeScript | 5.5.3 (strict mode) |
| Bundler | Vite | 8.2.0 (rolldown) |
| Plugin React | @vitejs/plugin-react | 6.0.5 |
| Mapas | MapLibre GL JS | 4.5.0 |
| Tests | Vitest + @testing-library/react | 4.1.0 / 16.0 |
| DOM simulado | jsdom | 24.1.0 |
| Tipografía | Inter (Google Fonts) | — |
| Estilos | CSS puro (tokens.css) | — |

### Estructura de directorios

```
dashboard/
  index.html               Entrada HTML, CSP, meta tags
  package.json             Dependencias y scripts
  vite.config.ts           Configuración de Vite + Vitest
  tsconfig.json            TypeScript strict
  src/
    main.tsx               Punto de entrada React
    App.tsx                Shell: header + main + footer
    api/
      client.ts            Cliente HTTP tipado (fetch)
      useApi.ts            Hook genérico useApi<T>
    pages/
      Inicio.tsx           Página principal (KPIs + mapa + metodología)
    components/
      KPIFuentes.tsx       KPI: conteo de fuentes oficiales
      KPIIndicador.tsx     KPI: total nacional de un indicador
      KPIPdet.tsx          KPI: proyectos PDET
      Footer.tsx           Pie de página
    maps/
      MapaNacional.tsx     Mapa coroplético interactivo
    styles/
      tokens.css           Sistema de diseño (423 líneas)
    test/
      setup.ts             Setup de testing-library
      useApi.test.tsx      6 tests del hook
      MapaNacional.test.tsx 8 tests (quintiles + formateo)
      KPIFuentes.test.tsx  3 tests smoke
      KPIIndicador.test.tsx 3 tests smoke
      KPIPdet.test.tsx     3 tests smoke
    vite-env.d.ts          Tipos de Vite para TS
```

---

## 2. Capa de comunicación con la API

### 2.1 Cliente HTTP (`client.ts`)

Archivo: `src/api/client.ts` (84 líneas)

El cliente está completamente **tipado con interfaces TypeScript** generadas a
partir de los modelos Pydantic del backend (`api/models/schemas.py`). Cada
interfaz describe la forma exacta de la respuesta JSON que el backend produce.

#### Interfaces exportadas

| Interfaz | Endpoint | Descripción |
|---|---|---|
| `Fuente` | `GET /fuentes` | Catálogo de fuentes (id, nombre, entidad, licencia, URL) |
| `TotalAnual` | (parte de IndicadorTotal) | Par año-valor del agregado nacional |
| `IndicadorTotal` | `GET /indicadores/{c}/total` | Total nacional por año de un indicador |
| `MapaFeature` | `GET /mapas/{c}` | Feature GeoJSON con propiedades (municipio, valor) |
| `MapaIndicador` | `GET /mapas/{c}` | Capa coroplética completa (indicador + features) |
| `PdetProyectos` | `GET /pdet/proyectos` | Conteos de proyectos y municipios PDET |

#### Funciones exportadas

| Función | Retorno | Uso |
|---|---|---|
| `obtenerFuentes()` | `Promise<Fuente[]>` | KPI de fuentes |
| `obtenerTotalIndicador(c)` | `Promise<IndicadorTotal>` | KPI de indicador concreto |
| `obtenerMapa(c)` | `Promise<MapaIndicador>` | Capa coroplética |
| `obtenerProyectosPdet()` | `Promise<PdetProyectos>` | KPI de PDET |
| `descargarCSV(c)` | `void` | Descarga directa de CSV |

**Mecanismo interno**: todas las funciones de lectura usan un helper genérico
`obtener<T>(ruta)` que hace `fetch` contra `BASE + ruta`, lanza `Error` si el
status no es 2xx, y devuelve `resp.json()` tipeado.

La base es `"/api/v1"`. En desarrollo, Vite proxy redirige `/api` a
`http://localhost:8000` (configurado en `vite.config.ts`).

---

### 2.2 Hook genérico `useApi<T>` (`useApi.ts`)

Archivo: `src/api/useApi.ts` (39 líneas)

Hook personalizado que encapsula el patrón de fetching de datos para **todos**
los componentes KPI y el mapa. Elimina la duplicación de `useState` +
`useEffect` + `.then/.catch` que existía en 4 componentes antes de `plan3.md`.

#### API del hook

```ts
function useApi<T>(
  llamada: () => Promise<T>,
  dependencias: readonly unknown[] = [],
): EstadoApi<T>
```

#### Estado devuelto (`EstadoApi<T>`)

| Campo | Tipo | Significado |
|---|---|---|
| `datos` | `T \| null` | Respuesta parseada, `null` mientras carga o si hay error |
| `error` | `string \| null` | Mensaje de error, `null` si éxito |
| `cargando` | `boolean` | `true` durante la petición, `false` al terminar |

#### Comportamiento

1. **Carga**: al montar o al cambiar `dependencias`, pone `cargando=true`,
   `error=null` y llama a `llamada()`.
2. **Éxito**: guarda el resultado en `datos`, `cargando=false`.
3. **Error**: si la promesa rechaza, guarda `e.message` en `error` (si `e` no es
   `Error`, guarda `"Error desconocido"`).
4. **Cancelación al desmontar**: usa una bandera `activo` con `useRef` para
   evitar `setState` sobre un componente desmontado (warning de React).
5. **Re-ejecución**: si `dependencias` cambia, se cancela la petición anterior y
   se lanza una nueva. La función `llamada` se mantiene actualizada vía
   `useRef` para evitar dependencias falsas.

---

## 3. Sistema de diseño (`tokens.css`)

Archivo: `src/styles/tokens.css` (423 líneas)

CSS puro sin preprocesador ni framework. Usa **custom properties** (variables
CSS) como único mecanismo de theming.

### 3.1 Paleta de color

| Token | Claro | Oscuro | Uso |
|---|---|---|---|
| `--color-primario` | `#0b5394` | `#6fa8dc` | Encabezado, enlaces, foco, botones hover |
| `--color-positivo` | `#2e7d32` | `#6fd07f` | (reservado para indicadores positivos) |
| `--color-alerta` | `#fb8c00` | `#f5b350` | (reservado para alertas) |
| `--color-critico` | `#d32f2f` | `#f08080` | Mensajes de error del mapa |
| `--texto` | `#14202b` | `#eef2f5` | Texto principal |
| `--texto-secundario` | `#4c5a66` | `#b7c2cb` | Etiquetas, descripciones |
| `--texto-mute` | `#7a8892` | `#8996a1` | Notas, metadatos, estados vacíos |
| `--superficie` | `#ffffff` | `#0f1720` | Fondo de página |
| `--superficie-elevada` | `#ffffff` | `#1a2530` | Tarjetas KPI, paneles |
| `--borde` | `#dfe4e8` | `#2b3947` | Bordes de inputs |
| `--borde-sutil` | `#eceff1` | `#212d38` | Bordes de tarjetas |

### 3.2 Modo oscuro

Soporte completo vía `prefers-color-scheme: dark`. Todos los tokens tienen
variante oscura. El `color-scheme: light dark` en `html` indica al navegador
que la página soporta ambos modos.

### 3.3 Tipografía

- Fuente: **Inter** (Google Fonts), con fallback a `system-ui, -apple-system,
  Segoe UI, sans-serif`.
- Pesos usados: 400 (regular), 500 (medium), 600 (semibold), 700 (bold).
- `font-variant-numeric: tabular-nums` en valores KPI para alineación estable.
- `text-wrap: balance` en headings para evitar líneas huérfanas.

### 3.4 Escala y ritmo

| Token | Valor | Uso |
|---|---|---|
| `--radio` | `10px` | Bordes redondeados de tarjetas KPI y paneles |
| `--radio-chico` | `6px` | Bordes de inputs, botones, mapa |
| `--sombra` | `0 1px 2px rgba(20,32,43,0.06), 0 2px 8px rgba(20,32,43,0.05)` | Elevación sutil |
| `--ancho-contenido` | `1200px` | Ancho máximo del contenido |

### 3.5 Accesibilidad

- **Foco visible**: `:focus-visible` con outline de 2px en el color primario.
- **Navegación por teclado**: todos los elementos interactivos (enlaces,
  botones, select) tienen anillo de foco.
- **Contraste**: los tokens de color se eligieron para contraste AA/AAA sobre
  sus respectivas superficies.

---

## 4. Componentes

### 4.1 Shell (`App.tsx`)

Archivo: `src/App.tsx` (24 líneas)

Componente raíz. Renderiza tres bloques:

1. **Encabezado** (`<header>`): sticky, fondo `--color-primario`, con el título
   "Observatorio para la Paz en Colombia" y una navegación de 4 enlaces:
   - Inicio (`#inicio`)
   - Mapa Nacional (`#mapa`)
   - Metodología (`#metodologia`)
   - API (`http://localhost:8000/docs`, abre en pestaña nueva)

2. **Contenido principal** (`<main>`): ancho máximo 1200px, centrado. Contiene
   el componente `<Inicio />`.

3. **Pie de página** (`<Footer />`): licencia CC BY 4.0, enlace a la
   documentación de la API.

### 4.2 Página de inicio (`Inicio.tsx`)

Archivo: `src/pages/Inicio.tsx` (51 líneas)

Página única de la SPA. Tres secciones:

#### Sección "Indicadores principales" (`#inicio`)

Grid responsive de 4 KPIs:

| KPI | Componente | Indicador | Fuente real |
|---|---|---|---|
| Fuentes oficiales | `KPIFuentes` | — | `GET /fuentes` |
| Homicidios | `KPIIndicador` | `homicidios` | Policía Nacional (SIEDCO 2025) |
| Víctimas RUV | `KPIIndicador` | `victimas_ruv` | UARIV (Datos Paz) |
| Población | `KPIIndicador` | `poblacion` | DANE (proyecciones 2020-2035) |
| Proyectos PDET | `KPIPdet` | — | ART (Socrata) |

El array `KPIS_PLANIFICADOS` permite añadir KPIs futuros que se renderizan como
placeholders con borde punteado y el texto "Próximamente", sin inventar cifras.

#### Sección "Mapa Nacional" (`#mapa`)

Panel con cabecera (título + nota "Capa coroplética por quintiles, agregado
municipal"), el componente `<MapaNacional />` y un enlace a la sección de
metodología.

#### Sección "Metodología" (`#metodologia`)

Panel con texto explicativo sobre trazabilidad, linaje de datos y fichas
metodológicas en `docs/fuentes/`.

### 4.3 KPIs

Los tres componentes KPI comparten el mismo patrón:

1. Llaman al hook `useApi` con la función del cliente correspondiente.
2. Renderizan una tarjeta (`.kpi`) con etiqueta, valor y subetiqueta opcional.
3. Estados:
   - **Cargando**: muestra `…` en el valor, color atenuado.
   - **Error**: muestra `"API no disponible"` en el valor, color atenuado.
   - **Éxito**: muestra el valor formateado con separadores de miles
     (`Intl.NumberFormat("es-CO")`).
   - **Sin datos**: muestra `"Sin datos"` (solo `KPIIndicador`, cuando la API
     responde 200 con `totales: []`).

#### `KPIFuentes.tsx` (15 líneas)

- Llama a `obtenerFuentes()`.
- Muestra `datos?.length` (número de fuentes oficiales integradas).

#### `KPIIndicador.tsx` (38 líneas)

- Recibe props: `codigo`, `etiqueta`, `unidad?`.
- Llama a `obtenerTotalIndicador(codigo)`.
- Muestra el valor del año más reciente (`datos.totales[0]`) con subetiqueta
  `"<año> · <unidad>"`.

#### `KPIPdet.tsx` (15 líneas)

- Llama a `obtenerProyectosPdet()`.
- Muestra `datos.proyectos.toLocaleString("es-CO")` (conteo de proyectos PDET).

### 4.4 Mapa Nacional (`MapaNacional.tsx`)

Archivo: `src/maps/MapaNacional.tsx` (241 líneas)

El componente más complejo del dashboard. Renderiza un mapa coroplético
interactivo de Colombia con datos municipales agregados.

#### Datos geoespaciales

- **Teselas base**: OpenStreetMap raster (tile.openstreetmap.org).
- **Capa coroplética**: GeoJSON devuelto por `GET /mapas/{indicador}`. La
  geometría viene simplificada (~110 m de tolerancia) desde PostGIS
  (`ST_SimplifyPreserveTopology`) y se pinta por quintiles.
- **Proyección**: Web Mercator (EPSG:3857), la nativa de MapLibre.
- **Vista inicial**: centrada en Colombia ([-73.5, 4.5], zoom 5).

#### Indicadores disponibles en el selector

| Código | Etiqueta | Fuente |
|---|---|---|
| `homicidios` | Homicidios (Policía Nacional) | SIEDCO 2025 |
| `victimas_ruv` | Personas incluidas en el RUV (UARIV) | Datos Paz |
| `poblacion` | Población proyectada (DANE) | Proyecciones 2020-2035 |
| `ideam_deforestacion` | Deforestación ha (IDEAM) | Raster Bosque/No Bosque |
| `hdx_conflicto_eventos` | Eventos de conflicto (HDX) | HAPI Colombia |
| `cnmh_desaparicion_victimas` | Desaparición forzada (CNMH) | SIEVCAC |

#### Paleta de color

**Viridis** (verificada para daltonismo, perceptual uniforme):

| Quintil | Color | Significado |
|---|---|---|
| Q1 (mín–20%) | `#fde725` (amarillo) | Valores más bajos |
| Q2 (20–40%) | `#addc30` (verde claro) | |
| Q3 (40–60%) | `#5ec962` (verde) | |
| Q4 (60–80%) | `#21918c` (teal) | |
| Q5 (80%–máx) | `#440154` (púrpura oscuro) | Valores más altos |
| Sin dato | `#e3e6e8` (gris) | Municipio sin dato en ese indicador |

#### Interactividad

- **Hover**: popup con nombre del municipio, departamento y valor formateado con
  unidad. Construido con `setDOMContent()` (DOM seguro, sin `innerHTML`).
- **Selector de indicador**: `<select>` con los 6 indicadores. Cambiar
  recarga la capa y actualiza la leyenda.
- **Exportación CSV**: botón que dispara `descargarCSV(indicador)` — descarga
  directa de `GET /indicadores/{c}/exportar.csv`.
- **Exportación GeoJSON**: botón que genera un Blob con la capa actual y lo
  descarga como archivo `.geojson`.

#### Funciones puras exportadas (testeables)

| Función | Firma | Descripción |
|---|---|---|
| `quintiles` | `(number[]) → number[]` | Calcula 4 cortes de quintil sobre un array de valores |
| `formatearValor` | `(number) → string` | Formato colombiano con 1 decimal (`Intl.NumberFormat`) |

#### Estructura interna

1. **Efecto 1** (montaje): crea la instancia de `maplibregl.Map` con el estilo
   base OSM y la guarda en `useRef`.
2. **Efecto 2** (cambio de indicador): llama a `useApi(() => obtenerMapa(indicador),
   [indicador])`. Al recibir datos, calcula quintiles y los guarda en estado.
3. **Efecto 3** (cambio de datos): añade o actualiza la fuente GeoJSON, la capa
   de relleno (`fill`) con expresión `step` para los quintiles, la capa de
   borde (`line`) y los handlers de hover/popup.

#### Estados visuales

- **Cargando**: el selector y la leyenda se renderizan; el contenedor del mapa
  muestra "Cargando…" en la etiqueta del año.
- **Error**: mensaje rojo "No se pudo cargar el mapa: <mensaje>".
- **Sin datos**: año muestra "Sin datos aún", leyenda muestra nota "Valores por
  quintiles cuando haya al menos 5 municipios con dato."
- **Con datos**: mapa renderizado con polígonos coloreados, leyenda con escala
  de 6 entradas (sin dato + 5 quintiles + máximo), año del agregado.

#### Responsive

El contenedor del mapa mide 420px de alto en desktop y 320px en mobile
(`max-width: 640px`).

### 4.5 Footer (`Footer.tsx`)

Archivo: `src/components/Footer.tsx` (15 líneas)

Pie de página con dos elementos: nota sobre trazabilidad y licencia CC BY 4.0,
y enlace a la documentación interactiva de la API (`/docs` de FastAPI).

---

## 5. Configuración de Vite

Archivo: `vite.config.ts` (30 líneas)

### Plugins

- `@vitejs/plugin-react`: transformación JSX y Fast Refresh.

### Dev server

- Puerto: `5173`
- Proxy: `/api` → `http://localhost:8000` (evita CORS en desarrollo).

### Build

- **Code-splitting**: `manualChunks` como función (compatible con rolldown de
  Vite 8) que separa `maplibre-gl` en su propio chunk (~787 KB).
- **Chunk de aplicación**: ~150 KB (React + componentes).

### Vitest

- **Entorno**: `jsdom` (simula DOM para testing-library).
- **Setup**: `src/test/setup.ts` (importa `@testing-library/jest-dom/vitest`).
- **Globals**: `true` (describe, it, expect disponibles sin import).

---

## 6. Seguridad del frontend

### 6.1 Content Security Policy (CSP)

Definida en `index.html` como meta tag:

```
default-src 'self';
script-src 'self';
worker-src 'self' blob:;
style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
font-src 'self' https://fonts.gstatic.com data:;
img-src 'self' data: blob: https://tile.openstreetmap.org;
connect-src 'self' ws: wss: https://tile.openstreetmap.org;
object-src 'none';
base-uri 'self'
```

> **`frame-ancestors` no va en el meta tag.** El navegador la descarta cuando la
> CSP se entrega por `<meta>` —solo surte efecto como cabecera HTTP— y además
> emite un error en consola. Estuvo declarada ahí, de modo que la protección
> anti-clickjacking parecía puesta sin estarlo. Ahora se envía como cabecera
> desde `vite.config.ts` (`server` y `preview`) y desde el middleware de la API.
> **En producción debe configurarla el servidor estático que sirva el build**;
> el `<meta>` no basta.

#### Decisiones de la CSP

| Directiva | Valor | Justificación |
|---|---|---|
| `worker-src blob:` | MapLibre carga su motor de renderizado en un Web Worker desde URL blob | Sin esto, el mapa no dibuja nada (bug de plan4.md) |
| `connect-src https://tile.openstreetmap.org` | MapLibre pide teselas con `fetch()`, no con `<img>` | `img-src` tenía el host pero no aplica; `connect-src` es la directiva correcta |
| `script-src 'self'` | Sin `blob:` ni `unsafe-inline` | Solo se abre la excepción en `worker-src`, no en `script-src` |
| `frame-ancestors 'none'` | Previene clickjacking | La SPA no debe embeberse en iframes de terceros — **por cabecera HTTP, no por meta** |

### 6.2 Otras cabeceras de seguridad

El backend añade (middleware en `api/main.py`):

- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: no-referrer`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- `Content-Security-Policy: frame-ancestors 'none'` y `X-Frame-Options: DENY`
  (cubren también `/docs`, que es superficie real de enmarcado)

### 6.3 Popup del mapa

El popup de hover se construye con `setDOMContent()` usando `createElement` +
`createTextNode`. **No se usa `innerHTML` ni `setHTML()`** — inmune a XSS vía
datos de la API.

### 6.4 Dependencias

- `npm audit --production`: **0 vulnerabilidades** (verificado 2026-08-03).
- TypeScript en modo `strict` (sin `any` implícito, sin parámetros sin usar).
- Vite 8 con plugin-react 6, vitest 4, todo pineado con `^` y lockfile.

---

## 7. Tests

23 tests en 5 archivos, todos pasando en `jsdom` (sin navegador real).

### 7.1 Hook `useApi` (6 tests)

| Test | Qué verifica |
|---|---|
| Carga inicial | `cargando=true`, `datos=null`, `error=null` |
| Éxito | Resuelve la promesa, `datos` contiene el valor |
| Error con mensaje | Promesa rechazada con `Error`, `error` contiene el mensaje |
| Error sin mensaje | Promesa rechazada con string, `error = "Error desconocido"` |
| Cancelación al desmontar | Desmontar antes de resolver no actualiza el estado |
| Cambio de dependencias | Nueva dependencia dispara nueva llamada |

### 7.2 Mapa (`MapaNacional.test.tsx`, 8 tests)

| Grupo | Tests | Qué verifica |
|---|---|---|
| `quintiles()` | 4 | 10 valores, 3 valores, valores repetidos, negativos+cero |
| `formatearValor()` | 4 | Millones, decimales, cero, negativos |

### 7.3 Componentes KPI (9 tests)

Cada componente (3) prueba 3 estados:
1. Render con datos mockeados (verifica el valor formateado).
2. Estado de carga (`cargando=true` → muestra `…`).
3. Estado de error (`error` no nulo → muestra `"API no disponible"`).

### 7.4 Cobertura

No se mide cobertura del frontend (vitest no tiene `--cov` configurado). Los 23
tests cubren la lógica de fetching (`useApi`), las funciones puras del mapa
(`quintiles`, `formatearValor`) y el contrato de renderizado de los 3 KPIs.

---

## 8. Métricas del bundle

| Chunk | Tamaño | Gzip | Contenido |
|---|---|---|---|
| `index-*.js` | 149.97 KB | 49.08 KB | Aplicación (React + componentes + cliente API) |
| `maplibre-*.js` | 786.54 KB | 209.95 KB | MapLibre GL JS (motor de renderizado WebGL) |
| `index-*.css` | 71.43 KB | 10.89 KB | Estilos (tokens.css completo) |
| `index.html` | 1.38 KB | 0.66 KB | Entrada HTML + CSP |

---

## 9. Estados de la UI

Cada componente visible para el usuario maneja explícitamente 4 estados:

| Estado | KPIs | Mapa |
|---|---|---|
| **Carga** | `…` en gris | "Cargando…" en etiqueta de año |
| **Error** | "API no disponible" en gris | Mensaje rojo con detalle |
| **Vacío** | "Sin datos" (solo KPIIndicador) | "Sin datos aún", leyenda con nota |
| **Éxito** | Valor formateado con separadores | Mapa renderizado con leyenda de quintiles |

**No hay estado de carga infinita**: todas las promesas tienen timeout
implícito vía `fetch` del navegador, y el hook `useApi` limpia la bandera al
desmontar.

---

## 10. Navegación

La SPA tiene una sola página con navegación por anclas:

1. **Inicio** (`#inicio`) — KPIs principales.
2. **Mapa Nacional** (`#mapa`) — Mapa coroplético interactivo.
3. **Metodología** (`#metodologia`) — Nota sobre trazabilidad y linaje.
4. **API** (`http://localhost:8000/docs`) — Documentación interactiva (Swagger),
   abre en pestaña nueva.

El encabezado es sticky (`position: sticky; top: 0`) para mantener la
navegación visible al hacer scroll.

---

## 11. Renderizado condicional y placeholders

### KPIs planificados

El array `KPIS_PLANIFICADOS` en `Inicio.tsx` permite declarar KPIs futuros sin
datos aún. Se renderizan con clase `.es-placeholder`:

- Borde punteado (no simula un dato real).
- Fondo transparente.
- Texto "Próximamente" en el valor.

### Leyenda del mapa

- **Con ≥5 municipios con dato**: escala de 7 entradas (sin dato + Q1–Q4 +
  máximo).
- **Con <5 municipios**: nota explicativa "Valores por quintiles cuando haya al
  menos 5 municipios con dato."

---

## 12. Dependencia de datos reales

El dashboard **no tiene datos hardcodeados**. Cada cifra proviene de la API, que
lee de `curated.*` en PostgreSQL. Si la API no está disponible:

- Los KPIs muestran "API no disponible".
- El mapa muestra "No se pudo cargar el mapa".
- Ningún componente falla con error no controlado (todas las promesas tienen
  `.catch`).

Esto fue verificado en vivo en las 4 rondas de auditoría: con Postgres detenido,
el dashboard renderiza correctamente todos sus estados de error sin crashes.
