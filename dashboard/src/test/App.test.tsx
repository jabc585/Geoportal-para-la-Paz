import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import App from "../app/App";

// MapLibre no funciona en jsdom (necesita WebGL): se sustituye por un doble.
vi.mock("maplibre-gl", () => {
  class MapaFalso {
    on() {}
    once() {}
    addControl() {}
    addSource() {}
    addLayer() {}
    getSource() {
      return undefined;
    }
    getLayer() {
      return undefined;
    }
    setPaintProperty() {}
    queryRenderedFeatures() {
      return [];
    }
    isStyleLoaded() {
      return false;
    }
    remove() {}
  }
  class PopupFalso {
    setLngLat() {
      return this;
    }
    setDOMContent() {
      return this;
    }
    addTo() {
      return this;
    }
    remove() {}
  }
  const modulo = {
    Map: MapaFalso,
    Popup: PopupFalso,
    NavigationControl: class {},
    ScaleControl: class {},
  };
  // `default` para `import maplibregl from ...` y los named por si acaso.
  return { default: modulo, ...modulo };
});
vi.mock("maplibre-gl/dist/maplibre-gl.css", () => ({}));

const FUENTES = [
  {
    fuente_id: 1,
    nombre: "Policía Nacional",
    entidad: "Policía Nacional",
    licencia: "Datos abiertos",
    ultima_actualizacion: "2026-08-03T10:00:00+00:00",
    url_base: "https://policia.gov.co",
  },
  {
    fuente_id: 2,
    nombre: "DANE",
    entidad: "DANE",
    licencia: "CC BY 4.0",
    ultima_actualizacion: null,
    url_base: null,
  },
];

function respuesta(cuerpo: unknown, ok = true) {
  return Promise.resolve({ ok, status: ok ? 200 : 503, json: () => Promise.resolve(cuerpo) });
}

function mockFetchOk() {
  return vi.fn((url: string) => {
    if (url.includes("/health")) return respuesta({ estado: "ok" });
    if (url.includes("/fuentes")) return respuesta(FUENTES);
    if (url.includes("/pdet/proyectos")) return respuesta({ proyectos: 31120, municipios: 170 });
    if (url.includes("/total")) {
      const totales: Record<string, { nombre: string; unidad: string; anio: number; valor: number }> = {
        homicidios: { nombre: "Homicidios", unidad: "casos", anio: 2025, valor: 13722 },
        victimas_ruv: { nombre: "Víctimas RUV", unidad: "personas", anio: 2026, valor: 9625248 },
        poblacion: { nombre: "Población", unidad: "personas", anio: 2035, valor: 55990158 },
      };
      const codigo = Object.keys(totales).find((c) => url.includes(c)) ?? "homicidios";
      const t = totales[codigo];
      return respuesta({
        indicador: codigo,
        nombre: t.nombre,
        unidad: t.unidad,
        totales: [{ anio: t.anio, valor: t.valor }],
      });
    }
    if (url.includes("/mapas/")) {
      return respuesta({
        indicador: "homicidios",
        nombre: "Homicidios",
        unidad: "casos",
        anio: 2025,
        type: "FeatureCollection",
        features: [
          {
            type: "Feature",
            geometry: { type: "Polygon", coordinates: [] },
            properties: {
              codigo_divipola: "05001",
              municipio: "MEDELLÍN",
              departamento: "ANTIOQUIA",
              valor: 500,
            },
          },
        ],
      });
    }
    return respuesta({}, false);
  });
}

beforeEach(() => {
  vi.stubGlobal("IntersectionObserver", class {
    observe() {}
    disconnect() {}
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("App conectada a la API", () => {
  it("muestra los KPIs con los datos reales de la API", async () => {
    vi.stubGlobal("fetch", mockFetchOk());
    render(<App />);
    // Fuentes: longitud del array devuelto, no un literal
    await waitFor(() => expect(screen.getByText("2")).toBeInTheDocument());
    // PDET formateado es-CO
    expect(await screen.findByText("31.120")).toBeInTheDocument();
    // Miles con precisión completa; millones abreviados
    expect(await screen.findByText("13.722")).toBeInTheDocument();
    expect(await screen.findByText("9,6 M")).toBeInTheDocument();
    expect(await screen.findByText("56,0 M")).toBeInTheDocument();
  });

  it("indica que la API está conectada solo cuando /health responde", async () => {
    vi.stubGlobal("fetch", mockFetchOk());
    render(<App />);
    expect(await screen.findByText("API conectada")).toBeInTheDocument();
  });

  it("no inventa cifras cuando la API falla", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.reject(new Error("sin red"))));
    render(<App />);
    // El aviso aparece tanto en el indicador de estado como en cada KPI.
    await waitFor(() =>
      expect(screen.getAllByText("API no disponible").length).toBeGreaterThan(1),
    );
    expect(screen.queryByText("31.120")).not.toBeInTheDocument();
    expect(screen.queryByText("13.722")).not.toBeInTheDocument();
  });

  it("genera la franja de fuentes desde la API", async () => {
    vi.stubGlobal("fetch", mockFetchOk());
    render(<App />);
    await waitFor(() => {
      expect(screen.getAllByText("Policía Nacional").length).toBeGreaterThan(0);
    });
  });

  it("lista las fuentes con su licencia en la tabla", async () => {
    vi.stubGlobal("fetch", mockFetchOk());
    render(<App />);
    expect(await screen.findByText("CC BY 4.0")).toBeInTheDocument();
    expect(await screen.findByText("Datos abiertos")).toBeInTheDocument();
  });

  it("agrega el top departamental a partir del mapa", async () => {
    vi.stubGlobal("fetch", mockFetchOk());
    render(<App />);
    expect(await screen.findByText("Top 10 departamentos")).toBeInTheDocument();
  });
});
