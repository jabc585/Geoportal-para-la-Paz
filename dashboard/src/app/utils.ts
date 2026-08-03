import type { MapaIndicador } from "../api/client";

export const VIRIDIS = ["#fde725", "#addc30", "#5ec962", "#21918c", "#440154"];

export function fmt(n: number): string {
  return new Intl.NumberFormat("es-CO").format(Math.round(n));
}

/** Compacto para ejes de gráficos, donde el espacio manda sobre la precisión. */
export function fmtCompact(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1).replace(".", ",")} M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)} K`;
  return String(Math.round(n));
}

/**
 * Cifra de KPI: los millones se abrevian (55,9 M se lee mejor que 55.990.158),
 * pero por debajo se muestra el número exacto — redondear 13.722 a "14 K" en
 * una tarjeta de homicidios perdería precisión que sí importa.
 */
export function fmtKPI(n: number): string {
  return n >= 1_000_000 ? fmtCompact(n) : fmt(n);
}

export interface FilaDepartamento {
  nombre: string;
  valor: number;
}

/**
 * Agrega el choropleth municipal por departamento (plandash2.md C3).
 * La API expone /mapas/{ind} a nivel municipio, pero cada feature ya trae
 * properties.departamento — así que el top-10 sale de la MISMA petición que
 * alimenta el mapa, sin llamadas extra ni cambios en el backend.
 *
 * Solo válido para indicadores de conteo (ver `agregable` en INDICADORES):
 * sumar una tasa o un porcentaje por departamento no significaría nada.
 */
export function agregarPorDepartamento(datos: MapaIndicador | null): FilaDepartamento[] {
  if (!datos) return [];
  const acumulado = new Map<string, number>();
  for (const f of datos.features) {
    const depto = f.properties.departamento;
    const valor = f.properties.valor;
    if (!depto || valor === null || valor === undefined) continue;
    acumulado.set(depto, (acumulado.get(depto) ?? 0) + valor);
  }
  return [...acumulado.entries()]
    .map(([nombre, valor]) => ({ nombre, valor }))
    .sort((a, b) => b.valor - a.valor);
}

export function asignarColoresViridis(
  data: FilaDepartamento[],
): (FilaDepartamento & { color: string })[] {
  const ordenados = [...data].sort((a, b) => a.valor - b.valor);
  const tamQuintil = Math.max(1, Math.ceil(ordenados.length / 5));
  return data.map((d) => {
    const rango = ordenados.findIndex((s) => s.nombre === d.nombre);
    const qi = Math.min(Math.floor(rango / tamQuintil), 4);
    return { ...d, color: VIRIDIS[qi] };
  });
}

/**
 * Elige el año que se muestra en un KPI: el más reciente **que ya ocurrió**.
 *
 * Sin esto, `totales[0]` daba el año máximo de la serie y la portada anunciaba
 * "Población · 2035 · 56,0 M" —una proyección del DANE a nueve años vista—
 * junto a "Homicidios · 2025", invitando a leer la primera como la cifra
 * actual. La población de 2026 son 53,5 M: la diferencia es de 2,5 millones
 * de personas que todavía no existen.
 *
 * Si toda la serie es futura se devuelve el año más cercano marcado como
 * proyección, en vez de ocultar el dato.
 */
export function totalVigente<T extends { anio: number }>(
  totales: T[] | undefined | null,
  anioActual: number = new Date().getFullYear(),
): { dato: T; proyeccion: boolean } | null {
  if (!totales || totales.length === 0) return null;
  const ordenados = [...totales].sort((a, b) => b.anio - a.anio);
  const ocurrido = ordenados.find((t) => t.anio <= anioActual);
  if (ocurrido) return { dato: ocurrido, proyeccion: false };
  return { dato: ordenados[ordenados.length - 1], proyeccion: true };
}
