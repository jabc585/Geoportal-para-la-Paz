import { obtenerFuentes } from "../api/client";
import { useApi } from "../api/useApi";

export function KPIFuentes() {
  const { datos, error, cargando } = useApi(obtenerFuentes);

  return (
    <div className="kpi">
      <div className="kpi-etiqueta">Fuentes oficiales integradas</div>
      <div className={`kpi-valor${error ? " es-error" : cargando ? " esta-cargando" : ""}`}>
        {error ? "API no disponible" : cargando ? "…" : datos?.length}
      </div>
    </div>
  );
}
