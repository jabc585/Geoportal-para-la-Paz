import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

export function MapaNacional() {
  const contenedor = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!contenedor.current) return;
    const mapa = new maplibregl.Map({
      container: contenedor.current,
      style: {
        version: 8,
        sources: {
          osm: {
            type: "raster",
            tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
            tileSize: 256,
            attribution: "© OpenStreetMap contributors",
          },
        },
        layers: [
          { id: "osm", type: "raster", source: "osm" },
        ],
      },
      center: [-73.5, 4.5],
      zoom: 5,
    });
    // TODO fase 5: capas coropléticas desde pg_tileserv (sección 4.1) con
    // indicadores reales de serie_historica y capas de contexto (sección 5.1)
    return () => mapa.remove();
  }, []);

  return <div ref={contenedor} className="mapa-contenedor" role="img" aria-label="Mapa nacional del observatorio" />;
}
