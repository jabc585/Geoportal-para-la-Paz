// Prueba de carga k6 — Observatorio para la Paz (plan.md §F5.1)
//
// Uso:
//   k6 run tests/load/load_test.js
//
// Mide RPS sostenido, p95 y punto de saturación del pool contra los 4
// endpoints calientes. Requiere Postgres cargado (run_all) y API corriendo.
// El rate limit debe desactivarse o elevarse durante la medición:
//   API_RATE_LIMIT=99999 uvicorn api.main:app ...

import { check, sleep } from "k6";
import http from "k6/http";

const BASE = __ENV.API_URL || "http://localhost:8000/api/v1";

export const options = {
  stages: [
    { duration: "30s", target: 5 },   // calentamiento
    { duration: "1m", target: 20 },   // carga moderada
    { duration: "1m", target: 50 },   // carga alta
    { duration: "30s", target: 0 },   // enfriamiento
  ],
  thresholds: {
    http_req_duration: ["p(95)<3000"],  // 95% < 3s
    http_req_failed: ["rate<0.05"],      // <5% errores
  },
};

export default function () {
  const endpoints = [
    `${BASE}/fuentes`,
    `${BASE}/indicadores/homicidios`,
    `${BASE}/indicadores/homicidios/total`,
    `${BASE}/mapas/homicidios`,
  ];

  for (const url of endpoints) {
    const res = http.get(url);
    check(res, {
      "status 200": (r) => r.status === 200,
      "response time < 2s": (r) => r.timings.duration < 2000,
    });
  }

  sleep(1);
}
