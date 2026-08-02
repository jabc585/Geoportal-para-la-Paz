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


def test_dane_transformar_con_formato_real_del_excel():
    """Formato verificado en auditoría: encabezado fila 9, columna MPIO,
    y 3 filas por municipio/año (Cabecera / Centros Poblados / Total).

    Ejemplo real: Medellín 2020 → Cabecera 2.476.569 + Centros Poblados
    43.023 = Total 2.519.592. Sin filtrar por Total se triplicaría.
    """
    df = pd.DataFrame(
        {
            "mpio": ["05001", "05001", "05001", "05002"],
            "dpmp": ["MEDELLÍN", "MEDELLÍN", "MEDELLÍN", "ABEJORRAL"],
            "ano": ["2020", "2020", "2020", "2020"],
            "area_geografica": ["Cabecera Municipal", "Centros Poblados y Rural Disperso", "Total", "Total"],
            "poblacion": ["2476569", "43023", "2519592", "23564"],
        }
    )
    resultado = DANE_Poblacion().transformar(df)
    assert len(resultado) == 2
    medellin = resultado[resultado["codigo_divipola"] == "05001"]
    assert float(medellin["valor"].iloc[0]) == 2519592.0


def test_dane_transformar_sin_columna_area_mantiene_filas():
    """Legacy Socrata sin columna de área: no se descarta nada."""
    df = pd.DataFrame(
        {
            "mpio": ["05001", "05002"],
            "ano": ["2020", "2020"],
            "poblacion": ["100", "200"],
        }
    )
    resultado = DANE_Poblacion().transformar(df)
    assert len(resultado) == 2


def test_dane_detecta_fila_encabezado_en_excel():
    """Replica el layout real: 9 filas de metadata antes del encabezado."""
    from etl.dane.pipeline import _detectar_fila_encabezado

    filas = [["TÍTULO DEL ARCHIVO"]] * 8 + [["DP", "DPNOM", "MPIO", "DPMP", "AÑO", "ÁREA GEOGRÁFICA", "Población"]]
    raw = pd.DataFrame(filas)
    assert _detectar_fila_encabezado(raw) == 8


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
