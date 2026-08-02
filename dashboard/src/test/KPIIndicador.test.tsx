import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { KPIIndicador } from "../components/KPIIndicador";

vi.mock("../api/useApi", () => ({
  useApi: vi.fn(),
}));

const { useApi } = await import("../api/useApi");
const mockedUseApi = useApi as unknown as ReturnType<typeof vi.fn>;

describe("KPIIndicador", () => {
  it("muestra valor formateado y año", () => {
    mockedUseApi.mockReturnValue({
      datos: {
        indicador: "poblacion",
        nombre: "Población",
        unidad: "habitantes",
        totales: [{ anio: 2024, valor: 1200000 }],
      },
      error: null,
      cargando: false,
    });
    render(<KPIIndicador codigo="poblacion" etiqueta="Población" unidad="habitantes" />);
    expect(screen.getByText("1.200.000")).toBeInTheDocument();
    expect(screen.getByText("2024 · habitantes")).toBeInTheDocument();
  });

  it("muestra 'Sin datos' cuando no hay totales", () => {
    mockedUseApi.mockReturnValue({
      datos: { totales: [] },
      error: null,
      cargando: false,
    });
    render(<KPIIndicador codigo="x" etiqueta="X" />);
    expect(screen.getByText("Sin datos")).toBeInTheDocument();
  });

  it("muestra estado de carga", () => {
    mockedUseApi.mockReturnValue({ datos: null, error: null, cargando: true });
    render(<KPIIndicador codigo="x" etiqueta="X" />);
    expect(screen.getByText("…")).toBeInTheDocument();
  });
});
