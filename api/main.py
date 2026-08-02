"""Punto de entrada de la API (sección 8: FastAPI + OpenAPI en /docs).

CORS configurado explícitamente para consumo desde dashboards de terceros
(medios, universidades) con política documentada en /docs (sección 8).
"""
from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from api.routes.v1 import router as v1_router

# Rate limiting (auditoría 2026-08-02, OWASP API4:2023): la API es pública; los
# límites por IP evitan agotamiento de recursos antes de exponerla fuera de
# loopback. Umbrales conservadores y configurables con API_RATE_LIMIT.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[os.getenv("API_RATE_LIMIT", "120/minute")],
)


def os_env_list(nombre: str, default: str) -> list[str]:
    return [o.strip() for o in os.getenv(nombre, default).split(",") if o.strip()]


app = FastAPI(
    title="Observatorio para la Paz en Colombia - API",
    description=(
        "API pública de datos oficiales sobre paz, conflicto y desarrollo "
        "territorial en Colombia. Solo lectura; cada cifra conserva su linaje "
        "(fuente, url, fecha de extracción)."
    ),
    version="0.1.0",
    contact={"name": "Observatorio para la Paz", "url": "https://www.datos.gov.co/"},
    license_info={"name": "CC BY 4.0 (datos curados del observatorio)"},
)

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def _rate_limit_exceeded(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": "Límite de solicitudes excedido; reintentar más tarde."},
        headers={"Retry-After": "60"},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=os_env_list("CORS_ORIGINS", default="*"),
    allow_methods=["GET"],
    allow_headers=["*"],
    expose_headers=["ETag"],
)

app.include_router(v1_router)


@app.get("/", include_in_schema=False)
def raiz() -> dict:
    return {
        "nombre": "Observatorio para la Paz en Colombia",
        "docs": "/docs",
        "api_v1": "/api/v1",
        "nota": "Datos agregados, sin PII (secciones 3 y 13 del plan).",
    }
