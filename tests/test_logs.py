"""Tests del formateador JSON de logs (plan.md §F2.4)."""

from __future__ import annotations

import json
import logging

from etl.common.logs import _JSONFormatter, obtener_logger_etl


def test_formatter_produce_json_valido():
    fmt = _JSONFormatter()
    record = logging.LogRecord(
        name="etl.test", level=logging.INFO, pathname="x", lineno=1,
        msg="pipeline iniciado", args=(), exc_info=None,
    )
    payload = json.loads(fmt.format(record))
    assert payload["level"] == "info"
    assert payload["message"] == "pipeline iniciado"
    assert payload["module"] == "etl.test"
    assert "timestamp" in payload


def test_formatter_incluye_error_en_excepcion():
    import sys

    fmt = _JSONFormatter()
    try:
        raise ValueError("algo salió mal")
    except ValueError:
        exc_info = sys.exc_info()
    record = logging.LogRecord(
        name="etl.test", level=logging.ERROR, pathname="x", lineno=1,
        msg="fallo", args=(), exc_info=exc_info,
    )
    payload = json.loads(fmt.format(record))
    assert payload["level"] == "error"
    assert "algo salió mal" in payload["error"]


def test_formatter_sin_exc_info_no_incluye_error():
    fmt = _JSONFormatter()
    record = logging.LogRecord(
        name="etl.test", level=logging.WARNING, pathname="x", lineno=1,
        msg="aviso sin excepción", args=(), exc_info=None,
    )
    payload = json.loads(fmt.format(record))
    assert "error" not in payload


def test_obtener_logger_etl_tiene_run_id():
    logger = obtener_logger_etl("dane")
    assert hasattr(logger, "_run_id") or isinstance(logger, logging.LoggerAdapter)


def test_log_singleton_existe():
    from etl.common.logs import log
    assert isinstance(log, logging.Logger)
    assert log.name == "observatorio"
