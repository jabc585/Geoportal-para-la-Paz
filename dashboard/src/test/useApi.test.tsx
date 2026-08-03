import { describe, expect, it, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useApi } from "../api/useApi";

describe("useApi", () => {
  it("empieza cargando y entrega los datos", async () => {
    const { result } = renderHook(() => useApi(() => Promise.resolve({ ok: 1 })));
    expect(result.current.cargando).toBe(true);
    await waitFor(() => expect(result.current.cargando).toBe(false));
    expect(result.current.datos).toEqual({ ok: 1 });
    expect(result.current.error).toBeNull();
  });

  it("expone el mensaje de error sin dejar datos a medias", async () => {
    const { result } = renderHook(() =>
      useApi(() => Promise.reject(new Error("Error 503 en /fuentes"))),
    );
    await waitFor(() => expect(result.current.cargando).toBe(false));
    expect(result.current.error).toBe("Error 503 en /fuentes");
    expect(result.current.datos).toBeNull();
  });

  it("no actualiza el estado si el componente se desmontó antes de responder", async () => {
    const errores = vi.spyOn(console, "error").mockImplementation(() => {});
    let resolver: (v: string) => void = () => {};
    const pendiente = new Promise<string>((res) => {
      resolver = res;
    });
    const { unmount } = renderHook(() => useApi(() => pendiente));
    unmount();
    resolver("tarde");
    await pendiente;
    expect(errores).not.toHaveBeenCalled();
    errores.mockRestore();
  });

  it("refetch al cambiar las dependencias", async () => {
    const llamada = vi.fn((n: number) => Promise.resolve(n));
    const { result, rerender } = renderHook(
      ({ n }: { n: number }) => useApi(() => llamada(n), [n]),
      { initialProps: { n: 1 } },
    );
    await waitFor(() => expect(result.current.datos).toBe(1));
    rerender({ n: 2 });
    await waitFor(() => expect(result.current.datos).toBe(2));
    expect(llamada).toHaveBeenCalledTimes(2);
  });
});
