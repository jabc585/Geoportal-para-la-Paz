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

export interface PdetProyectos {
  proyectos: number;
  municipios: number;
}

const BASE = "/api/v1";

// Nunca hardcodear http://localhost:8000: en dev el proxy de Vite sirve /docs
// desde la API; en producción se resuelve tras el mismo reverse proxy o se
// define VITE_DOCS_URL.
export const DOCS_URL: string = import.meta.env.VITE_DOCS_URL ?? "/docs";

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

export function obtenerMapa(indicador: string, anio?: number): Promise<MapaIndicador> {
  const params = anio ? `?anio=${anio}` : "";
  return obtener<MapaIndicador>(`/mapas/${indicador}${params}`);
}

export function obtenerProyectosPdet(): Promise<PdetProyectos> {
  return obtener<PdetProyectos>("/pdet/proyectos");
}

export function urlExportarCSV(indicador: string, territorio?: string): string {
  const params = territorio ? `?territorio=${territorio}` : "";
  return `${BASE}/indicadores/${indicador}/exportar.csv${params}`;
}

export async function healthcheck(): Promise<boolean> {
  try {
    const resp = await fetch(`${BASE}/health`);
    return resp.ok;
  } catch {
    return false;
  }
}
