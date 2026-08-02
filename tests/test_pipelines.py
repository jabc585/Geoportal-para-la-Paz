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


def test_dane_lector_excel_recorta_footer(tmp_path):
    """El Excel real trae filas de pie de página totalmente vacías tras los
    datos (nota de Barrancominas, cita, fecha): deben recortarse antes del crudo."""
    import openpyxl
    from etl.dane.pipeline import _leer_excel_dane

    archivo = tmp_path / "proyecciones.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["PROYECCIONES DE POBLACIÓN 2020-2035"])
    for _ in range(7):
        ws.append(["Fuente: DANE"])
    ws.append(["DP", "DPNOM", "MPIO", "DPMP", "AÑO", "ÁREA GEOGRÁFICA", "Población"])
    ws.append(["05", "ANTIOQUIA", "05001", "MEDELLÍN", "2020", "Total", "2519592"])
    ws.append(["05", "ANTIOQUIA", "05002", "ABEJORRAL", "2020", "Total", "23564"])
    ws.append([None, None, None, None, None, None, None])
    ws.append([None, None, None, None, None, None, None])
    ws.append([None, None, None, None, None, None, None])
    ws.append(["Nota: municipio de Barrancominas...", None, None, None, None, None, None])
    wb.save(archivo)

    df = _leer_excel_dane(str(archivo), None)
    assert list(df.columns) == ["DP", "DPNOM", "MPIO", "DPMP", "AÑO", "ÁREA GEOGRÁFICA", "Población"]
    assert len(df) == 2
    assert df["MPIO"].tolist() == ["05001", "05002"]


def test_dane_pipeline_completo_contra_excel_con_footer(tmp_path, monkeypatch):
    """Ejecuta extraer+transformar con un Excel que replica el layout real
    (metadata, encabezado fila 9, footer con NaN): 1 fila limpia."""
    import openpyxl
    from etl.dane.pipeline import DANE_Poblacion

    archivo = tmp_path / "proyecciones.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["PROYECCIONES DE POBLACIÓN 2020-2035"])
    for _ in range(7):
        ws.append(["Fuente: DANE"])
    ws.append(["DP", "DPNOM", "MPIO", "DPMP", "AÑO", "ÁREA GEOGRÁFICA", "Población"])
    ws.append(["05", "ANTIOQUIA", "05001", "MEDELLÍN", "2020", "Total", "2519592"])
    ws.append([None, None, None, None, None, None, None])
    ws.append([None, None, None, None, None, None, None])
    wb.save(archivo)

    monkeypatch.setenv("DANE_POBLACION_XLSX_URL", str(archivo))
    pipeline = DANE_Poblacion()
    df, _ = pipeline.extraer()
    resultado = pipeline.transformar(df)
    assert len(resultado) == 1
    assert float(resultado["valor"].iloc[0]) == 2519592.0


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
    assert "hecho" not in resultado.columns
    fila_5002 = resultado[resultado["codigo_divipola"] == "05002"]
    assert float(fila_5002["valor"].iloc[0]) == 7.0
    fila_5001 = resultado[resultado["codigo_divipola"] == "05001"]
    assert float(fila_5001["valor"].iloc[0]) == 1.0


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


def test_pdet_transformar_con_shape_real_de_iniciativas():
    """Shape real de 'Iniciativas PDET' (datos.gov.co/gmvf-t63e, auditoría
    2026-08-02): codigodane/t_tulo_iniciativa y sin estado/avance/inversión/año.
    El conector debe normalizar sin crashear y con valores None."""
    df = pd.DataFrame(
        {
            "subregi_n": ["CUENCA DEL CAGUÁN", "CUENCA DEL CAGUÁN"],
            "codigodane": ["18610", "18592"],
            "municipio_sujeto_concertaci": ["SAN JOSÉ DEL FRAGUA", "PUERTO RICO"],
            "t_tulo_iniciativa": ["CREAR LA EPS INDÍGENA", "CREAR IPS INDÍGENA"],
            "pilar": ["3. SALUD RURAL", "3. SALUD RURAL"],
        }
    )
    resultado = ART_PDET().transformar(df)
    assert len(resultado) == 2
    assert resultado["codigo_divipola"].tolist() == ["18610", "18592"]
    assert resultado["nombre"].tolist() == ["CREAR LA EPS INDÍGENA", "CREAR IPS INDÍGENA"]
    assert resultado["anio"].isna().all()
    assert resultado["valor_inversion"].isna().all()


def test_pdet_pipeline_completo_con_respuesta_real(monkeypatch):
    """extraer() contra la forma de respuesta real del dataset Iniciativas PDET:
    las filas se normalizan con las columnas opcionales ausentes."""
    import etl.pdet.pipeline as pdet

    class Respuesta:
        def raise_for_status(self):
            pass

        def json(self):
            return [
                {"codigodane": "18610", "t_tulo_iniciativa": "CREAR LA EPS INDÍGENA"},
                {"codigodane": "18592", "t_tulo_iniciativa": "CREAR IPS INDÍGENA"},
            ]

    monkeypatch.setenv("PDET_URL", "https://www.datos.gov.co/resource/gmvf-t63e.json")
    import requests

    monkeypatch.setattr(requests, "get", lambda url, timeout: Respuesta())
    pipeline = ART_PDET()
    df, _ = pipeline.extraer()
    resultado = pipeline.transformar(df)
    assert len(resultado) == 2
    assert resultado["estado"].isna().all()
    assert resultado["anio"].isna().all()


def test_divipola_anms_faltantes_bien_formadas():
    """El suplemento de ANMs debe tener (codigo, nombre, codigo_depto) válidos."""
    from etl.common.divipola import ANMS_FALTANTES

    assert ANMS_FALTANTES
    for codigo, nombre, codigo_depto in ANMS_FALTANTES:
        assert len(codigo) == 5 and codigo.startswith("94")
        assert nombre.strip()
        assert len(codigo_depto) == 2
