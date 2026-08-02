# HDX — Eventos de conflicto en Colombia (hdx-hapi-col)

> Fuente internacional (plan2.md Fase B, fuente 4). Dataset dedicado a
> Colombia de Humanitarian Data Exchange, verificado en vivo 2026-08-02.
> Se carga el recurso *Conflict Events* (346.698 filas mensuales por municipio).

| Campo | Valor |
|---|---|
| Entidad | Humanitarian Data Exchange (OCHA) |
| URL base | https://data.humdata.org/ |
| Método de acceso | API CKAN + descarga CSV (URL firmada vía `resource_show`) |
| Periodicidad | Mensual |
| Formato | CSV |
| Licencia | Verificar por dataset (sección 3, punto 5) |
| Variables | `HDX_BASE_URL`, `HDX_CONFLICTO_RESOURCE_ID` |
| Estado | Conector activo: `etl/internacional/hdx.py` |

## Qué se carga

| Indicador | Código | Unidad |
|---|---|---|
| Eventos de conflicto por municipio/año | `hdx_conflicto_eventos` | eventos |
| Fatalidades en eventos de conflicto por municipio/año | `hdx_conflicto_fatalidades` | fatalidades |

Fuente de los datos subyacentes: ACLED vía HDX HAPI (3 tipos de evento:
`civilian_targeting`, `demonstration`, `political_violence`). Cobertura
verificada: 1.121 municipios, años 2018–2026.

## Notas de gobernanza

- Los códigos `admin2_code` de HAPI ("CO76890") son DIVIPOLA con prefijo "CO":
  se descarta el prefijo y se resuelve contra el catálogo `curated.municipio`;
  las filas no resueltas se cuentan (patrón `insertar_serie`).
- Los eventos son mensuales y se agregan a serie anual en `curated`.
- Eventos de conflicto de fuentes internacionales (ACLED/HAPI) pueden diferir
  de los registros nacionales (Policía/CNMH): usar como capa de contexto.
- Las fichas ya existentes (`internacional.md`) documentan el resto de
  fuentes internacionales.
