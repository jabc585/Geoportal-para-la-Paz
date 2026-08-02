import { useEffect, useState } from "react";
import { obtenerFuentes, type Fuente } from "../api/client";

export function KPIFuentes() {
  const [fuentes, setFuentes] = useState<Fuente[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    obtenerFuentes()
      .then(setFuentes)
      .catch((e: Error) => setError(e.message))
      .finally(() => setCargando(false));
  }, []);

  if (error) {
    return (
      <div className="kpi">
        <div className="kpi-etiqueta">Fuentes oficiales integradas</div>
        <div className="kpi-valor es-error">API no disponible</div>
      </div>
    );
  }

  return (
    <div className="kpi">
      <div className="kpi-etiqueta">Fuentes oficiales integradas</div>
      <div className={`kpi-valor${cargando ? " esta-cargando" : ""}`}>
        {cargando ? "…" : fuentes.length}
      </div>
    </div>
  );
}
