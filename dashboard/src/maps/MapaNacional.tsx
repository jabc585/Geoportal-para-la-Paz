import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { MapaIndicador, descargarCSV, obtenerMapa } from "../api/client";

// Paleta secuencial viridis (verificada para daltonismo, sección 10 del plan):
// menor valor = amarillo, mayor valor = púrpura oscuro. Sin dato = gris.
const RAMPAS = {
  viridis: ["#fde725", "#addc30", "#5ec962", "#21918c", "#440154"],
  grisSinDato: "#e3e6e8",
  borde: "#fcfcfc",
};

// Indicadores municipales reales que ya cargan a serie_historica (fase 5).
const INDICADORES_MAPA: { codigo: string; etiqueta: string }[] = [
  { codigo: "homicidios", etiqueta: "Homicidios (Policía Nacional)" },
  { codigo: "victimas_ruv", etiqueta: "Personas incluidas en el RUV (UARIV)" },
  { codigo: "poblacion", etiqueta: "Población proyectada (DANE)" },
  { codigo: "ideam_deforestacion", etiqueta: "Deforestación ha (IDEAM)" },
  { codigo: "hdx_conflicto_eventos", etiqueta: "Eventos de conflicto (HDX)" },
  { codigo: "cnmh_desaparicion_victimas", etiqueta: "Desaparición forzada (CNMH)" },
];

function quintiles(valores: number[]): number[] {
  const ordenados = [...valores].sort((a, b) => a - b);
  return [1, 2, 3, 4].map((q) => ordenados[Math.floor((q * ordenados.length) / 5)]);
}

function formatearValor(valor: number): string {
  return new Intl.NumberFormat("es-CO").format(Math.round(valor * 10) / 10);
}

function descargarGeoJSON(datos: MapaIndicador): void {
  const blob = new Blob([JSON.stringify(datos, null, 2)], {
    type: "application/geo+json",
  });
  const url = URL.createObjectURL(blob);
  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = `${datos.indicador}_${datos.anio ?? "sindatos"}.geojson`;
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();
  URL.revokeObjectURL(url);
}

export function MapaNacional() {
  const contenedor = useRef<HTMLDivElement>(null);
  const mapaRef = useRef<maplibregl.Map | null>(null);
  const [indicador, setIndicador] = useState(INDICADORES_MAPA[0].codigo);
  const [datos, setDatos] = useState<MapaIndicador | null>(null);
  const [cortes, setCortes] = useState<number[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const mapa = new maplibregl.Map({
      container: contenedor.current!,
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
      center: [-73.5, 4.5],
      zoom: 5,
    });
    mapaRef.current = mapa;
    return () => {
      mapa.remove();
      mapaRef.current = null;
    };
  }, []);

  useEffect(() => {
    let cancelado = false;
    setError(null);
    obtenerMapa(indicador)
      .then((d) => {
        if (cancelado) return;
        setDatos(d);
        const valores = d.features
          .map((f) => f.properties.valor)
          .filter((v): v is number => v !== null);
        setCortes(valores.length >= 5 ? quintiles(valores) : []);
      })
      .catch((e: unknown) => {
        if (cancelado) return;
        setError(e instanceof Error ? e.message : "Error al cargar el mapa");
      });
    return () => {
      cancelado = true;
    };
  }, [indicador]);

  useEffect(() => {
    const mapa = mapaRef.current;
    if (!mapa || !datos) return;
    const fuente: maplibregl.GeoJSONSourceSpecification = {
      type: "geojson",
      data: {
        type: "FeatureCollection",
        features: datos.features,
      } as unknown as maplibregl.GeoJSONSourceSpecification["data"],
    };
    const capaFillId = "choropleth-fill";
    const capaBordeId = "choropleth-borde";
    if (mapa.getSource("choropleth")) {
      (mapa.getSource("choropleth") as maplibregl.GeoJSONSource).setData(fuente.data!);
    } else {
      mapa.addSource("choropleth", fuente);
      // Quintiles discretos: menor quintil = viridis[0], mayor = viridis[4].
      // Los municipios sin dato (null → -1) quedan en gris.
      const cortesDiscretos = cortes.length === 4 ? cortes : [Number.MAX_SAFE_INTEGER];
      const pasos: maplibregl.ExpressionSpecification = [
        "step",
        ["coalesce", ["get", "valor"], -1],
        RAMPAS.grisSinDato,
        0,
        RAMPAS.viridis[0],
      ];
      cortesDiscretos.forEach((corte, i) => {
        pasos.push(corte, RAMPAS.viridis[Math.min(i + 1, 4)]);
      });
      mapa.addLayer({
        id: capaFillId,
        type: "fill",
        source: "choropleth",
        paint: { "fill-color": pasos, "fill-opacity": 0.85 },
      });
      mapa.addLayer({
        id: capaBordeId,
        type: "line",
        source: "choropleth",
        paint: { "line-color": RAMPAS.borde, "line-width": 0.5 },
      });
      const popup = new maplibregl.Popup({ closeButton: false, offset: 8 });
      mapa.on("mousemove", (e) => {
        const feature = mapa.queryRenderedFeatures(e.point, {
          layers: [capaFillId],
        })[0];
        if (feature?.properties) {
          const p = feature.properties as { municipio?: string; departamento?: string; valor?: number | null };
          popup
            .setLngLat(e.lngLat)
            .setHTML(
              `<strong>${p.municipio ?? ""}</strong><br/>${p.departamento ?? ""}<br/>` +
                (p.valor === null || p.valor === undefined
                  ? "Sin dato"
                  : `${formatearValor(p.valor)} ${datos.unidad}`)
            )
            .addTo(mapa);
        } else {
          popup.remove();
        }
      });
      mapa.on("mouseleave", capaFillId, () => popup.remove());
    }
  }, [datos]);

  return (
    <div className="mapa-nacional">
      <div className="mapa-controles">
        <label htmlFor="mapa-indicador" className="mapa-control-etiqueta">
          Indicador
        </label>
        <select
          id="mapa-indicador"
          value={indicador}
          onChange={(e) => setIndicador(e.target.value)}
          className="mapa-select"
        >
          {INDICADORES_MAPA.map((i) => (
            <option key={i.codigo} value={i.codigo}>
              {i.etiqueta}
            </option>
          ))}
        </select>
        <span className="mapa-anio">
          {datos ? (datos.anio === null ? "Sin datos aún" : `Año ${datos.anio}`) : "Cargando…"}
        </span>
        {datos && (
          <span className="mapa-exportar">
            <button
              type="button"
              className="boton-secundario"
              onClick={() => descargarCSV(datos.indicador)}
              title="Serie completa (municipio-año) del indicador"
            >
              CSV
            </button>
            <button
              type="button"
              className="boton-secundario"
              onClick={() => descargarGeoJSON(datos)}
              title="Capa coroplética que se está viendo (GeoJSON)"
            >
              GeoJSON
            </button>
          </span>
        )}
      </div>
      {error && <p className="mapa-error">No se pudo cargar el mapa: {error}</p>}
      <div ref={contenedor} className="mapa-contenedor" role="img" aria-label="Mapa coroplético municipal del observatorio" />
      {datos && (
        <div className="mapa-leyenda" aria-label="Leyenda del mapa">
          <span className="mapa-leyenda-titulo">
            {datos.nombre} ({datos.unidad})
          </span>
          {cortes.length === 4 ? (
            <ol className="mapa-leyenda-escala">
              <li>
                <i style={{ background: RAMPAS.grisSinDato }} /> Sin dato
              </li>
              {cortes.map((corte, i) => (
                <li key={i}>
                  <i style={{ background: RAMPAS.viridis[i] }} />
                  {formatearValor(i === 0 ? 0 : cortes[i - 1] + 0.1)} – {formatearValor(corte)}
                </li>
              ))}
              <li>
                <i style={{ background: RAMPAS.viridis[4] }} /> {formatearValor(cortes[3] + 0.1)} – máx
              </li>
            </ol>
          ) : (
            <p className="mapa-leyenda-nota">Valores por quintiles cuando haya al menos 5 municipios con dato.</p>
          )}
        </div>
      )}
    </div>
  );
}
