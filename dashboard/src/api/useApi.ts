import { useEffect, useRef, useState } from "react";

export interface EstadoApi<T> {
  datos: T | null;
  error: string | null;
  cargando: boolean;
}

export function useApi<T>(
  llamada: () => Promise<T>,
  dependencias: readonly unknown[] = [],
): EstadoApi<T> {
  const [datos, setDatos] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(true);
  const llamadaRef = useRef(llamada);
  llamadaRef.current = llamada;

  useEffect(() => {
    let activo = true;
    setCargando(true);
    setError(null);
    llamadaRef
      .current()
      .then((d) => {
        if (activo) setDatos(d);
      })
      .catch((e: unknown) => {
        if (activo) setError(e instanceof Error ? e.message : "Error desconocido");
      })
      .finally(() => {
        if (activo) setCargando(false);
      });
    return () => {
      activo = false;
    };
  }, dependencias);

  return { datos, error, cargando };
}
