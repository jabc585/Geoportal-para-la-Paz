"""Instancia compartida de slowapi Limiter (Fase 0.3, plan3.md).

Un solo limiter para main.py y routes/v1.py evita que la instancia del router
quede sin conexión al middleware global.
"""

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[os.getenv("API_RATE_LIMIT", "120/minute")],
)
