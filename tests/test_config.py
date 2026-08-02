"""Pruebas de la configuración centralizada de fuentes (plan2.md, Fase A).

Sin red y sin BD: Settings se carga desde un .env temporal controlado
(tmp_path), no desde el .env real del desarrollador.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from etl.common import config as config_mod
from etl.common.config import FUENTES_ACTIVAS, get_source_url, settings

RAIZ = Path(__file__).resolve().parents[1]


def test_settings_sin_env_tiene_valores_por_defecto():
    for nombre in ("database_url", "dane_poblacion_hoja", "divipola_dept_dataset"):
        assert getattr(settings, nombre) is not None


def test_dane_poblacion_hoja_por_defecto_es_none():
    """Crítico: un default no-None rompería el Excel real de DANE (NaN fix)."""
    s = config_mod.Settings(_env_file=None)  # sin .env: solo el default de clase
    assert s.dane_poblacion_hoja is None


def test_divipola_tiene_defaults_socrata():
    assert settings.divipola_dept_dataset == "vcjz-niiq"
    assert settings.divipola_mun_dataset == "gdxc-w37w"


def test_get_source_url_devuelve_valor(tmp_path, monkeypatch):
    env_tmp = tmp_path / ".env"
    env_tmp.write_text("PDET_URL=https://example.test/datos.json\n")
    # _inyectar_al_entorno() deja PDET_URL en os.environ; el entorno real gana
    # sobre cualquier _env_file, así que se limpia para aislar el .env temporal.
    monkeypatch.delenv("PDET_URL", raising=False)
    s = config_mod.Settings(_env_file=env_tmp, _env_file_priority=1)
    monkeypatch.setattr(config_mod, "settings", s)
    assert get_source_url("PDET_URL") == "https://example.test/datos.json"


def test_get_source_url_lanza_si_falta(tmp_path, monkeypatch):
    env_tmp = tmp_path / ".env"
    env_tmp.write_text("")
    s = config_mod.Settings(_env_file=env_tmp)
    monkeypatch.setattr(config_mod, "settings", s)
    with pytest.raises(ValueError, match="VARIABLE_QUE_NO_EXISTE"):
        get_source_url("VARIABLE_QUE_NO_EXISTE", ayuda="ayuda de prueba")


def test_fuentes_activas_referencian_campos_reales():
    for variable, fuente, ayuda in FUENTES_ACTIVAS:
        campo = variable.lower()
        assert hasattr(settings, campo), f"{variable} no es campo de Settings"
        assert fuente and ayuda, f"entrada incompleta para {variable}"


def test_settings_carga_desde_env_temporal(tmp_path, monkeypatch):
    env_tmp = tmp_path / ".env"
    env_tmp.write_text("PDET_URL=https://example.test/datos.json\n")
    monkeypatch.delenv("PDET_URL", raising=False)
    s = config_mod.Settings(_env_file=env_tmp, _env_file_priority=1)
    assert s.pdet_url == "https://example.test/datos.json"


def test_fuentes_yaml_referencian_campos_reales():
    """Los valores de `variable` deben ser campos reales de Settings, salvo
    plantillas documentadas (p. ej. CNMH_<HECHO>_URL) o listas (X / Y)."""
    catalogo = yaml.safe_load((RAIZ / "config" / "fuentes.yaml").read_text())["fuentes"]
    assert catalogo, "catálogo vacío"
    for slug, meta in catalogo.items():
        assert meta.get("nombre") and meta.get("tipo"), f"fuente {slug} incompleta"
        variable = meta.get("variable")
        assert variable, f"fuente {slug} sin variable documentada"
        es_plantilla = any(marca in variable for marca in ("<", "/"))
        if not es_plantilla:
            assert hasattr(settings, variable.lower()), (
                f"{slug}: {variable} no es campo real de Settings"
            )


def test_investigacion_yaml_carga():
    invest = yaml.safe_load((RAIZ / "config" / "investigacion_fuentes.yaml").read_text())
    assert "fuentes" in invest
    for slug in ("policia", "fiscalia", "cnmh", "unhcr", "hdx"):
        assert slug in invest["fuentes"]


def test_check_cli_reporta_variables_ausentes(tmp_path):
    # _inyectar_al_entorno() deja las fuentes configuradas en os.environ; se
    # filtran para que el subproceso arranque limpio (cwd temporal sin .env).
    variables_fuente = {var.lower() for var, _, _ in FUENTES_ACTIVAS}
    env_limpio = {k: v for k, v in os.environ.items() if k.lower() not in variables_fuente}
    proc = subprocess.run(
        [sys.executable, "-m", "etl.common.config", "--check"],
        cwd=tmp_path,  # sin .env: Settings con defaults → variables ausentes
        env={**env_limpio, "PYTHONPATH": str(RAIZ)},
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1
    assert "sin configurar" in proc.stdout
    assert "PDET_URL" in proc.stdout
