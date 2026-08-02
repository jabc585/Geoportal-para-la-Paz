import { obtenerTotalIndicador } from "../api/client";
import { useApi } from "../api/useApi";

const NUMERO = new Intl.NumberFormat("es-CO");

interface Props {
  codigo: string;
  etiqueta: string;
  unidad?: string;
}

export function KPIIndicador({ codigo, etiqueta, unidad }: Props) {
  const { datos, error, cargando } = useApi(
    () => obtenerTotalIndicador(codigo),
    [codigo],
  );

  const ultimo = datos?.totales[0];
  const texto = error
    ? "API no disponible"
    : ultimo
      ? NUMERO.format(ultimo.valor)
      : cargando
        ? "…"
        : "Sin datos";

  return (
    <div className="kpi">
      <div className="kpi-etiqueta">{etiqueta}</div>
      <div className={`kpi-valor${cargando ? " esta-cargando" : ""}`}>{texto}</div>
      {ultimo && (
        <div className="kpi-subetiqueta">
          {ultimo.anio} · {unidad ?? "dato nacional"}
        </div>
      )}
    </div>
  );
}
