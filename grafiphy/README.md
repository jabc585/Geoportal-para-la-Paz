# grafiphy — arquitectura del Observatorio para la Paz

Diagramas de arquitectura del proyecto generados con [Graphify](https://graphify.com/) (`graphifyy` en PyPI, v0.9.32) a partir del código fuente y del esquema de la base de datos PostgreSQL viva (Docker).

Regenerado el 2026-08-02 contra el árbol de trabajo actual (incluye el rediseño
sin commitear de `dashboard/`) + esquema real de PostgreSQL 17/PostGIS (nativo,
no Docker — ver `AUDITORIA.md`).

## Artefactos

| Archivo | Qué es |
|---|---|
| `AUDITORIA.md` | Síntesis de esta corrida: god nodes, comunidades, y verificación en vivo de que el pipeline de DANE ya carga datos reales a `curated` de punta a punta. |
| `ARQUITECTURA_TREE.html` | Árbol colapsable (D3 v7) de todo el proyecto: módulos, clases, funciones y la BD. Abrir en navegador (`file://`). |
| `graphify-out/grafiphy-callflow.html` | Diagramas Mermaid de arquitectura y call-flow con zoom/pan interactivo. |
| `graphify-out/graph.html` | Grafo interactivo completo: 1115 nodos, 1519 aristas, 42 comunidades. |
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
