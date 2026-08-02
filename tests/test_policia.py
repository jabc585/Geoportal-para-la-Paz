"""Pruebas del conector Policía Nacional (plan2.md Fase B, fuente 5).

Replica los shapes reales verificados en vivo (2026-08-02): columnas
codigo_dane (DIVIPOLA 5 + "000"), fecha_hecho (dd/mm/aaaa) y cantidad por
segmento demográfico.
"""

import pandas as pd
import pytest

from etl.policia.pipeline import DELITOS, Policia_Delitos


def _df_hurto():
    return pd.DataFrame(
        {
            "codigo_dane": ["44420000", "44420000", "05001000", "44420000"],
            "municipio": ["La Jagua del Pilar", "La Jagua del Pilar", "Medellín", "La Jagua del Pilar"],
            "fecha_hecho": ["28/04/2024", "28/04/2024", "15/03/2024", "01/01/2025"],
            "tipo_de_hurto": ["HURTO ABIGEATO", "HURTO A PERSONAS", "HURTO ABIGEATO", "HURTO A PERSONAS"],
            "cantidad": ["1", "2", "1", "5"],
        }
    )


def test_delitos_cubren_los_tres_datasets_reales():
    assert set(DELITOS) == {"hurto", "violencia", "sexuales"}
    assert DELITOS["hurto"]["resource_id"] == "d4fr-sbn2"
    assert DELITOS["violencia"]["resource_id"] == "vuyt-mqpw"
    assert DELITOS["sexuales"]["resource_id"] == "fpe5-yrmw"


def test_delito_desconocido_rechazado():
    with pytest.raises(ValueError, match="Delito Policía desconocido"):
        Policia_Delitos("homicidios")


def test_pipeline_id_por_delito():
    assert Policia_Delitos("hurto").pipeline_id == "policia_hurto"
    assert Policia_Delitos("sexuales").tabla_raw == "policia_sexuales"


def test_transformar_hurto_suma_cantidad_y_recorta_codigo():
    resultado = Policia_Delitos("hurto").transformar(_df_hurto())
    filas = resultado.sort_values("valor").to_dict("records")
    # 05001/2024: abigeato 1; 44420/2024: abigeato 1 + personas 2; 44420/2025: personas 5
    assert len(filas) == 4
    assert filas[0]["codigo_divipola"] == "05001"
    assert filas[0]["valor"] == 1
    assert filas[1]["codigo_divipola"] == "44420"  # sin el sufijo "000"
    assert filas[1]["valor"] == 1
    assert filas[2]["valor"] == 2
    assert filas[2]["periodo_inicio"].year == 2024
    assert filas[3]["valor"] == 5
    assert filas[3]["periodo_inicio"].year == 2025


def test_transformar_violencia_sin_dimension():
    df = pd.DataFrame(
        {
            "codigo_dane": ["05001000"],
            "fecha_hecho": ["10/10/2023"],
            "cantidad": ["3"],
        }
    )
    resultado = Policia_Delitos("violencia").transformar(df)
    fila = resultado.iloc[0]
    assert fila["dimension"] == "violencia_intrafamiliar"
    assert fila["valor"] == 3


def test_transformar_fechas_invalidas_se_descartan():
    df = pd.DataFrame(
        {
            "codigo_dane": ["05001000", "05001000"],
            "fecha_hecho": ["31/02/2024", "10/10/2023"],
            "tipo_de_hurto": ["HURTO A PERSONAS", "HURTO A PERSONAS"],
            "cantidad": ["3", "1"],
        }
    )
    resultado = Policia_Delitos("hurto").transformar(df)
    assert len(resultado) == 1  # 31/02 no existe → descartada


def test_transformar_vacio():
    assert Policia_Delitos("hurto").transformar(pd.DataFrame()).empty
