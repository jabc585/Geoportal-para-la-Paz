import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { MapaIndicador } from "../../api/client";

// Paleta viridis del proyecto: menor valor = amarillo, mayor = púrpura.
// Verificada para daltonismo (sección 10 del plan) — no cambiar los hex.
const VIRIDIS = ["#fde725", "#addc30", "#5ec962", "#21918c", "#440154"];
const SIN_DATO = "#1e3a52";

// Colombia continental + insular, para que el país entre completo en
// cualquier viewport (plandash2.md C4.2).
const LIMITES: [number, number, number, number] = [-79.1, -4.3, -66.8, 12.6];

export function quintiles(valores: number[]): number[] {
  const ordenados = [...valores].sort((a, b) => a - b);
  return [1, 2, 3, 4].map((q) => ordenados[Math.floor((q * ordenados.length) / 5)]);
}

function contenidoPopup(
  p: { municipio?: string; departamento?: string; valor?: number | null },
  unidad: string,
): HTMLElement {
  const caja = document.createElement("div");
  caja.className = "mapa-popup";
  const municipio = document.createElement("strong");
  municipio.textContent = p.municipio ?? "";
  caja.appendChild(municipio);
  caja.appendChild(document.createElement("br"));
  caja.appendChild(document.createTextNode(p.departamento ?? ""));
  caja.appendChild(document.createElement("br"));
  caja.appendChild(
    document.createTextNode(
      p.valor === null || p.valor === undefined
        ? "Sin dato"
        : `${new Intl.NumberFormat("es-CO").format(Math.round(p.valor * 10) / 10)} ${unidad}`,
    ),
  );
  return caja;
}

interface Props {
  datos: MapaIndicador | null;
  cargando: boolean;
  error: string | null;
}

export function MapaNacional({ datos, cargando, error }: Props) {
  const contenedor = useRef<HTMLDivElement>(null);
  const mapaRef = useRef<maplibregl.Map | null>(null);
  const popupRef = useRef<maplibregl.Popup | null>(null);

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
        layers: [{ id: "osm", type: "raster", source: "osm" }],
      },
      bounds: LIMITES,
      fitBoundsOptions: { padding: 24 },
      // Sin esto, en móvil arrastrar sobre el mapa secuestra el scroll de la
      // página (plandash2.md C4.2).
      cooperativeGestures: true,
    });
    mapa.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    mapa.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-left");
    mapaRef.current = mapa;
    popupRef.current = new maplibregl.Popup({ closeButton: false, offset: 8 });

    return () => {
      popupRef.current?.remove();
      mapa.remove();
      mapaRef.current = null;
    };
  }, []);

  useEffect(() => {
    const mapa = mapaRef.current;
    if (!mapa || !datos) return;

    const aplicar = () => {
      const valores = datos.features
        .map((f) => f.properties.valor)
        .filter((v): v is number => v !== null);
      const cortes = valores.length >= 5 ? quintiles(valores) : [Number.MAX_SAFE_INTEGER];

      const coleccion = { type: "FeatureCollection", features: datos.features };

      const fuente = mapa.getSource("choropleth") as maplibregl.GeoJSONSource | undefined;
      if (fuente) {
        fuente.setData(coleccion as never);
      } else {
        mapa.addSource("choropleth", { type: "geojson", data: coleccion as never });
      }

      // Escalón por quintiles; los municipios sin dato (null → -1) en gris azulado.
      const pasos: unknown[] = ["step", ["coalesce", ["get", "valor"], -1], SIN_DATO, 0, VIRIDIS[0]];
      cortes.forEach((corte, i) => {
        pasos.push(corte, VIRIDIS[Math.min(i + 1, 4)]);
      });

      if (mapa.getLayer("choropleth-fill")) {
        mapa.setPaintProperty("choropleth-fill", "fill-color", pasos as never);
      } else {
        mapa.addLayer({
          id: "choropleth-fill",
          type: "fill",
          source: "choropleth",
          paint: { "fill-color": pasos as never, "fill-opacity": 0.85 },
        });
        mapa.addLayer({
          id: "choropleth-borde",
          type: "line",
          source: "choropleth",
          paint: { "line-color": "#06111e", "line-width": 0.4, "line-opacity": 0.5 },
        });

        const mostrar = (e: maplibregl.MapMouseEvent) => {
          const feature = mapa.queryRenderedFeatures(e.point, { layers: ["choropleth-fill"] })[0];
          if (feature?.properties) {
            popupRef.current
              ?.setLngLat(e.lngLat)
              .setDOMContent(contenidoPopup(feature.properties as never, datos.unidad))
              .addTo(mapa);
          } else {
            popupRef.current?.remove();
          }
        };
        mapa.on("mousemove", "choropleth-fill", mostrar);
        // En táctil no hay hover: el click es la única vía al dato (C4.2).
        mapa.on("click", "choropleth-fill", mostrar);
        mapa.on("mouseleave", "choropleth-fill", () => popupRef.current?.remove());
      }
    };

    if (mapa.isStyleLoaded()) aplicar();
    else mapa.once("load", aplicar);
  }, [datos]);

  return (
    <div className="relative">
      <div
        ref={contenedor}
        role="img"
        aria-label={`Mapa coroplético municipal de ${datos?.nombre ?? "el indicador seleccionado"}`}
        className="h-[420px] w-full rounded-xl overflow-hidden border border-border mapa-oscuro"
      />
      {cargando && (
        <div className="absolute inset-0 flex items-center justify-center rounded-xl bg-background/60 backdrop-blur-sm">
          <span className="text-xs font-mono text-muted-foreground">Cargando capa…</span>
        </div>
      )}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center rounded-xl bg-background/80">
          <span className="text-xs text-destructive">No se pudo cargar el mapa: {error}</span>
        </div>
      )}
    </div>
  );
}
