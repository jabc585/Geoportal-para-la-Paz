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
