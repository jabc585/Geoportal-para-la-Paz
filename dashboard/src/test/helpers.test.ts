import { describe, expect, it } from "vitest";
import {
  agregarPorDepartamento,
  asignarColoresViridis,
  fmt,
  fmtCompact,
  fmtKPI,
} from "../app/utils";
import type { MapaIndicador } from "../api/client";

function mapa(
  features: { departamento: string; valor: number | null }[],
): MapaIndicador {
  return {
    indicador: "homicidios",
    nombre: "Homicidios",
    unidad: "casos",
    anio: 2025,
    type: "FeatureCollection",
    features: features.map((f, i) => ({
      type: "Feature",
      geometry: { type: "Polygon", coordinates: [] },
      properties: {
        codigo_divipola: String(5000 + i),
        municipio: `Municipio ${i}`,
        departamento: f.departamento,
        valor: f.valor,
      },
    })),
  };
}

describe("fmt", () => {
  it("formatea con separador de miles es-CO", () => {
    expect(fmt(13722)).toBe("13.722");
  });

  it("redondea decimales", () => {
    expect(fmt(2035.6)).toBe("2.036");
  });
});

describe("fmtCompact", () => {
  it("abrevia millones con coma decimal", () => {
    expect(fmtCompact(55990158)).toBe("56,0 M");
  });

  it("abrevia miles", () => {
    expect(fmtCompact(31120)).toBe("31 K");
  });

  it("deja los valores pequeños tal cual", () => {
    expect(fmtCompact(815)).toBe("815");
  });
});

describe("fmtKPI", () => {
  it("abrevia solo a partir del millón", () => {
    expect(fmtKPI(55990158)).toBe("56,0 M");
  });

  it("conserva la precisión por debajo del millón", () => {
    expect(fmtKPI(13722)).toBe("13.722");
    expect(fmtKPI(31120)).toBe("31.120");
  });
});

describe("agregarPorDepartamento", () => {
  it("suma los municipios de cada departamento y ordena descendente", () => {
    const resultado = agregarPorDepartamento(
      mapa([
        { departamento: "ANTIOQUIA", valor: 10 },
        { departamento: "ANTIOQUIA", valor: 5 },
        { departamento: "VALLE DEL CAUCA", valor: 20 },
      ]),
    );
    expect(resultado).toEqual([
      { nombre: "VALLE DEL CAUCA", valor: 20 },
      { nombre: "ANTIOQUIA", valor: 15 },
    ]);
  });

  it("ignora municipios sin dato en vez de contarlos como cero", () => {
    const resultado = agregarPorDepartamento(
      mapa([
        { departamento: "CHOCÓ", valor: null },
        { departamento: "CHOCÓ", valor: 7 },
      ]),
    );
    expect(resultado).toEqual([{ nombre: "CHOCÓ", valor: 7 }]);
  });

  it("devuelve lista vacía sin datos", () => {
    expect(agregarPorDepartamento(null)).toEqual([]);
  });
});

describe("asignarColoresViridis", () => {
  it("asigna el tono más oscuro al valor mayor", () => {
    const coloreados = asignarColoresViridis([
      { nombre: "A", valor: 1 },
      { nombre: "B", valor: 2 },
      { nombre: "C", valor: 3 },
      { nombre: "D", valor: 4 },
      { nombre: "E", valor: 5 },
    ]);
    expect(coloreados.find((c) => c.nombre === "E")?.color).toBe("#440154");
    expect(coloreados.find((c) => c.nombre === "A")?.color).toBe("#fde725");
  });

  it("no falla con un solo elemento", () => {
    expect(asignarColoresViridis([{ nombre: "Solo", valor: 1 }])).toHaveLength(1);
  });
});
