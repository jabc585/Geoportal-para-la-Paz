"""Conector internacional: ACLED (agregados país-año, archivos locales).

ACLED exige registro para la API; en su lugar se descargan los agregados
oficiales (export XLSX de acleddata.com) a data/external/ y se leen con pandas.
Cobertura verificada 2026-08-02: Colombia, años 1997-2026 (filas 2018-2026 con
datos completos). Se cargan en curated.indicador_internacional, igual que
World Bank y UNHCR (sección 7.6): a nivel país, separadas de la serie municipal.

Archivos usados (variables por archivo en etl/common/config.py):
- number_of_political_violence_events_by_country-year_as-of-24Jul2026.xlsx
- number_of_demonstration_events_by_country-year_as-of-24Jul2026.xlsx
- number_of_events_targeting_civilians_by_country-year_as-of-24Jul2026.xlsx

El agregado semanal por admin1 (Latin-America-the-Caribbean_aggregated_data...)
queda en data/external para una futura capa por departamento (requiere mapeo
ADMIN1 → DIVIPOLA); no se carga todavía.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from etl.common.config import settings
from etl.common.lineage import Lineage, hash_registro
from etl.common.pipeline import PipelineETL

PAIS = "Colombia"

RUTA_REPO = Path(__file__).resolve().parents[2]

# archivo en data/external → (indicador, unidad)
ARCHIVOS = {
    "number_of_political_violence_events_by_country-year_as-of-24Jul2026.xlsx": (
        "Eventos de violencia política (ACLED)",
        "eventos",
    ),
    "number_of_demonstration_events_by_country-year_as-of-24Jul2026.xlsx": (
        "Eventos de demostración (ACLED)",
        "eventos",
    ),
    "number_of_events_targeting_civilians_by_country-year_as-of-24Jul2026.xlsx": (
        "Eventos dirigidos contra civiles (ACLED)",
        "eventos",
    ),
}

NOMBRE_ARCHIVOS = ", ".join(ARCHIVOS)


class Internacional_ACLED(PipelineETL):
    pipeline_id = "internacional_acled"
    tabla_raw = "internacional_acled"

    def _directorio(self) -> Path:
        directorio = Path(settings.acled_data_dir)
        if not directorio.is_absolute():
            directorio = RUTA_REPO / directorio
        return directorio

    def _rutas(self) -> list[tuple[Path, str, str]]:
        directorio = self._directorio()
        rutas = []
        for nombre, (indicador, unidad) in ARCHIVOS.items():
            ruta = directorio / nombre
            if not ruta.exists():
                raise FileNotFoundError(
                    f"Falta el archivo ACLED {ruta.name} (descargar de "
                    f"acleddata.com y guardar en {directorio})"
                )
            rutas.append((ruta, indicador, unidad))
        return rutas

    def extraer(self) -> tuple[pd.DataFrame, Lineage]:
        rutas = self._rutas()
        filas = []
        for ruta, indicador, unidad in rutas:
            df = pd.read_excel(ruta)
            df["indicador"] = indicador
            df["unidad"] = unidad
            df["archivo"] = ruta.name
            filas.append(df)
        df = pd.concat(filas, ignore_index=True)
        lineage = Lineage.ahora(
            fuente="ACLED",
            url_origen=str(rutas[0][0].parent),
            fecha_corte_dato="2026-07-24",
            licencia="ACLED Aggregated Data (uso con atribución)",
        )
        return df, lineage

    def transformar(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        # Solo las filas de Colombia; el resto del mundo queda en raw.
        es_colombia = df["COUNTRY"].astype(str).str.upper() == PAIS.upper()
        out = df.loc[es_colombia, ["YEAR", "EVENTS", "indicador", "unidad"]].copy()
        out = out.rename(columns={"YEAR": "anio", "EVENTS": "valor"})
        out["anio"] = pd.to_numeric(out["anio"], errors="coerce")
        out["valor"] = pd.to_numeric(out["valor"], errors="coerce")
        return out.dropna(subset=["anio", "valor"])

    def cargar_curated(self, df: pd.DataFrame) -> None:
        if df.empty:
            return
        with self.conn:
            fuente_id = self._fuente_id()
            insertadas = 0
            with self.conn.cursor() as cur:
                for fila in df.to_dict("records"):
                    cur.execute(
                        """
                        INSERT INTO curated.indicador_internacional
                            (fuente_id, pais, indicador, periodo, valor, unidad,
                             url_origen, fecha_extraccion, fecha_corte_dato, hash_registro)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (fuente_id, pais, indicador, periodo) DO NOTHING
                        """,
                        (
                            fuente_id,
                            PAIS,
                            fila["indicador"],
                            f"{int(fila['anio'])}-01-01",
                            float(fila["valor"]),
                            fila["unidad"],
                            self.lineage.url_origen,
                            self.lineage.fecha_extraccion,
                            self.lineage.fecha_corte_dato,
                            hash_registro(fila),
                        ),
                    )
                    insertadas += cur.rowcount > 0
            print(f"[acled] indicadores internacionales cargados: {insertadas}")

    def _fuente_id(self) -> int:
        from etl.common.cargar import upsert_fuente

        return upsert_fuente(
            self.conn,
            nombre="ACLED",
            entidad="Armed Conflict Location & Event Data",
            tipo="internacional",
            descripcion="Agregados país-año de eventos de violencia política, demostraciones y ataques contra civiles (sección 5.2)",
            url_base="https://acleddata.com/",
            metodo_acceso="descarga",
            periodicidad="semanal",
            formato="XLSX",
            licencia=self.lineage.licencia,
            ficha_doc="docs/fuentes/acled.md",
        )


if __name__ == "__main__":
    Internacional_ACLED().ejecutar()
