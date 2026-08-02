import { useEffect, useState } from "react";
import { obtenerFuentes, type Fuente } from "../api/client";

export function KPIFuentes() {
  const [fuentes, setFuentes] = useState<Fuente[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    obtenerFuentes()
      .then(setFuentes)
      .catch((e: Error) => setError(e.message));
  }, []);

  if (error) {
    return (
      <div className="kpi">
        <div className="kpi-etiqueta">API no disponible</div>
        <div className="kpi-valor">—</div>
      </div>
    );
  }

  return (
    <div className="kpi">
      <div className="kpi-etiqueta">Fuentes oficiales integradas</div>
      <div className="kpi-valor">{fuentes.length}</div>
    </div>
  );
}
