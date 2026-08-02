"""Estado de configuración de fuentes para el healthcheck (plan2.md, Fase A punto 10).

Solo lectura: reporta por fuente si su variable está configurada y la fecha del
último data_quality_metrics exitoso. No modifica los endpoints existentes.
"""

from __future__ import annotations

from psycopg.rows import dict_row

from etl.common.config import FUENTES_ACTIVAS, settings
from etl.common.db import conectar

# Variable de fuente → pipeline_id que la consume (para data_quality_metrics).
_PIPELINE_POR_VARIABLE = {
    "DANE_POBLACION_XLSX_URL": "dane_poblacion",
    "VICTIMAS_URL": "victimas_hechos",
    "PDET_URL": "art_pdet",
    "WB_INDICADORES": "internacional_worldbank",
    "UNHCR_BASE_URL": "internacional_unhcr",
    "HDX_CONFLICTO_RESOURCE_ID": "internacional_hdx",
    "CNMH_MINAS_URL": "cnmh_minas",
    "CNMH_ATENTADOS_URL": "cnmh_atentados",
    "CNMH_DESAPARICION_URL": "cnmh_desaparicion",
    "CNMH_RECLUTAMIENTO_URL": "cnmh_reclutamiento",
    "CNMH_BIENES_URL": "cnmh_bienes",
    "CNMH_ACCIONES_URL": "cnmh_acciones",
    "FISCALIA_PROCESOS_URL": "fiscalia_procesos",
    "FISCALIA_VICTIMAS_URL": "fiscalia_victimas",
    "POLICIA_HURTO_URL": "policia_hurto",
    "POLICIA_VIOLENCIA_URL": "policia_violencia",
    "POLICIA_SEXUALES_URL": "policia_sexuales",
    "DIVIPOLA_DEPT_DATASET": "divipola",
    "DIVIPOLA_MUN_DATASET": "divipola",
    "UCDP_API_TOKEN": "internacional_ucdp",
    "ACLED_EMAIL": "internacional_acled",
    "ACLED_KEY": "internacional_acled",
    "ACLED_DATA_DIR": "internacional_acled",
    "IDEAM_BOSQUE_URL": "ideam_ambiental",
}


def estado_fuentes() -> list[dict]:
    """Por fuente: variable configurada + último pipeline exitoso en la BD."""
    ultimos = {}
    try:
        with conectar() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT pipeline_id, MAX(timestamp_ejecucion) AS ultima_corrida
                FROM curated.data_quality_metrics
                WHERE estado = 'exitoso'
                GROUP BY pipeline_id
                """
            )
            ultimos = {fila["pipeline_id"]: fila["ultima_corrida"] for fila in cur.fetchall()}
    except Exception:  # noqa: BLE001 — la BD puede no estar arriba: se reporta sin ultima_corrida
        pass
    resultado = []
    for variable, fuente, ayuda in FUENTES_ACTIVAS:
        pipeline_id = _PIPELINE_POR_VARIABLE.get(variable)
        resultado.append(
            {
                "variable": variable,
                "fuente": fuente,
                "configurada": bool(getattr(settings, variable.lower(), None)),
                "ayuda": ayuda,
                "ultima_corrida_exitosa": ultimos.get(pipeline_id) if pipeline_id else None,
            }
        )
    return resultado
