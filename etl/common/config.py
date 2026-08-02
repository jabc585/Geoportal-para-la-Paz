"""Configuración centralizada de fuentes (plan2.md, Fase A).

Carga automática de `.env` (python-dotenv vía pydantic-settings) con una clase
Settings tipada. Todos los campos de fuente son *opcionales* a nivel de
Settings: la obligatoriedad se valida en el punto de uso (extraer()), igual
que antes, para no acoplar el arranque de la API o de un pipeline a variables
que no usa (revisión de la propuesta ronda 2, punto 1).

Los 4 pipelines reales (DANE, Víctimas, PDET, World Bank) NO leen de aquí:
siguen usando os.getenv() con su lógica ya probada, por eso los valores del
.env se inyectan al entorno (ver _inyectar_al_entorno). `settings`/
`get_source_url()` son para los pipelines nuevos (Fase B).
"""

from __future__ import annotations

import os
import sys

from pydantic_settings import BaseSettings, SettingsConfigDict

# Variables de fuente que un pipeline real/skeleton necesita para funcionar.
# Se usan solo en el comando opt-in `--check`; nada falla al importar.
FUENTES_ACTIVAS = [
    ("DANE_POBLACION_XLSX_URL", "DANE", "Excel oficial de proyecciones de población"),
    ("VICTIMAS_URL", "Víctimas", "API de Datos Paz"),
    ("PDET_URL", "PDET", "Dataset Socrata de proyectos PDET"),
    ("WB_INDICADORES", "Banco Mundial", "Lista codigo:nombre de indicadores"),
    ("UNHCR_BASE_URL", "UNHCR", "API pública de población"),
    ("HDX_BASE_URL", "HDX", "API CKAN de Humanitarian Data Exchange"),
    ("HDX_CONFLICTO_RESOURCE_ID", "HDX", "Resource id de Conflict Events Colombia (hdx-hapi-col)"),
    ("CNMH_MINAS_URL", "CNMH", "Dataset SIEVCAC de minas antipersonal"),
    ("CNMH_ATENTADOS_URL", "CNMH", "Dataset SIEVCAC de atentados terroristas"),
    ("CNMH_DESAPARICION_URL", "CNMH", "Dataset SIEVCAC de desaparición forzada"),
    ("CNMH_RECLUTAMIENTO_URL", "CNMH", "Dataset SIEVCAC de reclutamiento NNA"),
    ("CNMH_BIENES_URL", "CNMH", "Dataset SIEVCAC de daño a bienes civiles"),
    ("CNMH_ACCIONES_URL", "CNMH", "Dataset SIEVCAC de acciones bélicas"),
    ("FISCALIA_PROCESOS_URL", "Fiscalía", "Dataset Socrata de procesos V3"),
    ("FISCALIA_VICTIMAS_URL", "Fiscalía", "Dataset Socrata de víctimas V3"),
    ("POLICIA_HURTO_URL", "Policía", "Dataset Socrata de hurto"),
    ("POLICIA_VIOLENCIA_URL", "Policía", "Dataset Socrata de violencia intrafamiliar"),
    ("POLICIA_SEXUALES_URL", "Policía", "Dataset Socrata de delitos sexuales"),
    ("POLICIA_HOMICIDIOS_URL", "Policía", "Dataset Socrata de homicidios (pendiente de localizar)"),
    ("DIVIPOLA_DEPT_DATASET", "DIVIPOLA", "Dataset Socrata de departamentos (default vcjz-niiq)"),
    ("DIVIPOLA_MUN_DATASET", "DIVIPOLA", "Dataset Socrata de municipios (default gdxc-w37w)"),
    ("UCDP_API_TOKEN", "UCDP", "Token de la API UCDP (registro previo)"),
    ("ACLED_EMAIL", "ACLED", "Email de registro de ACLED"),
    ("ACLED_KEY", "ACLED", "Key de registro de ACLED"),
    ("ACLED_DATA_DIR", "ACLED", "Directorio de los agregados XLSX (default data/external)"),
    ("IDEAM_BOSQUE_URL", "IDEAM", "ZIP del raster de deforestación (opcional: se resuelve por redirección pública)"),
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Todas las URLs de fuente son *opcionales* a nivel de Settings: la
    # obligatoriedad se valida en el punto de uso (extraer()), igual que hoy.
    database_url: str = "postgresql://observatorio:observatorio_dev@localhost:5432/observatorio"

    dane_poblacion_xlsx_url: str | None = None
    # Sin default "1" ni similar: None preserva el comportamiento real ya
    # probado (sheet_name=hoja or 0 → primera hoja). Un default no-None aquí
    # rompería el Excel real de DANE (ver revisión ronda 2, punto 1).
    dane_poblacion_hoja: str | None = None
    dane_poblacion_dataset: str | None = None  # legacy, eliminado del pipeline
    victimas_url: str | None = None
    pdet_url: str | None = None
    divipola_dept_dataset: str = "vcjz-niiq"
    divipola_mun_dataset: str = "gdxc-w37w"
    wb_indicadores: str = "NY.GDP.PCAP.PP.CD:PIB per cápita (PPA)"

    # Campos nuevos, solo para pipelines de Fase B (hoy esqueletos, sin
    # lógica que romper):
    unhcr_base_url: str = "https://api.unhcr.org/population/v1"
    hdx_base_url: str = "https://data.humdata.org/api/3"
    policia_hurto_url: str | None = None
    policia_violencia_url: str | None = None
    policia_sexuales_url: str | None = None
    policia_homicidios_url: str | None = None  # pendiente de localizar dataset
    fiscalia_procesos_url: str | None = None
    fiscalia_victimas_url: str | None = None
    cnmh_minas_url: str | None = None
    cnmh_atentados_url: str | None = None
    cnmh_desaparicion_url: str | None = None
    cnmh_reclutamiento_url: str | None = None
    cnmh_bienes_url: str | None = None
    cnmh_acciones_url: str | None = None

    # IDEAM: raster de deforestación (39dh-rc72, archivo .img en ZIP). Si la
    # variable está vacía se resuelve la redirección pública de /download/39dh-rc72.
    ideam_bosque_url: str | None = None

    # HDX: recurso CSV de Conflict Events (hdx-hapi-col) dentro del dataset
    # de Colombia; se resuelve la URL firmada vía resource_show.
    hdx_conflicto_resource_id: str | None = None

    socrata_app_token: str | None = None
    ucdp_api_token: str | None = None
    acled_email: str | None = None
    acled_key: str | None = None

    # ACLED: agregados país-año descargados a mano (data/external, 2026-08-02);
    # el pipeline es de archivos locales y no requiere API key.
    acled_data_dir: str = "data/external"


settings = Settings()


def _inyectar_al_entorno() -> None:
    """Puente para los 4 pipelines legacy (DANE, Víctimas, PDET, World Bank):
    siguen leyendo os.getenv() por diseño (plan2.md Fase A), así que los
    valores del .env se exponen en el entorno solo si no están ya definidos
    (las variables exportadas en el shell tienen prioridad). Los valores
    vacíos del .env NO se inyectan: un `VAR=` vacío significa "no
    configurado", igual que una variable ausente."""
    for nombre, valor in settings.model_dump().items():
        if valor is None or (isinstance(valor, str) and not valor.strip()):
            continue
        variable = nombre.upper()
        if variable not in os.environ:
            os.environ[variable] = str(valor)


_inyectar_al_entorno()


def get_source_url(nombre_variable: str, *, ayuda: str = "") -> str:
    """Para pipelines nuevos (Fase B): valida en el punto de uso, no al importar."""
    val = getattr(settings, nombre_variable.lower(), None) or ""
    if not val:
        raise ValueError(f"Variable de entorno {nombre_variable} no definida. {ayuda}")
    return val


def _check() -> int:
    """Comando opt-in (plan2.md, Fase A punto 8): reporta qué variables de
    fuentes activas faltan, sin abortar nada por sí solo."""
    ausentes = [(var, fuente, ayuda) for var, fuente, ayuda in FUENTES_ACTIVAS if not getattr(settings, var.lower(), None)]
    if ausentes:
        print(f"[config] {len(ausentes)} variables de fuente sin configurar:")
        for var, fuente, ayuda in ausentes:
            print(f"  - {var} ({fuente}): {ayuda}")
        return 1
    print("[config] todas las variables de fuente configuradas.")
    return 0


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(_check())
    print(settings.model_dump())
