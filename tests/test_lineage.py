"""Pruebas del módulo de linaje (sección 3, punto 4)."""

from datetime import UTC, date, datetime

from etl.common.lineage import Lineage, hash_registro


def test_hash_determinista():
    datos = {"municipio": "Abejorral", "anio": 2023, "valor": 12}
    assert hash_registro(datos) == hash_registro(dict(datos))


def test_hash_sensible_al_orden_y_contenido():
    assert hash_registro({"a": 1, "b": 2}) == hash_registro({"b": 2, "a": 1})
    assert hash_registro({"a": 1, "b": 2}) != hash_registro({"a": 1, "b": 3})


def test_lineage_completo():
    linaje = Lineage.ahora(
        fuente="DANE",
        url_origen="https://datos.gov.co/resource/x.json",
        fecha_corte_dato=date(2023, 12, 31),
        licencia="CC BY 4.0",
    )
    assert linaje.fuente == "DANE"
    assert linaje.fecha_corte_dato == date(2023, 12, 31)
    assert isinstance(linaje.fecha_extraccion, datetime)
    assert linaje.fecha_extraccion.tzinfo == UTC
