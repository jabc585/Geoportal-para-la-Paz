"""Test de integración: el rate limiter debe proteger la app real con
include_router (plan4.md, Bug 2).

Para forzar un límite bajo sin que otros tests interfieran, recargamos
api.routes.v1 tras inyectar la variable de entorno. La app se importa
dentro de cada test para que el reload surta efecto.
"""

from __future__ import annotations

import importlib
from unittest.mock import patch

from starlette.testclient import TestClient


def _app_con_limite(monkeypatch, limite: str = "5/minute") -> TestClient:
    monkeypatch.setenv("API_RATE_LIMIT", limite)
    # Recargar el router para re-evaluar os.getenv en los decoradores
    import api.limiter
    import api.main
    import api.routes.v1

    importlib.reload(api.limiter)
    importlib.reload(api.routes.v1)
    importlib.reload(api.main)
    return TestClient(api.main.app, raise_server_exceptions=False)


def test_rate_limiter_protege_rutas(monkeypatch):
    """10 requests a /api/v1/fuentes con límite 5/min → al menos un 429."""
    client = _app_con_limite(monkeypatch, "5/minute")
    with patch("api.routes.v1.listar_fuentes", return_value=[]):
        codigos = [client.get("/api/v1/fuentes").status_code for _ in range(10)]
    assert any(c == 429 for c in codigos), (
        f"Ningún 429 tras 10 requests a /api/v1/fuentes (límite 5/min). "
        f"Códigos: {sorted(set(codigos))}."
    )


def test_rate_limiter_protege_health(monkeypatch):
    """El endpoint /health también debe ser rate-limited."""
    client = _app_con_limite(monkeypatch, "5/minute")
    with patch("api.routes.v1.estado_fuentes", return_value=[]):
        codigos = [client.get("/api/v1/health").status_code for _ in range(10)]
    assert any(c == 429 for c in codigos), (
        f"Ningún 429 en /api/v1/health tras 10 requests. "
        f"Códigos: {sorted(set(codigos))}."
    )


def test_rate_limiter_respeta_exportar_csv(monkeypatch):
    """El decorador @limiter.limit('10/minute') de exportar.csv."""
    client = _app_con_limite(monkeypatch, "5/minute")
    with patch("api.routes.v1.exportar_serie_csv", return_value=[
        {"indicador": "x", "indicador_nombre": "X", "unidad": "u",
         "codigo_divipola": "05", "municipio": "a", "departamento_divipola": "05",
         "departamento": "b", "periodo_inicio": "2020-01-01", "periodo_fin": "2020-12-31",
         "valor": 1.0, "fuente": "c"}
    ]):
        codigos = [client.get("/api/v1/indicadores/homicidios/exportar.csv").status_code for _ in range(12)]
    assert any(c == 429 for c in codigos), (
        f"El decorador @limiter.limit('10/minute') de exportar.csv no rechazó. "
        f"Códigos: {sorted(set(codigos))}."
    )
