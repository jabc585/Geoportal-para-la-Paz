"""Ejecuta todos los pipelines de la fase piloto (sección 21, paso 4)."""

from __future__ import annotations

from etl.dane.pipeline import DANE_Poblacion
from etl.pdet.pipeline import ART_PDET
from etl.victimas.pipeline import Victimas_Hechos

PIPELINES = [
    DANE_Poblacion,
    Victimas_Hechos,
    ART_PDET,
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
