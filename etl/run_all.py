"""Ejecuta los pipelines activos (sección 21, pasos 4 y 11).

Los conectores de la fase piloto (DANE, Víctimas, PDET) y el internacional
World Bank se ejecutan en orden. Los esqueletos pendientes (Fiscalía,
Policía, IDEAM, memoria) se agregan a medida que se confirme su endpoint.
"""

from __future__ import annotations

from etl.dane.pipeline import DANE_Poblacion
from etl.internacional.world_bank import Internacional_WorldBank
from etl.pdet.pipeline import ART_PDET
from etl.victimas.pipeline import Victimas_Hechos

PIPELINES = [
    DANE_Poblacion,
    Victimas_Hechos,
    ART_PDET,
    Internacional_WorldBank,
]


def run_all() -> None:
    fallidos = []
    for pipeline in PIPELINES:
        try:
            pipeline().ejecutar()
            print(f"[OK] {pipeline.pipeline_id}")
        except Exception as exc:  # noqa: BLE001
            print(f"[FALLO] {pipeline.pipeline_id}: {exc}")
            fallidos.append(pipeline.pipeline_id)
    if fallidos:
        raise SystemExit(f"Pipelines fallidos: {fallidos}")


if __name__ == "__main__":
    run_all()
