import { useState, useEffect, useMemo, useCallback } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import {
  Download,
  ExternalLink,
  Shield,
  Users,
  Globe,
  Layers,
  TreePine,
  AlertTriangle,
  Search,
  Map,
  BookOpen,
  ChevronRight,
  Database,
  FileText,
} from "lucide-react";
import {
  DOCS_URL,
  healthcheck,
  obtenerFuentes,
  obtenerMapa,
  obtenerProyectosPdet,
  obtenerTotalIndicador,
  urlExportarCSV,
} from "../api/client";
import { useApi } from "../api/useApi";
import { MapaNacional } from "./components/MapaNacional";
import {
  VIRIDIS,
  agregarPorDepartamento,
  asignarColoresViridis,
  fmt,
  fmtCompact,
  fmtKPI,
} from "./utils";

// ─── Indicadores ─────────────────────────────────────────────────────────────
// Los seis códigos existen en curated.indicadores y responden 200 en
// /api/v1/mapas/{codigo} (verificado contra la API).
const INDICADORES = [
  {
    codigo: "homicidios",
    etiqueta: "Homicidios",
    fuente: "Policía Nacional · SIEDCO",
    Icon: Shield,
    unidad: "casos",
    // Un agregado departamental solo tiene sentido sumando conteos. Si alguna
    // vez se añade una tasa o un porcentaje, debe marcarse agregable: false.
    agregable: true,
  },
  {
    codigo: "victimas_ruv",
    etiqueta: "Personas incluidas en el RUV",
    fuente: "UARIV · Datos Paz",
    Icon: Users,
    unidad: "personas",
    agregable: true,
  },
  {
    codigo: "poblacion",
    etiqueta: "Población proyectada",
    fuente: "DANE · Proyecciones",
    Icon: Globe,
    unidad: "habitantes",
    agregable: true,
  },
  {
    codigo: "ideam_deforestacion",
    etiqueta: "Deforestación",
    fuente: "IDEAM · Raster Bosque/No Bosque",
    Icon: TreePine,
    unidad: "ha",
    agregable: true,
  },
  {
    codigo: "hdx_conflicto_eventos",
    etiqueta: "Eventos de conflicto",
    fuente: "HDX · HAPI Colombia",
    Icon: AlertTriangle,
    unidad: "eventos",
    agregable: true,
  },
  {
    codigo: "cnmh_desaparicion_victimas",
    etiqueta: "Desaparición forzada",
    fuente: "CNMH · SIEVCAC",
    Icon: Search,
    unidad: "víctimas",
    agregable: true,
  },
];

// ─── Custom Tooltip ───────────────────────────────────────────────────────────
function CustomTooltip({
  active,
  payload,
  unidad,
}: {
  active?: boolean;
  payload?: { value: number; payload: { nombre: string; color: string } }[];
  unidad: string;
}) {
  if (!active || !payload?.length) return null;
  const { nombre, color } = payload[0].payload;
  const valor = payload[0].value;
  return (
    <div
      style={{ background: "#0c1e2f", border: "1px solid rgba(255,255,255,0.1)" }}
      className="rounded-lg px-3 py-2 text-sm shadow-xl"
    >
      <p className="text-[#94b8d4] mb-1 font-medium">{nombre}</p>
      <p className="font-mono font-semibold" style={{ color }}>
        {fmt(valor)}{" "}
        <span className="font-normal text-[#5c7a91] text-xs">{unidad}</span>
      </p>
    </div>
  );
}

// ─── KPI Card ─────────────────────────────────────────────────────────────────
function KPICard({
  label,
  value,
  sub,
  Icon,
  accent = false,
  cargando = false,
  error = false,
  linaje,
}: {
  label: string;
  value: string;
  sub?: string;
  Icon: React.ComponentType<{ className?: string; size?: number }>;
  accent?: boolean;
  cargando?: boolean;
  error?: boolean;
  linaje?: string;
}) {
  return (
    <div
      className={[
        "rounded-xl p-5 flex flex-col gap-3 transition-all duration-200",
        "bg-card border border-border hover:border-white/15 hover:shadow-lg hover:shadow-black/30",
      ].join(" ")}
      title={linaje}
    >
      <div className="flex items-center justify-between">
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center"
          style={{
            background: accent ? "rgba(245,197,24,0.12)" : "rgba(29,115,201,0.12)",
          }}
        >
          <Icon size={15} className={accent ? "text-accent" : "text-primary"} />
        </div>
        {!cargando && !error && sub && (
          <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest">
            {sub}
          </span>
        )}
      </div>
      <div>
        <p className="text-muted-foreground text-xs font-medium mb-1 leading-tight">
          {label}
        </p>
        {cargando ? (
          // Skeleton del tamaño final: evita el salto de layout al llegar el dato.
          <div className="h-8 w-24 rounded-md bg-white/5 animate-pulse" aria-hidden />
        ) : error ? (
          <p className="font-mono text-muted-foreground text-sm">API no disponible</p>
        ) : (
          <p
            className="font-mono font-semibold text-2xl text-foreground tracking-tight"
            style={{ fontVariantNumeric: "tabular-nums" }}
            aria-live="polite"
          >
            {value}
          </p>
        )}
      </div>
    </div>
  );
}

/** KPI de un indicador: total nacional del año más reciente. */
function KPIIndicador({
  codigo,
  label,
  unidad,
  Icon,
}: {
  codigo: string;
  label: string;
  unidad: string;
  Icon: React.ComponentType<{ className?: string; size?: number }>;
}) {
  const llamada = useCallback(() => obtenerTotalIndicador(codigo), [codigo]);
  const { datos, error, cargando } = useApi(llamada, [codigo]);
  const ultimo = datos?.totales?.[0];

  return (
    <KPICard
      label={label}
      value={ultimo ? fmtKPI(ultimo.valor) : "Sin datos"}
      sub={ultimo ? `${ultimo.anio} · ${datos?.unidad ?? unidad}` : undefined}
      Icon={Icon}
      cargando={cargando}
      error={!!error}
      linaje={ultimo ? `${fmt(ultimo.valor)} ${datos?.unidad ?? unidad} · ${datos?.nombre ?? label}` : undefined}
    />
  );
}

// ─── Sección de Metodología ───────────────────────────────────────────────────
function Metodologia() {
  const items = [
    {
      title: "Trazabilidad de datos",
      body: "Cada cifra que aparece en este observatorio puede rastrearse hasta su fuente primaria: la entidad que la recopila, el año de corte y el método de agregación. Los datos se ingresan a través de un ETL auditable que registra cada transformación.",
      Icon: Database,
    },
    {
      title: "Fichas metodológicas",
      body: "Cada indicador cuenta con una ficha en docs/fuentes/ que describe la población de referencia, la unidad de medida, la periodicidad de actualización, las limitaciones conocidas y el linaje de procesamiento desde la fuente hasta curated.*.",
      Icon: FileText,
    },
    {
      title: "Linaje de indicadores",
      body: "El pipeline extrae datos de APIs oficiales (Policía Nacional, UARIV, DANE, IDEAM, CNMH, ART), los valida con controles de rango y consistencia temporal, y los carga en tablas curadas en PostgreSQL conservando fuente, URL de origen y fecha de extracción.",
      Icon: Layers,
    },
  ];

  return (
    <section id="metodologia" className="py-16">
      <div className="flex items-center gap-3 mb-2">
        <BookOpen size={18} className="text-primary" />
        <span className="text-xs font-mono text-muted-foreground uppercase tracking-widest">
          Metodología
        </span>
      </div>
      <h2 className="text-2xl font-semibold text-foreground mb-2">
        Trazabilidad y linaje de datos
      </h2>
      <p className="text-muted-foreground text-sm mb-10 max-w-2xl">
        El observatorio no publica cifras sin respaldo. Cada indicador tiene una
        ficha metodológica que documenta su origen, transformación y limitaciones.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {items.map(({ title, body, Icon }) => (
          <div
            key={title}
            className="bg-card border border-border rounded-xl p-6 hover:border-white/15 transition-colors duration-200"
          >
            <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
              <Icon size={16} className="text-primary" />
            </div>
            <h3 className="font-semibold text-foreground text-sm mb-2">{title}</h3>
            <p className="text-muted-foreground text-xs leading-relaxed">{body}</p>
          </div>
        ))}
      </div>
      <div className="mt-6 p-4 rounded-xl border border-accent/20 bg-accent/5 flex items-start gap-3">
        <span className="text-accent mt-0.5">
          <BookOpen size={14} />
        </span>
        <p className="text-xs text-[#94b8d4] leading-relaxed">
          Las fichas metodológicas completas están disponibles en{" "}
          <code className="font-mono text-accent/80 bg-accent/10 px-1 py-0.5 rounded text-xs">
            docs/fuentes/
          </code>{" "}
          dentro del repositorio. Cualquier discrepancia entre la fuente primaria y lo
          publicado aquí debe reportarse como issue en el repositorio del proyecto.
        </p>
      </div>
    </section>
  );
}

// ─── Tabla de fuentes ─────────────────────────────────────────────────────────
function TablaFuentes() {
  const { datos, error, cargando } = useApi(obtenerFuentes);

  if (cargando) {
    return (
      <div className="h-24 rounded-xl border border-border bg-card animate-pulse" aria-hidden />
    );
  }
  if (error || !datos?.length) return null;

  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden overflow-x-auto">
      <table className="w-full text-xs">
        <caption className="sr-only">
          Fuentes oficiales integradas, con entidad, licencia y última actualización
        </caption>
        <thead>
          <tr className="border-b border-border text-muted-foreground">
            <th scope="col" className="text-left font-medium px-4 py-2.5">Fuente</th>
            <th scope="col" className="text-left font-medium px-4 py-2.5">Entidad</th>
            <th scope="col" className="text-left font-medium px-4 py-2.5">Licencia</th>
            <th scope="col" className="text-left font-medium px-4 py-2.5">Actualizada</th>
          </tr>
        </thead>
        <tbody>
          {datos.map((f) => (
            <tr key={f.fuente_id} className="border-b border-border/50 last:border-0">
              <td className="px-4 py-2.5 text-foreground">
                {f.url_base ? (
                  <a
                    href={f.url_base}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:text-primary/80 transition-colors"
                  >
                    {f.nombre}
                  </a>
                ) : (
                  f.nombre
                )}
              </td>
              <td className="px-4 py-2.5 text-muted-foreground">{f.entidad}</td>
              <td className="px-4 py-2.5 text-muted-foreground">{f.licencia}</td>
              <td className="px-4 py-2.5 font-mono text-muted-foreground">
                {f.ultima_actualizacion ? f.ultima_actualizacion.slice(0, 10) : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── Footer ───────────────────────────────────────────────────────────────────
function Footer() {
  return (
    <footer className="border-t border-border py-8">
      <div className="max-w-[1200px] mx-auto px-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Datos publicados bajo licencia{" "}
            <a
              href="https://creativecommons.org/licenses/by/4.0/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:text-primary/80 transition-colors"
            >
              CC BY 4.0
            </a>
            . Cada indicador incluye ficha metodológica con trazabilidad completa.
          </p>
          <p className="text-[11px] text-muted-foreground/60 mt-1">
            Observatorio para la Paz en Colombia · {new Date().getFullYear()}
          </p>
        </div>
        <a
          href={DOCS_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 text-xs text-primary hover:text-primary/80 transition-colors whitespace-nowrap"
        >
          Documentación API
          <ExternalLink size={12} />
        </a>
      </div>
    </footer>
  );
}

// ─── App principal ────────────────────────────────────────────────────────────
export default function App() {
  const [indicador, setIndicador] = useState("homicidios");
  const [activeNav, setActiveNav] = useState("inicio");
  const [apiViva, setApiViva] = useState<boolean | null>(null);

  const indInfo = INDICADORES.find((i) => i.codigo === indicador)!;

  // El mapa y el gráfico por departamento salen de la MISMA petición (C3).
  const llamadaMapa = useCallback(() => obtenerMapa(indicador), [indicador]);
  const { datos: mapaDatos, error: mapaError, cargando: mapaCargando } = useApi(
    llamadaMapa,
    [indicador],
  );

  const { datos: fuentes } = useApi(obtenerFuentes);
  const { datos: pdet, error: pdetError, cargando: pdetCargando } = useApi(obtenerProyectosPdet);

  const porDepartamento = useMemo(() => agregarPorDepartamento(mapaDatos), [mapaDatos]);
  const chartData = useMemo(
    () => asignarColoresViridis(porDepartamento.slice(0, 10)),
    [porDepartamento],
  );
  const totalNacional = useMemo(
    () => porDepartamento.reduce((s, d) => s + d.valor, 0),
    [porDepartamento],
  );
  const anio = mapaDatos?.anio ?? null;
  const unidad = mapaDatos?.unidad ?? indInfo.unidad;

  // Estado real de la API: nunca un literal (plandash2.md C1.3).
  useEffect(() => {
    let activo = true;
    healthcheck().then((ok) => {
      if (activo) setApiViva(ok);
    });
    return () => {
      activo = false;
    };
  }, []);

  // Scroll spy
  useEffect(() => {
    const sections = ["inicio", "mapa", "fuentes", "metodologia"];
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) setActiveNav(entry.target.id);
        });
      },
      { rootMargin: "-40% 0px -55% 0px" },
    );
    sections.forEach((id) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });
    return () => observer.disconnect();
  }, []);

  // Descarga la serie completa desde la API (hasta 200k filas), no un CSV
  // fabricado en el navegador (plandash2.md C5.1).
  function handleDownloadCSV() {
    window.location.href = urlExportarCSV(indicador);
  }

  // GeoJSON con la geometría real que ya está en memoria para el mapa.
  function handleDownloadGeoJSON() {
    if (!mapaDatos) return;
    const geojson = { type: "FeatureCollection", features: mapaDatos.features };
    const blob = new Blob([JSON.stringify(geojson)], { type: "application/geo+json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${indicador}_${anio ?? "sindatos"}.geojson`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const navLinks = [
    { id: "inicio", label: "Inicio" },
    { id: "mapa", label: "Mapa Nacional" },
    { id: "fuentes", label: "Fuentes" },
    { id: "metodologia", label: "Metodología" },
  ];

  return (
    <div
      className="min-h-screen bg-background text-foreground"
      style={{ fontFamily: "'Inter Variable', Inter, system-ui, -apple-system, sans-serif" }}
    >
      <a
        href="#inicio"
        className="sr-only focus:not-sr-only focus:absolute focus:z-[60] focus:top-2 focus:left-2 focus:px-3 focus:py-2 focus:rounded-md focus:bg-primary focus:text-primary-foreground text-xs"
      >
        Saltar al contenido
      </a>

      {/* ── Header ── */}
      <header
        className="sticky top-0 z-50 border-b border-border"
        style={{ background: "rgba(6,17,30,0.92)", backdropFilter: "blur(12px)" }}
      >
        <div className="max-w-[1200px] mx-auto px-6 h-14 flex items-center justify-between gap-8">
          <div className="flex items-center gap-2.5 shrink-0">
            <div className="w-7 h-7 rounded-md bg-primary/20 border border-primary/30 flex items-center justify-center">
              <Map size={13} className="text-primary" />
            </div>
            <span className="font-semibold text-sm text-foreground">
              Observatorio para la Paz
            </span>
            <span className="hidden sm:inline text-muted-foreground text-xs ml-0.5">
              · Colombia
            </span>
          </div>

          <nav className="flex items-center gap-1">
            {navLinks.map(({ id, label }) => (
              <a
                key={id}
                href={`#${id}`}
                onClick={() => setActiveNav(id)}
                aria-current={activeNav === id ? "true" : undefined}
                className={[
                  "px-3 py-1.5 rounded-md text-xs font-medium transition-colors duration-150",
                  activeNav === id
                    ? "bg-primary/15 text-primary"
                    : "text-muted-foreground hover:text-foreground hover:bg-white/5",
                ].join(" ")}
              >
                {label}
              </a>
            ))}
            <a
              href={DOCS_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors duration-150"
            >
              API
              <ExternalLink size={10} />
            </a>
          </nav>
        </div>
      </header>

      {/* ── Main ── */}
      <main className="max-w-[1200px] mx-auto px-6 pb-4">
        {/* ── Inicio: KPIs ── */}
        <section id="inicio" className="pt-14 pb-16">
          <div className="flex items-center gap-3 mb-2">
            <Database size={16} className="text-primary" />
            <span className="text-xs font-mono text-muted-foreground uppercase tracking-widest">
              Indicadores principales
            </span>
          </div>
          <div className="flex items-end justify-between mb-8 flex-wrap gap-4">
            <div>
              <h1 className="text-3xl font-semibold text-foreground tracking-tight">
                Indicadores de paz
              </h1>
              <p className="text-muted-foreground text-sm mt-1.5 max-w-lg">
                Datos de fuentes oficiales. Cada cifra es trazable hasta su
                fuente primaria.
              </p>
            </div>
            {/* Estado real de la API, no un literal */}
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span
                className={[
                  "w-1.5 h-1.5 rounded-full",
                  apiViva === null
                    ? "bg-muted-foreground"
                    : apiViva
                      ? "bg-green-400 animate-pulse"
                      : "bg-destructive",
                ].join(" ")}
              />
              {apiViva === null
                ? "Comprobando API…"
                : apiViva
                  ? "API conectada"
                  : "API no disponible"}
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            <KPICard
              label="Fuentes oficiales integradas"
              value={fuentes ? String(fuentes.length) : "—"}
              sub="activas"
              Icon={Layers}
              cargando={!fuentes && apiViva !== false}
              error={apiViva === false}
            />
            <KPIIndicador codigo="homicidios" label="Homicidios" unidad="casos" Icon={Shield} />
            <KPIIndicador
              codigo="victimas_ruv"
              label="Víctimas RUV"
              unidad="personas"
              Icon={Users}
            />
            <KPIIndicador
              codigo="poblacion"
              label="Población"
              unidad="habitantes"
              Icon={Globe}
            />
            <KPICard
              label="Proyectos PDET"
              value={pdet ? fmt(pdet.proyectos) : "—"}
              sub={pdet ? `${pdet.municipios} municipios` : undefined}
              Icon={AlertTriangle}
              accent
              cargando={pdetCargando}
              error={!!pdetError}
            />
          </div>

          {/* Franja de fuentes: generada desde la API, no hardcodeada */}
          {fuentes && fuentes.length > 0 && (
            <div className="mt-6 flex flex-wrap gap-3">
              {[...new Set(fuentes.map((f) => f.entidad))].map((entidad) => (
                <span
                  key={entidad}
                  className="text-[10px] font-mono text-muted-foreground bg-muted/50 border border-border px-2 py-1 rounded-md"
                >
                  {entidad}
                </span>
              ))}
            </div>
          )}
        </section>

        {/* ── Mapa Nacional ── */}
        <section id="mapa" className="pb-16">
          <div className="flex items-center gap-3 mb-2">
            <Map size={16} className="text-primary" />
            <span className="text-xs font-mono text-muted-foreground uppercase tracking-widest">
              Mapa Nacional
            </span>
          </div>
          <div className="flex items-start justify-between flex-wrap gap-4 mb-6">
            <div>
              <h2 className="text-2xl font-semibold text-foreground mb-1">
                Distribución municipal
              </h2>
              <p className="text-muted-foreground text-xs">
                Capa coroplética por quintiles · agregado municipal
              </p>
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <button
                onClick={handleDownloadCSV}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border text-xs text-muted-foreground hover:text-foreground hover:border-white/20 transition-colors duration-150"
                title="Serie completa del indicador desde la API"
              >
                <Download size={12} />
                CSV
              </button>
              <button
                onClick={handleDownloadGeoJSON}
                disabled={!mapaDatos}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border text-xs text-muted-foreground hover:text-foreground hover:border-white/20 transition-colors duration-150 disabled:opacity-40"
                title="Capa coroplética visible, con geometría"
              >
                <Download size={12} />
                GeoJSON
              </button>
            </div>
          </div>

          <div className="bg-card border border-border rounded-2xl overflow-hidden">
            {/* Selector de indicador */}
            <div
              className="px-6 py-4 border-b border-border flex items-center justify-between flex-wrap gap-3"
              style={{ background: "rgba(15,36,56,0.6)" }}
            >
              <div className="flex items-center gap-3">
                <indInfo.Icon size={15} className="text-primary" />
                <label htmlFor="selector-indicador" className="sr-only">
                  Indicador
                </label>
                <select
                  id="selector-indicador"
                  value={indicador}
                  onChange={(e) => setIndicador(e.target.value)}
                  className="bg-transparent text-sm font-medium text-foreground focus:outline-none cursor-pointer"
                  style={{ color: "inherit" }}
                >
                  {INDICADORES.map((i) => (
                    <option key={i.codigo} value={i.codigo} style={{ background: "#0c1e2f" }}>
                      {i.etiqueta}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex items-center gap-4 text-xs text-muted-foreground font-mono">
                <span>
                  Total nacional:{" "}
                  <span className="text-foreground font-semibold">
                    {mapaCargando ? "…" : mapaError ? "—" : fmt(totalNacional)}
                  </span>{" "}
                  {unidad}
                </span>
                <span className="text-[10px] bg-primary/10 text-primary px-2 py-0.5 rounded-md border border-primary/20">
                  {mapaCargando ? "…" : (anio ?? "sin año")}
                </span>
              </div>
            </div>

            {/* Fuente */}
            <div className="px-6 pt-3 pb-0">
              <p className="text-[10px] text-muted-foreground font-mono">
                Fuente: {indInfo.fuente}
                {mapaDatos?.nombre ? ` · ${mapaDatos.nombre}` : ""}
              </p>
            </div>

            {/* Mapa + leyenda */}
            <div className="grid grid-cols-1 lg:grid-cols-[1fr_220px] gap-0">
              <div className="p-6 pt-4">
                <MapaNacional datos={mapaDatos} cargando={mapaCargando} error={mapaError} />
              </div>

              <div className="lg:border-l border-border p-6 flex flex-col gap-6">
                <div>
                  <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest mb-3">
                    Escala Viridis (quintiles)
                  </p>
                  <div className="space-y-2">
                    {[
                      { label: "Sin dato", color: "#1e3a52" },
                      { label: "Q1 · mínimo", color: VIRIDIS[0] },
                      { label: "Q2", color: VIRIDIS[1] },
                      { label: "Q3 · mediana", color: VIRIDIS[2] },
                      { label: "Q4", color: VIRIDIS[3] },
                      { label: "Q5 · máximo", color: VIRIDIS[4] },
                    ].map(({ label, color }) => (
                      <div key={label} className="flex items-center gap-2.5">
                        <span
                          className="w-4 h-3 rounded-sm shrink-0"
                          style={{ background: color }}
                        />
                        <span className="text-[11px] text-muted-foreground">{label}</span>
                      </div>
                    ))}
                  </div>
                  <p className="text-[10px] text-muted-foreground/50 mt-3 leading-relaxed">
                    Paleta perceptualmente uniforme, verificada para daltonismo
                    (Viridis).
                  </p>
                </div>

                <a
                  href="#metodologia"
                  className="flex items-center gap-1 text-xs text-primary hover:text-primary/80 transition-colors"
                >
                  Ver metodología
                  <ChevronRight size={12} />
                </a>
              </div>
            </div>

            {/* Top-10 departamental, agregado desde la misma petición del mapa */}
            <div className="border-t border-border px-6 py-5">
              <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest mb-3">
                Top 10 departamentos
              </p>
              {mapaCargando ? (
                <div className="h-[320px] flex items-center justify-center">
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-6 h-6 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
                    <p className="text-xs text-muted-foreground font-mono">
                      Agregando por departamento…
                    </p>
                  </div>
                </div>
              ) : chartData.length === 0 ? (
                <p className="text-xs text-muted-foreground py-8 text-center">
                  Sin datos para este indicador.
                </p>
              ) : (
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart
                    data={chartData}
                    layout="vertical"
                    margin={{ top: 0, right: 16, left: 4, bottom: 0 }}
                  >
                    <XAxis
                      type="number"
                      tickFormatter={fmtCompact}
                      tick={{
                        fill: "#5c7a91",
                        fontSize: 10,
                        fontFamily: "'JetBrains Mono Variable', monospace",
                      }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis
                      type="category"
                      dataKey="nombre"
                      width={148}
                      tick={{ fill: "#94b8d4", fontSize: 11, fontFamily: "'Inter Variable', sans-serif" }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <Tooltip
                      content={<CustomTooltip unidad={unidad} />}
                      cursor={{ fill: "rgba(29,115,201,0.05)" }}
                    />
                    <Bar dataKey="valor" radius={[0, 4, 4, 0]} maxBarSize={22}>
                      {chartData.map((entry, index) => (
                        <Cell key={index} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Otros indicadores */}
            <div className="border-t border-border px-6 py-4">
              <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest mb-3">
                Otros indicadores disponibles
              </p>
              <div className="flex flex-wrap gap-2">
                {INDICADORES.filter((i) => i.codigo !== indicador).map((i) => (
                  <button
                    key={i.codigo}
                    onClick={() => setIndicador(i.codigo)}
                    className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs text-muted-foreground border border-border hover:border-primary/40 hover:text-primary hover:bg-primary/5 transition-all duration-150"
                  >
                    <i.Icon size={10} />
                    {i.etiqueta}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* ── Fuentes ── */}
        <section id="fuentes" className="pb-16">
          <div className="flex items-center gap-3 mb-2">
            <Layers size={16} className="text-primary" />
            <span className="text-xs font-mono text-muted-foreground uppercase tracking-widest">
              Fuentes
            </span>
          </div>
          <h2 className="text-2xl font-semibold text-foreground mb-2">
            Fuentes oficiales integradas
          </h2>
          <p className="text-muted-foreground text-sm mb-6 max-w-2xl">
            Cada fuente conserva su entidad responsable, licencia de uso y fecha de
            última actualización registrada por el ETL.
          </p>
          <TablaFuentes />
        </section>

        {/* ── Metodología ── */}
        <Metodologia />
      </main>

      <Footer />
    </div>
  );
}
