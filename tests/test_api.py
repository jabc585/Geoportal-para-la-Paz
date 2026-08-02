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
    monkeypatch.setattr(
        rutas,
        "consultar_total",
        lambda indicador: {
            "indicador": indicador,
            "nombre": "Homicidios (Policía Nacional)",
            "unidad": "delitos",
            "totales": [{"anio": 2025, "valor": 13722.0}],
        }
        if indicador == "homicidios"
        else None,
    )
    monkeypatch.setattr(
        rutas,
        "consultar_mapa",
        lambda indicador, anio=None: {
            "indicador": indicador,
            "nombre": "Homicidios (Policía Nacional)",
            "unidad": "delitos",
            "anio": anio or 2025,
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 1]]]},
                    "properties": {
                        "codigo_divipola": "05002",
                        "municipio": "Abejorral",
                        "departamento": "Antioquia",
                        "valor": 6.0,
                    },
                }
            ],
        }
        if indicador == "homicidios"
        else None,
    )
    monkeypatch.setattr(
        rutas,
        "estado_fuentes",
        lambda: [
            {
                "variable": "PDET_URL",
                "fuente": "PDET",
                "configurada": True,
                "ayuda": "Dataset Socrata de proyectos PDET",
                "ultima_corrida_exitosa": None,
            }
        ],
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


def test_total_indicador_con_datos():
    resp = client.get("/api/v1/indicadores/homicidios/total")
    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["indicador"] == "homicidios"
    assert cuerpo["totales"][0] == {"anio": 2025, "valor": 13722.0}


def test_total_indicador_inexistente_404():
    resp = client.get("/api/v1/indicadores/nada/total")
    assert resp.status_code == 404


def test_mapa_indicador_con_capa():
    resp = client.get("/api/v1/mapas/homicidios")
    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["type"] == "FeatureCollection"
    assert len(cuerpo["features"]) == 1
    feature = cuerpo["features"][0]
    assert feature["geometry"]["type"] == "Polygon"
    assert feature["properties"]["valor"] == 6.0
    assert feature["properties"]["municipio"] == "Abejorral"


def test_mapa_indicador_inexistente_404():
    resp = client.get("/api/v1/mapas/nada")
    assert resp.status_code == 404


def test_openapi_disponible():
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    assert "/api/v1/fuentes" in resp.json()["paths"]


def test_health_reporta_estado_de_fuentes():
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["estado"] == "ok"
    assert cuerpo["fuentes"][0]["variable"] == "PDET_URL"
    assert cuerpo["fuentes"][0]["configurada"] is True
