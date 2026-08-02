import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { KPIPdet } from "../components/KPIPdet";

vi.mock("../api/useApi", () => ({
  useApi: vi.fn(),
}));

const { useApi } = await import("../api/useApi");
const mockedUseApi = useApi as unknown as ReturnType<typeof vi.fn>;

describe("KPIPdet", () => {
  it("muestra conteo de proyectos", () => {
    mockedUseApi.mockReturnValue({
      datos: { proyectos: 35000, municipios: 170 },
      error: null,
      cargando: false,
    });
    render(<KPIPdet />);
    expect(screen.getByText("35.000")).toBeInTheDocument();
  });

  it("muestra estado de carga", () => {
    mockedUseApi.mockReturnValue({ datos: null, error: null, cargando: true });
    render(<KPIPdet />);
    expect(screen.getByText("…")).toBeInTheDocument();
  });

  it("muestra mensaje de error", () => {
    mockedUseApi.mockReturnValue({ datos: null, error: "Error", cargando: false });
    render(<KPIPdet />);
    expect(screen.getByText("API no disponible")).toBeInTheDocument();
  });
});
