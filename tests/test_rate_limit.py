"""Test de integración: el rate limiter global debe rechazar después de
superar el límite (plan3.md, Fase 4.18).
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.testclient import TestClient


def _build_app(default_limit: str = "10/minute") -> FastAPI:
    app = FastAPI()
    limiter = Limiter(key_func=get_remote_address, default_limits=[default_limit])
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    @app.exception_handler(RateLimitExceeded)
    async def _rate_limit_exceeded(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

    @app.get("/test")
    def _test_endpoint():
        return {"ok": True}

    return app


def test_rate_limiter_rechaza_tras_limite():
    """11 requests a /test con límite 10/min → al menos uno devuelve 429."""
    app = _build_app("10/minute")
    client = TestClient(app, raise_server_exceptions=False)

    codigos = [client.get("/test").status_code for _ in range(15)]

    assert any(c == 429 for c in codigos), (
        f"Ningún request devolvió 429 tras 15 peticiones a /test "
        f"(límite 10/min). Códigos: {sorted(set(codigos))}."
    )
