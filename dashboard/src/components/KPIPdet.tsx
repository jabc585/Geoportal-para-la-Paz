import { obtenerProyectosPdet } from "../api/client";
import { useApi } from "../api/useApi";

export function KPIPdet() {
  const { datos, error, cargando } = useApi(obtenerProyectosPdet);

  return (
    <div className="kpi">
      <div className="kpi-etiqueta">Proyectos PDET (ART)</div>
      <div className={`kpi-valor${error ? " es-error" : cargando ? " esta-cargando" : ""}`}>
        {error ? "API no disponible" : cargando ? "…" : datos?.proyectos.toLocaleString("es-CO")}
      </div>
    </div>
  );
}
