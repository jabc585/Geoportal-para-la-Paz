"""Punto de entrada de la API (sección 8: FastAPI + OpenAPI en /docs).

CORS configurado explícitamente para consumo desde dashboards de terceros
(medios, universidades) con política documentada en /docs (sección 8).
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.v1 import router as v1_router


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
