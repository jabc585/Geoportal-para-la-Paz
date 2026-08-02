"""Pruebas del ciclo de transformación/carga de los pipelines piloto.

Las transformaciones se prueban sin BD ni red; la carga se prueba con una
conexión simulada en memoria.
"""

from datetime import date

import pandas as pd

from etl.common.cargar import periodo_anual, slugificar
from etl.dane.pipeline import DANE_Poblacion
from etl.pdet.pipeline import ART_PDET
from etl.victimas.pipeline import Victimas_Hechos


def test_periodo_anual():
    assert periodo_anual(2020) == (date(2020, 1, 1), date(2020, 12, 31))


def test_slugificar():
    assert slugificar("Desplazamiento forzado") == "desplazamiento_forzado"
    assert slugificar("Secuestro") == "secuestro"
    assert slugificar("  Minas  antipersonal ") == "minas_antipersonal"


def test_dane_transformar_normaliza():
    df = pd.DataFrame(
        {
            "codigo_municipio": ["5002", "5001"],
            "anio": [2020, 2020],
            "poblacion": ["100.5", "200.5"],
        }
    )
    resultado = DANE_Poblacion().transformar(df)
    assert list(resultado["codigo_divipola"]) == ["05002", "05001"]
    assert resultado["periodo_inicio"].iloc[0] == date(2020, 1, 1)
    assert float(resultado["valor"].sum()) == 301.0


def test_dane_transformar_descarta_invalidos():
    df = pd.DataFrame(
        {
            "codigo_municipio": ["5002", "5001"],
            "anio": [2020, None],
            "poblacion": ["100.5", "200.5"],
        }
    )
    resultado = DANE_Poblacion().transformar(df)
    assert len(resultado) == 1


def test_victimas_transformar_agrega_por_tipo():
    df = pd.DataFrame(
        {
            "codigo_municipio": ["5002", "5002", "5001"],
            "anio": [2020, 2020, 2020],
            "hecho": ["Desplazamiento forzado", "Desplazamiento forzado", "Secuestro"],
            "casos": [3, 4, 1],
        }
    )
    resultado = Victimas_Hechos().transformar(df)
    assert len(resultado) == 2
    fila_desplazamiento = resultado[resultado["hecho"] == "Desplazamiento forzado"]
    assert float(fila_desplazamiento["valor"].iloc[0]) == 7.0


def test_pdet_transformar_normaliza():
    df = pd.DataFrame(
        {
            "codigo_municipio": ["5002"],
            "nombre_proyecto": ["Vía veredal"],
            "estado": ["En ejecución"],
            "avance": ["45.5"],
            "valor_inversion": ["1200000000"],
            "anio": [2023],
        }
    )
    resultado = ART_PDET().transformar(df)
    assert len(resultado) == 1
    assert float(resultado["valor_inversion"].iloc[0]) == 1.2e9
