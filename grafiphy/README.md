# grafiphy — arquitectura del Observatorio para la Paz

Diagramas de arquitectura del proyecto generados con [Graphify](https://graphify.com/) (`graphifyy` en PyPI, v0.9.32) a partir del código fuente y del esquema de la base de datos PostgreSQL viva (nativo).

Regenerado el **2026-08-02 (segunda corrida)** tras implementar las 4 fases
de `plan3.md` (correcciones de `auditoria2.md`). El grafo incluye todos los
archivos nuevos: `api/limiter.py`, `api/db.py`, `etl/common/logs.py`,
`etl/common/descargas.py`, tests de conexiones/descargas/rate-limit,
y los 3 tests de frontend (vitest).

## Métricas clave

| Métrica | Anterior (auditoria2) | Actual (post-plan3) | Delta |
|---|---|---|---|
| Nodos | 1279 | **1323** | +44 |
| Aristas | 1890 | **1922** | +32 |
| Comunidades | 62 | **74** | +12 |
| Ciclos de importación | 0 | **0** | — |
| Aristas colgantes | 0 | **0** | — |
| Extracción | 98% | 98% | — |

### God nodes (más conectados)

| # | Nodo | Aristas | Cambio vs. anterior |
|---|---|---|---|
| 1 | `PipelineETL` | 32 | = (antes 32, ahora 32) |
| 2 | `upsert_fuente()` | 29 | = |
| 3 | `insertar_serie()` | 27 | = |
| 4 | `Internacional_ACLED` | 23 | ↑ nuevo en top |
| 5 | `transaccion()` | 22 | ↓ (antes 33: conectores ahora usan `insertar_indicador_internacional()`) |
| 6 | `validar()` | 22 | = |
| 7 | `upsert_indicador()` | 22 | = |
| 8 | `periodo_anual()` | 20 | = |
| 9 | `IDEAM_Ambiental` | 17 | = |
| 10 | `Policia_Homicidios` | 17 | = |

La caída de `transaccion()` de 33 a 22 aristas confirma que la refactorización
de la Fase 1.7 (helper `insertar_indicador_internacional()`) redujo el
acoplamiento directo a la BD en los conectores internacionales.

## Artefactos

| Archivo | Qué es |
|---|---|
| `ARQUITECTURA_TREE.html` | Árbol colapsable (D3 v7) de todo el proyecto: módulos, clases, funciones y la BD. Abrir en navegador (`file://`). |
| `graphify-out/grafiphy-callflow.html` | Diagramas Mermaid de arquitectura y call-flow con zoom/pan interactivo. |
| `graphify-out/graph.html` | Grafo interactivo: 1323 nodos, 1922 aristas, 74 comunidades. |
| `graphify-out/graph.json` | Grafo completo en JSON (linaje consultable con `graphify query/path/explain`). |
| `graphify-out/GRAPH_REPORT.md` | Reporte del grafo: comunidades, hubs de arquitectura, mediciones. |

El grafo incluye **código (etl/, api/, dashboard/) + esquema de la BD** (tablas `curated.*`/`raw.*`, obtenidas con `--postgres DSN` contra el Postgres de Docker) y las migraciones SQL.

## Regenerar

```bash
# venv aislado (fuera del venv del proyecto para no contaminarlo)
python3 -m venv /tmp/graphify-venv
/tmp/graphify-venv/bin/pip install "graphifyy[sql]"

# Extracción: AST local (sin API key) + esquema de la BD viva
/tmp/graphify-venv/bin/graphify extract <raiz-del-repo> --code-only \
  --postgres "postgresql://observatorio:observatorio_dev@localhost:5432/observatorio" \
  --out grafiphy

# Reporte + HTML interactivo + diagramas Mermaid
/tmp/graphify-venv/bin/graphify cluster-only grafiphy --no-label
/tmp/graphify-venv/bin/graphify tree --graph grafiphy/graphify-out/graph.json \
  --output grafiphy/ARQUITECTURA_TREE.html --root <raiz-del-repo>
/tmp/graphify-venv/bin/graphify export callflow-html --graph grafiphy/graphify-out/graph.json
```

Actualización incremental tras cambios de código (sin costo de API): `graphify update <raiz-del-repo>`.

## Consultas sobre el grafo

```bash
/tmp/graphify-venv/bin/graphify query "cómo fluyen los datos de DANE a curated" --graph grafiphy/graphify-out/graph.json
/tmp/graphify-venv/bin/graphify god-nodes --graph grafiphy/graphify-out/graph.json
```
