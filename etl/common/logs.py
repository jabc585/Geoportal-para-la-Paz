"""Logging estructurado para ETL y API (plan3.md, Fase 4.19).

Reemplaza los ``print()`` dispersos (33 ocurrencias en etl/, confirmado por
auditoría) con un logger JSON con ``run_id`` de correlación para ETL y
``request_id`` para la API.
"""

from __future__ import annotations

import json
import logging
import sys
import uuid
from datetime import UTC, datetime


class _JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname.lower(),
            "message": record.getMessage(),
            "module": record.name,
        }
        if hasattr(record, "run_id"):
            payload["run_id"] = record.run_id
        if hasattr(record, "request_id"):
            payload["request_id"] = record.request_id
        if record.exc_info and record.exc_info[1] is not None:
            payload["error"] = str(record.exc_info[1])
        return json.dumps(payload, ensure_ascii=False)


def _setup_logger(nombre: str) -> logging.Logger:
    logger = logging.getLogger(nombre)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def obtener_logger_etl(nombre: str) -> logging.Logger:
    """Logger con ``run_id`` fijo para toda la corrida de un pipeline."""
    logger = _setup_logger(f"etl.{nombre}")
    run_id = getattr(logger, "_run_id", None) or str(uuid.uuid4())[:8]
    logger._run_id = run_id
    logger = logging.LoggerAdapter(logger, {"run_id": run_id})  # type: ignore[arg-type]
    return logger  # type: ignore[return-value]


log = _setup_logger("observatorio")
