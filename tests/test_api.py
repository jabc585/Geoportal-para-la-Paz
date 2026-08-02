"""Pruebas de la API v1 (sección 8) con servicios simulados — sin BD."""

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

FUENTES_FALSAS = [
    {
        "fuente_id": 1,
        "nombre": "DANE",
        "entidad": "DANE",
        "licencia": "CC BY 4.0",
        "ultima_actualizacion": "2026-01-01T00:00:00Z",
        "url_base": "https://www.dane.gov.co/",
    },
    {
        "fuente_id": 2,
        "nombre": "Unidad para las Víctimas",
        "entidad": "UARIV",
        "licencia": "Verificar",
        "ultima_actualizacion": None,
        "url_base": None,
    },
]


@pytest.fixture(autouse=True)
def simular_servicios(monkeypatch):
    import api.routes.v1 as rutas

    monkeypatch.setattr(rutas, "listar_fuentes", lambda: FUENTES_FALSAS)
    monkeypatch.setattr(
        rutas,
        "consultar_serie",
        lambda indicador, territorio=None, desde=None, hasta=None, limit=100, cursor=None: (
            [
                {
                    "serie_id": 1,
                    "indicador": indicador,
                    "municipio": "Abejorral",
                    "departamento": "Antioquia",
                    "periodo_inicio": "2020-01-01",
                    "periodo_fin": "2020-12-31",
                    "valor": 100.0,
                    "fuente": "DANE",
                    "fecha_extraccion": "2026-01-01T00:00:00Z",
                }
            ],
            None,
        ),
    )
    monkeypatch.setattr(
        rutas,
        "consultar_territorio",
        lambda codigo: {
            "municipio_id": 1,
            "codigo_divipola": codigo,
            "nombre": "Abejorral",
            "departamento": "Antioquia",
        }
        if codigo == "05002"
        else None,
    )


def test_raiz():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Observatorio" in resp.json()["nombre"]


def test_listar_fuentes():
    resp = client.get("/api/v1/fuentes")
    assert resp.status_code == 200
    datos = resp.json()
    assert len(datos) == 2
    assert datos[0]["nombre"] == "DANE"


def test_consultar_indicador():
    resp = client.get("/api/v1/indicadores/poblacion")
    assert resp.status_code == 200
    cuerpo = resp.json()
    assert len(cuerpo["items"]) == 1
    assert cuerpo["next_cursor"] is None
    assert cuerpo["items"][0]["indicador"] == "poblacion"


def test_consultar_indicador_con_filtros():
    resp = client.get(
        "/api/v1/indicadores/poblacion",
        params={"territorio": "05002", "desde": "2018-01-01", "hasta": "2023-12-31"},
    )
    assert resp.status_code == 200


def test_consultar_indicador_rechaza_limit_mayor_1000():
    resp = client.get("/api/v1/indicadores/poblacion", params={"limit": 5000})
    assert resp.status_code == 422


def test_consultar_territorio_existente():
    resp = client.get("/api/v1/territorios/05002")
    assert resp.status_code == 200
    assert resp.json()["nombre"] == "Abejorral"


def test_consultar_territorio_inexistente():
    resp = client.get("/api/v1/territorios/99999")
    assert resp.status_code == 404


def test_openapi_disponible():
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    assert "/api/v1/fuentes" in resp.json()["paths"]
