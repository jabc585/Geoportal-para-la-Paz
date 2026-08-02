"""Conector internacional: ACLED (agregados país-año y departamento-año).

ACLED exige registro para la API; en su lugar se descargan los agregados
oficiales (export XLSX de acleddata.com) a data/external/ y se leen con pandas.
Cobertura verificada 2026-08-02: Colombia, años 1997-2026 (filas 2018-2026 con
datos completos). Los agregados país-año se cargan en
curated.indicador_internacional, igual que World Bank y UNHCR (sección 7.6);
el agregado semanal por admin1 se convierte a departamento-año (mapeo
ADMIN1 → DIVIPOLA) y se carga en curated.serie_historica.

Archivos usados (variables por archivo en etl/common/config.py):
- number_of_political_violence_events_by_country-year_as-of-24Jul2026.xlsx
- number_of_demonstration_events_by_country-year_as-of-24Jul2026.xlsx
- number_of_events_targeting_civilians_by_country-year_as-of-24Jul2026.xlsx
- Latin-America-the-Caribbean_aggregated_data_up_to_week_of-2026-07-18.xlsx
  (opcional: si existe en el directorio se procesa la capa por departamento)
"""

from __future__ import annotations

import unicodedata
from pathlib import Path

import pandas as pd

from etl.common.config import settings
from etl.common.db import transaccion
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

# Agregado semanal por admin1 (opcional): habilita la capa departamental.
ARCHIVO_ADMIN1 = "Latin-America-the-Caribbean_aggregated_data_up_to_week_of-2026-07-18.xlsx"

INDICADORES_DEPARTAMENTO = {
    "EVENTS": ("acled_eventos_departamento", "Eventos (ACLED) por departamento", "eventos"),
    "FATALITIES": ("acled_fatalidades_departamento", "Fatalidades (ACLED) por departamento", "fatalidades"),
}

NOMBRE_ARCHIVOS = ", ".join(ARCHIVOS)


def _normalizar(texto: str) -> str:
    """Sin tildes, minúsculas, no alfanumérico → '_' (para emparejar nombres)."""
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    import re

    return re.sub(r"[^a-z0-9]+", "_", texto.lower()).strip("_")


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

    def _mapeo_admin1(self) -> dict[str, str]:
        """nombre normalizado de departamento → código DIVIPOLA (2 dígitos)."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT codigo_divipola, nombre FROM curated.departamento")
            filas = cur.fetchall()
        return {_normalizar(nombre): codigo for codigo, nombre in filas}

    def extraer(self) -> tuple[pd.DataFrame, Lineage]:
        rutas = self._rutas()
        filas = []
        for ruta, indicador, unidad in rutas:
            df = pd.read_excel(ruta)
            df["indicador"] = indicador
            df["unidad"] = unidad
            df["archivo"] = ruta.name
            filas.append(df)
        ruta_admin1 = self._directorio() / ARCHIVO_ADMIN1
        if ruta_admin1.exists():
            df = pd.read_excel(ruta_admin1)
            # solo Colombia: el resto de la región no se duplica en raw
            df = df[df["COUNTRY"].astype(str).str.upper() == PAIS.upper()]
            df["WEEK"] = df["WEEK"].astype(str)  # Timestamp → texto (raw JSON)
            df["archivo"] = ruta_admin1.name
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
        es_colombia = df["COUNTRY"].astype(str).str.upper() == PAIS.upper()
        out_pais = df.loc[es_colombia & (df["archivo"] != ARCHIVO_ADMIN1), ["YEAR", "EVENTS", "indicador", "unidad"]].copy()
        out_pais = out_pais.rename(columns={"YEAR": "anio", "EVENTS": "valor"})
        out_pais["anio"] = pd.to_numeric(out_pais["anio"], errors="coerce")
        out_pais["valor"] = pd.to_numeric(out_pais["valor"], errors="coerce")
        out_pais = out_pais.dropna(subset=["anio", "valor"])
        return out_pais

    def transformar_admin1(self, df: pd.DataFrame) -> pd.DataFrame:
        """Capa departamental: admin1 semanal → departamento-año (EVENTS y FATALITIES)."""
        admin1 = df[df["archivo"] == ARCHIVO_ADMIN1]
        if admin1.empty:
            return pd.DataFrame()
        admin1 = admin1[admin1["COUNTRY"].astype(str).str.upper() == PAIS.upper()]
        mapeo = self._mapeo_admin1()
        admin1 = admin1.assign(
            codigo_divipola=admin1["ADMIN1"].astype(str).map(_normalizar).map(mapeo)
        )
        sin_mapear = admin1["codigo_divipola"].isna().sum()
        if sin_mapear:
            print(f"[acled] AVISO: {sin_mapear} filas admin1 sin mapeo DIVIPOLA")
        admin1 = admin1.dropna(subset=["codigo_divipola"]).copy()
        if admin1.empty:
            return admin1
        anio = pd.to_datetime(admin1["WEEK"], errors="coerce").dt.year
        admin1["anio"] = pd.to_numeric(anio, errors="coerce")
        salidas = []
        for columna in ("EVENTS", "FATALITIES"):
            codigo_ind, nombre_ind, unidad = INDICADORES_DEPARTAMENTO[columna]
            parcial = pd.DataFrame(
                {
                    "codigo_divipola": admin1["codigo_divipola"],
                    "anio": admin1["anio"],
                    "indicador_codigo": codigo_ind,
                    "indicador_nombre": nombre_ind,
                    "unidad": unidad,
                    "valor": pd.to_numeric(admin1[columna], errors="coerce"),
                }
            ).dropna(subset=["anio", "valor"])
            if parcial.empty:
                continue
            parcial = parcial.groupby(
                ["codigo_divipola", "anio", "indicador_codigo", "indicador_nombre", "unidad"],
                as_index=False,
            )["valor"].sum()
            salidas.append(parcial)
        if not salidas:
            return pd.DataFrame()
        return pd.concat(salidas, ignore_index=True)

    def cargar_curated(self, df: pd.DataFrame) -> None:
        if df.empty:
            return
        with transaccion(self.conn):
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

    def cargar_curated_admin1(self, df: pd.DataFrame) -> None:
        """Capa departamental: departamento-año → curated.serie_historica."""
        if df.empty:
            return
        from datetime import date  # noqa: F401 — usado por periodo_anual

        from etl.common.cargar import insertar_serie, periodo_anual, upsert_indicador
        from etl.common.validation import EsquemaSerieNormalizada, validar

        with transaccion(self.conn):
            fuente_id = self._fuente_id()
            for codigo_ind, grupo in df.groupby("indicador_codigo"):
                indicador_id = upsert_indicador(
                    self.conn,
                    codigo=codigo_ind,
                    nombre=grupo.iloc[0]["indicador_nombre"],
                    descripcion="Eventos/fatalidades de conflicto por departamento/año (ACLED, agregado semanal admin1)",
                    unidad=grupo.iloc[0]["unidad"],
                    granularidad_min="departamento",
                    periodicidad="anual",
                )
                periodo = grupo["anio"].apply(periodo_anual)
                a_cargar = grupo.assign(
                    indicador_id=indicador_id,
                    periodo_inicio=periodo.apply(lambda p: p[0]),
                    periodo_fin=periodo.apply(lambda p: p[1]),
                )
                a_cargar = validar(a_cargar, EsquemaSerieNormalizada)[0]
                insertadas = insertar_serie(
                    self.conn, a_cargar, fuente_id, self.lineage.url_origen, self.lineage.fecha_extraccion
                )
                print(f"[acled] departamento-año cargados a serie_historica ({codigo_ind}): {insertadas}")

    def ejecutar(self) -> None:
        # Capa país-año (igual que el base) y luego la capa departamental opcional.
        super().ejecutar()
        try:
            df_crudo = None
            if (self._directorio() / ARCHIVO_ADMIN1).exists():
                df_crudo, _ = self.extraer()
            if df_crudo is not None:
                admin1 = self.transformar_admin1(df_crudo)
                self.cargar_curated_admin1(admin1)
        except Exception as exc:  # noqa: BLE001
            print(f"[acled] AVISO: capa departamental falló ({exc}) — no afecta los país-año")

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
