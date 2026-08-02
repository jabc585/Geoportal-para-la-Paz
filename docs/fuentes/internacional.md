# Fuentes internacionales de comparabilidad global

> Capa complementaria de fuentes abiertas internacionales (sección 5.2 del plan). Los indicadores de estas fuentes se modelan en `curated.indicador_internacional` a nivel **país**, nunca se mezclan visualmente con cifras municipales (secciones 5.2 y 7.6).

## Banco Mundial — World Bank Open Data (implementado)

| Campo | Valor |
|---|---|
| Entidad | World Bank |
| URL base | https://api.worldbank.org/v2/ |
| Método de acceso | API |
| Periodicidad | Anual |
| Formato | JSON |
| Licencia | Open Data (CC BY 4.0) |
| Estado | Conector activo: `etl/internacional/world_bank.py` |

Indicadores configurados con la variable `WB_INDICADORES` (lista `codigo:nombre`, comas):

```bash
export WB_INDICADORES="NY.GDP.PCAP.PP.CD:PIB per cápita (PPA),SI.POV.GINI:Índice de Gini"
```

## HDX (Humanitarian Data Exchange)

- URL: https://data.humdata.org/
- Estado: pendiente — documentar método de acceso y dataset específico de Colombia (desplazamiento, respuesta humanitaria).
- Licencia: verificar por dataset.

## UCDP (Uppsala Conflict Data Program)

- URL: https://ucdp.uu.se/
- Estado: pendiente — eventos georreferenciados; evaluar granularidad mínima contra checklist de privacidad (3.1).
- Licencia: abierta con atribución.

## ACNUR (UNHCR)

- URL: https://www.unhcr.org/refugee-statistics/
- Estado: pendiente.
- Licencia: abierta.

## ACLED

- URL: https://acleddata.com/
- Estado: pendiente — **licencia con condiciones de atribución**; revisar y documentar antes de integrar (sección 3, punto 5).

## IOM DTM

- URL: https://dtm.iom.int/
- Estado: pendiente.
