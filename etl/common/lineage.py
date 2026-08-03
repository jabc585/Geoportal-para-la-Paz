"""Linaje de datos obligatorio (sección 3, punto 4 y sección 7).

Todo registro almacenado debe conservar: fuente, url_origen, fecha_extraccion,
fecha_corte_dato y licencia. El hash de registro detecta cambios/duplicados.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime


@dataclass(frozen=True)
class Lineage:
    fuente: str
    url_origen: str
    fecha_extraccion: datetime
    fecha_corte_dato: date | None
    licencia: str

    @classmethod
    def ahora(cls, fuente: str, url_origen: str, fecha_corte_dato: date | None, licencia: str) -> Lineage:
        return cls(
            fuente=fuente,
            url_origen=url_origen,
            fecha_extraccion=datetime.now(UTC),
            fecha_corte_dato=fecha_corte_dato,
            licencia=licencia,
        )


def hash_registro(datos: dict) -> str:
    """Hash determinista del contenido de una fila para detección de cambios/duplicados."""
    serializado = json.dumps(datos, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(serializado.encode("utf-8")).hexdigest()


def archivo_raw(descarga: bytes, fuente: str) -> bytes:
    """Marca de inmutabilidad: los datos crudos se almacenan tal como se descargan."""
    return descarga
