import { KPIFuentes } from "../components/KPIFuentes";
import { MapaNacional } from "../maps/MapaNacional";

// KPIs planificados en el wireframe del dashboard (sección 9.1 del plan) que
// todavía no tienen pipeline con carga a curated (ver auditoría): se marcan
// como "próximamente" en vez de inventar una cifra.
const KPIS_PLANIFICADOS = ["Víctimas", "Homicidios", "Proyectos PDET"];

export function Inicio() {
  return (
    <>
      <section className="kpis" id="inicio" aria-label="Indicadores principales">
        <KPIFuentes />
        {KPIS_PLANIFICADOS.map((etiqueta) => (
          <div className="kpi es-placeholder" key={etiqueta}>
            <div className="kpi-etiqueta">{etiqueta}</div>
            <div className="kpi-valor">Próximamente</div>
          </div>
        ))}
      </section>

      <section className="panel" id="mapa">
        <div className="panel-cabecera">
          <h2 className="panel-titulo">Mapa Nacional</h2>
          <span className="panel-nota">Capas de indicadores: fase 5 del plan</span>
        </div>
        <MapaNacional />
        <a className="enlace-metodologia" href="#metodologia" title="¿Cómo se calcula?">
          ¿Cómo se calcula? →
        </a>
      </section>

      <section className="panel" id="metodologia">
        <h2 className="panel-titulo">Metodología</h2>
        <p>
          Cada cifra del observatorio conserva su linaje: fuente oficial, URL de
          origen, fecha de extracción y licencia (sección 3, punto 4 del plan).
          Fichas metodológicas por fuente en <code>docs/fuentes/</code>.
        </p>
      </section>
    </>
  );
}
