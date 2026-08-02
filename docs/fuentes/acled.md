# ACLED — Eventos de conflicto y protesta (agregados país-año)

> Fuente internacional (plan2.md Fase B, fuente 6). La API de ACLED requiere
> registro y licencia de uso; en su lugar se usan los **agregados oficiales**
> descargados a `data/external/` (export XLSX de acleddata.com, corte
> 2026-07-24, descarga 2026-08-02).

| Campo | Valor |
|---|---|
| Entidad | Armed Conflict Location & Event Data (ACLED) |
| URL base | https://acleddata.com/ |
| Método de acceso | Archivos locales (`data/external/`, sin API key) |
| Periodicidad | Semanal (archivos descargados a mano) |
| Formato | XLSX |
| Licencia | **Uso con atribución** — revisar términos de distribución antes de republicar los datos (sección 3, punto 5) |
| Variables | `ACLED_DATA_DIR` (default `data/external`) |
| Estado | Conector activo: `etl/internacional/acled.py` (a nivel país) |

## Qué se carga

| Indicador | Código | Unidad | Archivo |
|---|---|---|---|
| Eventos de violencia política | `acled_political_violence` | eventos | `number_of_political_violence_events_by_country-year_as-of-24Jul2026.xlsx` |
| Eventos de demostración | `acled_demonstration_events` | eventos | `number_of_demonstration_events_by_country-year_as-of-24Jul2026.xlsx` |
| Eventos dirigidos contra civiles | `acled_targeting_civilians` | eventos | `number_of_events_targeting_civilians_by_country-year_as-of-24Jul2026.xlsx` |

Solo se promueven a `curated.indicador_internacional` las filas de **Colombia**
(años con datos completos: 2018–2026; el archivo incluye 1997–2026, el resto
queda en `raw`).

## Pendiente / alternativas

- **Granularidad departamental**: `Latin-America-the-Caribbean_aggregated_data_up_to_week_of-2026-07-18.xlsx`
  trae agregados semanales por admin1 (EVENTS y FATALITIES) — requeriría mapear
  ADMIN1 a DIVIPOLA de departamento. No se carga todavía; el archivo queda en
  `data/external` para una futura capa (comparar siempre con registros
  nacionales: ACLED es de origen internacional).
- **HDX/HAPI**: expone ACLED con granularidad municipal (ver [hdx.md](hdx.md));
  para nivel país este conector local es suficiente y no depende de la API.

## Notas de gobernanza

- Atribución obligatoria: "ACLED (Armed Conflict Location & Event Data)" en el
  dashboard/descargas de datos derivados.
- La variable `ACLED_KEY` del `.env` queda documentada vacía: este conector no
  la necesita; si en el futuro se usa la API en vivo, revisar el límite de uso
  y la licencia por export.
