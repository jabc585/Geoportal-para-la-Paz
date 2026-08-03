# Auditoría integral — Observatorio para la Paz en Colombia

**Ronda 5** · 2026-08-03 · commit `e1558e4`
Documento interno. Verificado en vivo con Graphify, pytest, ruff y npm audit.

---

## Resumen ejecutivo

El proyecto alcanza su **mejor estado histórico**. Tras la poda de 47 componentes
shadcn/ui y ~40 paquetes npm no usados, el grafo pasó de 1893→1494 nodos y
3126→2432 aristas. `Lineage` (trazabilidad) es el nodo más conectado — lo que el
proyecto declara es lo que el grafo muestra.

**Puntuación global: 8.1/10** (↑2.3 desde ronda 4).

---

## 1. Arquitectura — 9.0/10

| Métrica | Valor |
|---|---|
| Nodos | 1494 (código + PostgreSQL) |
| Aristas | 2432 |
| Comunidades | 73 |
| Ciclos de importación | 0 |
| Aristas colgantes | 0 |
| Aristas duplicadas | 0 |
| Self-loops | 0 |
| Extracción | 100% (0 nodos sin verificar) |

### God nodes

| # | Nodo | Aristas | Rol |
|---|---|---|---|
| 1 | `Lineage` | 45 | Trazabilidad (fuente, URL, fecha, licencia, hash) |
| 2 | `PipelineETL` | 37 | Clase base de los 18 pipelines |
| 3 | `transaccion()` | 33 | Commit/rollback explícito |
| 4 | `insertar_serie()` | 32 | Carga batch a `curated.serie_historica` |
| 5 | `upsert_fuente()` | 29 | Catálogo de fuentes |
| 6 | `validar()` | 29 | Validación Pandera |
| 7 | `Internacional_ACLED` | 26 | Conector país-año + admin1 |
| 8 | `upsert_indicador()` | 22 | Catálogo de indicadores |
| 9 | `periodo_anual()` | 22 | Conversión año → periodo |
| 10 | `EsquemaSerieNormalizada` | 21 | Contrato de validación |

---

## 2. Calidad de código — 8.0/10

### Backend
- **Tests**: 165, deterministas, <2s
- **Cobertura total**: 68% (umbral CI: 65%)
- **pipeline.py**: 85% · **descargas.py**: 100% · **main.py**: 98% · **db.py**: 89%
- **routes/v1.py**: 82% · **config.py**: 83%
- **consultas.py**: 14% (brecha) · **run_all.py**: 0% (brecha)
- **Lint (ruff)**: 0 errores
- **Dependencias Python**: 0 CVEs

### Frontend
- **Tests**: 22 (vitest + testing-library)
- **TypeScript**: strict, 0 errores
- **Build**: 2.65s · Bundle: 548 KB app + 800 KB maplibre
- **Dependencias prod**: 7 (↓ desde ~60)
- **CVEs npm prod**: 0

---

## 3. Seguridad — 8.5/10

| Control | Estado |
|---|---|
| Inyección SQL | 100% parametrizado |
| Endpoints escritura | 0 (solo GET) |
| Rate limiting | 10/10 rutas protegidas |
| CSP | worker-src blob:, connect-src tiles |
| Headers seguridad | nosniff, Referrer-Policy, Permissions-Policy |
| CORS producción | RuntimeError si ENV=production sin CORS_ORIGINS |
| Docker | USER no-root + imagen por digest |
| Secretos | 0 tokens hardcodeados, .env fuera del repo |
| CVEs pip | 0 · CVEs npm prod | 0 |
| Umbral-k | UMBRAL_K=5 en capa SQL |
| PII | Solo agregados (CNMH: dedup en memoria, nunca a curated) |
| CI audit | pip-audit sin ignores ni ||true |

---

## 4. Rendimiento — 7.5/10

| Aspecto | Estado |
|---|---|
| Connection pooling | psycopg-pool |
| Inserciones batch | executemany + territorio memoizado |
| Raw sin iterrows() | df.to_dict("records") |
| Cache-Control | 300s default, 3600s catálogos |
| Code-splitting | maplibre 800 KB separado |
| SOCRATA_APP_TOKEN | usado en descargar_socrata_paginado |
| Raw dedup (0016) | ON CONFLICT (hash_fila, ocurrencia) |
| Prueba de carga | Script k6 listo, no ejecutado |

---

## 5. Mantenibilidad — 7.5/10

- **CI honesto**: ruff + pip-audit + pytest + npm build + npm test + migraciones sync
- **Gobernanza**: workflow mensual (schedule, abre issue)
- **Logging**: JSON en pipeline.py, cargar.py, run_all.py
- **Alerta**: etl/estado.py (exit 1 si fallidos)
- **Docs**: runbook.md (4 escenarios), operacion.md (backup/restore)
- **LICENSE**: MIT (código) + CC BY 4.0 (datos)
- **Dependabot**: grupos vite-toolchain
- **CHANGELOG**: no existe

---

## 6. API — 10 rutas GET

| Ruta | Rate | Tasa? |
|---|---|---|
| `/` | — | — |
| `/api/v1/health` | 120/min | — |
| `/api/v1/pdet/proyectos` | 120/min | — |
| `/api/v1/territorios/{c}` | 120/min | — |
| `/api/v1/territorios/{c}/indicadores` | 120/min | — |
| `/api/v1/indicadores/{c}` | 120/min | modo=tasa |
| `/api/v1/indicadores/{c}/total` | 120/min | — |
| `/api/v1/fuentes` | 120/min | — |
| `/api/v1/mapas/{c}` | 120/min | modo=tasa |
| `/api/v1/indicadores/{c}/exportar.csv` | 10/min | — |

---

## 7. Hallazgos abiertos

### Crítico
1. **consultas.py al 14%.** Toda la capa SQL de la API sin tests de integración.
   CI tiene services: postgres + 16 migraciones; falta escribir test_consulta_db.py.

### Importante
2. **run_all.py al 0%.** Orquestador sin tests. Un smoke test son ~20 líneas.
3. **Prueba de carga no ejecutada.** Script k6 listo, sin cifras de capacidad.
4. **Frontend C2-C5 pendiente.** KPIs con datos reales, mapa MapLibre, tests.
5. **frescura.py al 43%.** Módulo nuevo sin cobertura completa.

### Menor
6. **CHANGELOG inexistente.**
7. **5 CVEs npm dev** (esbuild ≤0.24.2, solo dev-server).

---

## 8. Puntuación global

| Dimensión | Puntuación |
|---|---|
| Arquitectura | 9.0 |
| Calidad de código | 8.0 |
| Seguridad | 8.5 |
| Rendimiento | 7.5 |
| Mantenibilidad | 7.5 |
| **Global** | **8.1** |
