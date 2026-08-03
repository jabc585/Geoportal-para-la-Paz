"""Ejecuta los 18 pipelines activos (sección 21, pasos 4 y 11).

Activos: DANE, Víctimas, PDET, World Bank, UNHCR, CNMH SIEVCAC (6 hechos),
HDX Conflict Events, Policía (hurto, violencia, sexuales, homicidios),
ACLED, IDEAM y Fiscalía. Pendientes (no en PIPELINES): Defensoría, UCDP
(ver config/investigacion_fuentes.yaml).
"""

from __future__ import annotations

from functools import partial

from etl.common.logs import obtener_logger_etl
from etl.dane.pipeline import DANE_Poblacion
from etl.ideam.pipeline import IDEAM_Ambiental
from etl.internacional.acled import Internacional_ACLED
from etl.internacional.hdx import Internacional_HDX
from etl.internacional.unhcr import Internacional_UNHCR
from etl.internacional.world_bank import Internacional_WorldBank
from etl.memoria.pipeline import HECHOS, CNMH_Memoria
from etl.pdet.pipeline import ART_PDET
from etl.policia.pipeline import DELITOS, Policia_Delitos, Policia_Homicidios
from etl.victimas.pipeline import Victimas_Hechos

# Cada entrada es un callable sin argumentos que devuelve un PipelineETL
# (las clases directas o functools.partial para pipelines parametrizados).
PIPELINES = [
    DANE_Poblacion,
    Victimas_Hechos,
    ART_PDET,
    Internacional_WorldBank,
    Internacional_UNHCR,
    Internacional_HDX,
    Internacional_ACLED,
    *[partial(CNMH_Memoria, hecho) for hecho in HECHOS],
    *[partial(Policia_Delitos, delito) for delito in DELITOS],
    Policia_Homicidios,
    IDEAM_Ambiental,
]


def run_all() -> None:
    log = obtener_logger_etl("run_all")
    fallidos = []
    for construir in PIPELINES:
        try:
            pipeline = construir()
            pipeline.ejecutar()
            log.info("[OK] %s", pipeline.pipeline_id)
        except Exception as exc:
            pipeline_id = getattr(construir, "pipeline_id", None)
            log.error("[FALLO] %s: %s", pipeline_id or construir, exc)
            fallidos.append(str(pipeline_id or construir))

    # F5.3 (plan.md): presupuesto de duración — avisar si algún pipeline
    # tardó >2× su mediana histórica (degradación de fuentes externas).
    _presupuesto_duracion()

    if fallidos:
        raise SystemExit(f"Pipelines fallidos: {fallidos}")


def _presupuesto_duracion() -> None:
    try:
        from psycopg.rows import dict_row

        from etl.common.db import conectar
        with conectar(autocommit=True) as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT pipeline_id,
                       percentile_cont(0.5) WITHIN GROUP (ORDER BY duracion_segundos) AS mediana
                FROM curated.data_quality_metrics
                WHERE estado = 'exitoso'
                GROUP BY pipeline_id
                """
            )
            medianas = {f["pipeline_id"]: f["mediana"] for f in cur.fetchall()}
            cur.execute(
                """
                SELECT pipeline_id, duracion_segundos
                FROM curated.data_quality_metrics
                WHERE (pipeline_id, timestamp_ejecucion) IN (
                    SELECT pipeline_id, MAX(timestamp_ejecucion)
                    FROM curated.data_quality_metrics GROUP BY pipeline_id
                )
                """
            )
            for fila in cur.fetchall():
                mediana = medianas.get(fila["pipeline_id"])
                if mediana and fila["duracion_segundos"] > 2 * mediana:
                    print(
                        f"[AVISO] {fila['pipeline_id']}: {fila['duracion_segundos']:.0f}s "
                        f"(mediana histórica {mediana:.0f}s, >2×)"
                    )
    except Exception:
        pass  # métricas no disponibles (BD caída, sin histórico): sin aviso


if __name__ == "__main__":
    run_all()
