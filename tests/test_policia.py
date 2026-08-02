"""Pruebas del conector Policía Nacional (plan2.md Fase B, fuente 5).

Replica los shapes reales verificados en vivo (2026-08-02): columnas
codigo_dane (DIVIPOLA 5 + "000"), fecha_hecho (dd/mm/aaaa) y cantidad por
segmento demográfico. Para homicidios: el Excel oficial SIEDCO con cabecera
en la fila 10 (metadatos arriba) y columnas en mayúsculas.
"""

import io

import pandas as pd
import pytest

from etl.policia.pipeline import (
    HOMICIDIOS_ANIOS_DEFAULT,
    HOMICIDIOS_URL_PATRON,
    DELITOS,
    Policia_Delitos,
    Policia_Homicidios,
)


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


# ── Homicidios (Excel oficial SIEDCO, verificado en vivo 2026-08-02) ──────

HEADER_HOMICIDIOS = [
    "ARMAS MEDIOS", "DEPARTAMENTO", "MUNICIPIO", "FECHA HECHO",
    "GENERO", "*AGRUPA EDAD PERSONA*", "CODIGO DANE", "CANTIDAD",
]


def _df_homicidios():
    return pd.DataFrame(
        [
            ["ARMA BLANCA", "CUNDINAMARCA", "Bogotá D.C. (CT)", "01/01/2025", "MASCULINO", "ADULTOS", "11001000", "1"],
            ["ARMA BLANCA", "CUNDINAMARCA", "Bogotá D.C. (CT)", "01/01/2025", "FEMENINO", "ADULTOS", 11001000, "1"],
            ["ARMA DE FUEGO", "ANTIOQUIA", "Envigado", "15/03/2025", "MASCULINO", "ADULTOS", "05266000", "1"],
            ["ARMA BLANCA", "CESAR", "Chimichagua", "02/01/2025", "MASCULINO", "ADULTOS", "20175000", "2"],
        ],
        columns=HEADER_HOMICIDIOS,
    )


def _excel_homicidios_bytes():
    """Excel con metadatos en filas 0-9, cabecera en la fila 10 y 2 filas de datos."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        pd.DataFrame([[f"METADATO {i}"] for i in range(10)]).to_excel(w, header=False, index=False)
        _df_homicidios().to_excel(w, startrow=10, index=False, header=True)
    buf.seek(0)
    return buf


def test_homicidios_urls_patron_por_anio():
    p = Policia_Homicidios()
    urls = p._urls_a_descargar()
    assert urls == [HOMICIDIOS_URL_PATRON.format(anio=a) for a in HOMICIDIOS_ANIOS_DEFAULT]
    assert "Homicidio%20Intencional2025.xlsx" in urls[0]


def test_homicidios_urls_variable_configurada(monkeypatch):
    monkeypatch.setattr("etl.policia.pipeline.settings.policia_homicidios_url",
                        "https://a.test/2025.xlsx, https://b.test/2024.xlsx")
    urls = Policia_Homicidios()._urls_a_descargar()
    assert urls == ["https://a.test/2025.xlsx", "https://b.test/2024.xlsx"]


def test_homicidios_descarga_404_devuelve_none(monkeypatch):
    class _Resp404:
        status_code = 404

        def raise_for_status(self):
            raise RuntimeError("404")

    monkeypatch.setattr("etl.policia.pipeline.requests.get", lambda *a, **k: _Resp404())
    assert Policia_Homicidios()._descargar_excel("https://x.test/nada.xlsx") is None


def test_homicidios_transformar_suma_y_recorta_codigo():
    resultado = Policia_Homicidios().transformar(_df_homicidios())
    filas = resultado.to_dict("records")
    bogota = [f for f in filas if f["codigo_divipola"] == "11001"]
    assert bogota[0]["valor"] == 2  # las dos filas de Bogotá (str y float) se suman
    assert bogota[0]["periodo_inicio"].year == 2025
    envigado = [f for f in filas if f["codigo_divipola"] == "05266"]
    assert envigado[0]["valor"] == 1
    assert all(f["dimension"] == "homicidio" for f in filas)


def test_homicidios_extraer_une_anios_y_guarda_metadatos(monkeypatch):
    class _RespExcel:
        def __init__(self, contenido):
            self._c = contenido
            self.status_code = 200

        def raise_for_status(self):
            pass

        @property
        def content(self):
            return self._c

    def fake_get(url, timeout=120):
        return _RespExcel(_excel_homicidios_bytes().getvalue())

    monkeypatch.setattr("etl.policia.pipeline.requests.get", fake_get)
    p = Policia_Homicidios()
    monkeypatch.setattr(p, "_urls_a_descargar", lambda: ["https://a.test/2025.xlsx"])
    df, lineage = p.extraer()
    assert df.iloc[0]["filas"] == 4
    assert "2025.xlsx" in df.iloc[0]["url"]
    assert lineage.fuente == "Policía Nacional"
