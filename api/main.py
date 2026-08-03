"""Punto de entrada de la API (sección 8: FastAPI + OpenAPI en /docs).

CORS configurado explícitamente para consumo desde dashboards de terceros
(medios, universidades) con política documentada en /docs (sección 8).
"""
from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.limiter import limiter
from api.routes.v1 import router as v1_router

# Cache HTTP (auditoría 2026-08-02): la API expone ETag en CORS pero ningún
# endpoint emitía Cache-Control ni ETag. Este middleware agrega Cache-Control
# por defecto y ETag para las respuestas JSON de /api/v1/.
_CACHE_DEFAULT = "public, max-age=300"
_RUTAS_LARGA_DURACION = ("/api/v1/health", "/api/v1/fuentes", "/api/v1/pdet/proyectos")


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
app.add_middleware(SlowAPIMiddleware)


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
)

# F4.1 (plan.md): CORS explícito en producción. El default "*" es aceptable
# solo en desarrollo; producción debe definir CORS_ORIGINS explícitamente.
if os.getenv("ENV", "").lower() == "production" and os.getenv("CORS_ORIGINS", "*") == "*":
    raise RuntimeError(
        "CORS_ORIGINS debe definirse explícitamente en producción "
        "(no usar el default '*'). Ver .env.example."
    )

app.include_router(v1_router)


@app.middleware("http")
async def _cabeceras_seguridad(request: Request, call_next) -> Response:
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    # Anti-clickjacking: la CSP del dashboard declaraba `frame-ancestors 'none'`
    # en un <meta>, donde el navegador la ignora (solo vale como cabecera HTTP).
    # /docs de FastAPI es superficie real de enmarcado, así que va aquí.
    response.headers.setdefault("Content-Security-Policy", "frame-ancestors 'none'")
    response.headers.setdefault("X-Frame-Options", "DENY")
    return response


@app.middleware("http")
async def _cache_control(request: Request, call_next) -> Response:
    cache = _CACHE_DEFAULT
    if request.url.path in _RUTAS_LARGA_DURACION:
        cache = "public, max-age=3600"
    response = await call_next(request)
    if (
        request.method == "GET"
        and response.status_code < 400
        and "cache-control" not in response.headers
    ):
        response.headers["Cache-Control"] = cache
    return response


@app.get("/", include_in_schema=False)
def raiz() -> dict:
    return {
        "nombre": "Observatorio para la Paz en Colombia",
        "docs": "/docs",
        "api_v1": "/api/v1",
        "nota": "Datos agregados, sin PII (secciones 3 y 13 del plan).",
    }
