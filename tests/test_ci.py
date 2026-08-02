"""CI estático (auditoría 2026-08-02, hallazgo 1): las migraciones montadas en
docker-compose.yml deben coincidir con database/migrations/ exactamente.

La desincronización histórica (montaban 0001-0008 y existían 0001-0011) rompía
el arranque en contenedor; este test falla si vuelve a pasar.
"""

from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[1]
MIGRACIONES = RAIZ / "database" / "migrations"
COMPOSE = RAIZ / "docker" / "docker-compose.yml"


def test_migraciones_montadas_coinciden_con_directorio():
    archivos_en_disco = sorted(p.name for p in MIGRACIONES.glob("*.sql"))
    with COMPOSE.open() as f:
        compose = yaml.safe_load(f)
    montadas = sorted(
        linea.split(":")[0].rsplit("/", 1)[-1]
        for servicio in compose["services"].values()
        for linea in servicio.get("volumes", [])
        if "migrations/" in linea
    )
    assert montadas == archivos_en_disco, (
        "docker-compose.yml está desincronizado con database/migrations/. "
        f"En disco: {archivos_en_disco}; montadas: {montadas}"
    )


def test_migraciones_ordenadas_y_renumeradas():
    nombres = sorted(p.name for p in MIGRACIONES.glob("*.sql"))
    for i, nombre in enumerate(nombres, start=1):
        assert nombre.startswith(f"{i:04d}_"), (
            f"Migración fuera de secuencia: {nombre} debería ser {i:04d}_..."
        )
