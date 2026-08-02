"""Conector de comparabilidad internacional (sección 5.2).

La capa de comparabilidad global se compone de varios conectores; el patrón
es el mismo para todos: extracción a nivel país, carga en
curated.indicador_internacional (sección 7.6), nunca combinada con cifras
municipales en el dashboard (sección 5.2).
"""

from __future__ import annotations

from etl.internacional.world_bank import Internacional_WorldBank

__all__ = ["Internacional_WorldBank"]
