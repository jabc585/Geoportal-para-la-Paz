import { useEffect, useState } from "react";
import { obtenerTotalIndicador } from "../api/client";

const NUMERO = new Intl.NumberFormat("es-CO");

interface Props {
  codigo: string;
  etiqueta: string;
  unidad?: string;
}

export function KPIIndicador({ codigo, etiqueta, unidad }: Props) {
  const [texto, setTexto] = useState<string | null>(null);
  const [anio, setAnio] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    obtenerTotalIndicador(codigo)
      .then((d) => {
        const ultimo = d.totales[0];
        if (ultimo) {
          setTexto(NUMERO.format(ultimo.valor));
          setAnio(ultimo.anio);
        } else {
          setTexto("Sin datos");
        }
      })
      .catch((e: Error) => setError(e.message));
  }, [codigo]);

  return (
    <div className="kpi">
      <div className="kpi-etiqueta">{etiqueta}</div>
      <div className={`kpi-valor${texto === null && !error ? " esta-cargando" : ""}`}>
        {error ? "API no disponible" : texto ?? "…"}
      </div>
      {anio !== null && (
        <div className="kpi-subetiqueta">
          {anio} · {unidad ?? "dato nacional"}
        </div>
      )}
    </div>
  );
}
