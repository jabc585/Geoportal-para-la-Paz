import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { KPIFuentes } from "../components/KPIFuentes";
import type { Fuente } from "../api/client";

vi.mock("../api/useApi", () => ({
  useApi: vi.fn(),
}));

const { useApi } = await import("../api/useApi");
const mockedUseApi = useApi as unknown as ReturnType<typeof vi.fn>;

describe("KPIFuentes", () => {
  it("muestra el conteo de fuentes", () => {
    mockedUseApi.mockReturnValue({
      datos: [
        { fuente_id: 1, nombre: "a", entidad: "b", licencia: "c", ultima_actualizacion: null, url_base: null },
        { fuente_id: 2, nombre: "d", entidad: "e", licencia: "f", ultima_actualizacion: null, url_base: null },
      ] as Fuente[],
      error: null,
      cargando: false,
    });
    render(<KPIFuentes />);
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("muestra estado de carga", () => {
    mockedUseApi.mockReturnValue({ datos: null, error: null, cargando: true });
    render(<KPIFuentes />);
    expect(screen.getByText("…")).toBeInTheDocument();
  });

  it("muestra mensaje de error", () => {
    mockedUseApi.mockReturnValue({ datos: null, error: "Error de red", cargando: false });
    render(<KPIFuentes />);
    expect(screen.getByText("API no disponible")).toBeInTheDocument();
  });
});
