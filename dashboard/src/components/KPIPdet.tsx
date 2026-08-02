import { useEffect, useState } from "react";
import { obtenerProyectosPdet, type PdetProyectos } from "../api/client";

export function KPIPdet() {
  const [datos, setDatos] = useState<PdetProyectos | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    obtenerProyectosPdet()
      .then(setDatos)
      .catch((e: Error) => setError(e.message))
      .finally(() => setCargando(false));
  }, []);

  if (error) {
    return (
      <div className="kpi">
        <div className="kpi-etiqueta">Proyectos PDET (ART)</div>
        <div className="kpi-valor es-error">API no disponible</div>
      </div>
    );
  }

  return (
    <div className="kpi">
      <div className="kpi-etiqueta">Proyectos PDET (ART)</div>
      <div className={`kpi-valor${cargando ? " esta-cargando" : ""}`}>
        {cargando ? "…" : datos?.proyectos.toLocaleString("es-CO")}
      </div>
    </div>
  );
}
