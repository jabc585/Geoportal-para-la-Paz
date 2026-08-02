export interface Fuente {
  fuente_id: number;
  nombre: string;
  entidad: string;
  licencia: string;
  ultima_actualizacion: string | null;
  url_base: string | null;
}

export interface TotalAnual {
  anio: number;
  valor: number;
}

export interface IndicadorTotal {
  indicador: string;
  nombre: string;
  unidad: string;
  totales: TotalAnual[];
}

export interface MapaFeature {
  type: string;
  geometry: {
    type: string;
    coordinates: unknown[];
  };
  properties: {
    codigo_divipola: string;
    municipio: string;
    departamento: string;
    valor: number | null;
  };
}

export interface MapaIndicador {
  indicador: string;
  nombre: string;
  unidad: string;
  anio: number | null;
  type: string;
  features: MapaFeature[];
}

const BASE = "/api/v1";

async function obtener<T>(ruta: string): Promise<T> {
  const resp = await fetch(`${BASE}${ruta}`);
  if (!resp.ok) {
    throw new Error(`Error ${resp.status} en ${ruta}`);
  }
  return resp.json() as Promise<T>;
}

export function obtenerFuentes(): Promise<Fuente[]> {
  return obtener<Fuente[]>("/fuentes");
}

export function obtenerTotalIndicador(indicador: string): Promise<IndicadorTotal> {
  return obtener<IndicadorTotal>(`/indicadores/${indicador}/total`);
}

export function obtenerMapa(indicador: string): Promise<MapaIndicador> {
  return obtener<MapaIndicador>(`/mapas/${indicador}`);
}

export function descargarCSV(indicador: string): void {
  const url = `${BASE}/indicadores/${indicador}/exportar.csv`;
  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = `${indicador}.csv`;
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();
}
