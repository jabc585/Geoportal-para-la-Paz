"""Ejecuta los pipelines activos (sección 21, pasos 4 y 11).

Pipelines reales: DANE, Víctimas, PDET, World Bank, UNHCR, CNMH SIEVCAC (uno
por tipo de hecho), HDX Conflict Events y Policía (por delito). Los esqueletos
pendientes (IDEAM, Defensoría, UCDP, ACLED, Fiscalía por volumen) se agregan a
medida que se confirme su viabilidad (ver config/investigacion_fuentes.yaml).
"""

from __future__ import annotations

from functools import partial

from etl.dane.pipeline import DANE_Poblacion
from etl.ideam.pipeline import IDEAM_Ambiental
from etl.internacional.acled import Internacional_ACLED
from etl.internacional.hdx import Internacional_HDX
from etl.internacional.unhcr import Internacional_UNHCR
from etl.internacional.world_bank import Internacional_WorldBank
from etl.memoria.pipeline import CNMH_Memoria, HECHOS
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
    fallidos = []
    for construir in PIPELINES:
        try:
            pipeline = construir()
            pipeline.ejecutar()
            print(f"[OK] {pipeline.pipeline_id}")
        except Exception as exc:  # noqa: BLE001
            pipeline_id = getattr(construir, "pipeline_id", None)
            print(f"[FALLO] {pipeline_id or construir}: {exc}")
            fallidos.append(str(pipeline_id or construir))
    if fallidos:
        raise SystemExit(f"Pipelines fallidos: {fallidos}")


if __name__ == "__main__":
    run_all()
