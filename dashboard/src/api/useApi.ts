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
    llamadaRef
      .current()
      .then((d) => {
        if (activo) setDatos(d);
      })
      .catch((e: Error) => {
        if (activo) setError(e.message);
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
