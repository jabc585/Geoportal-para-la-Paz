import { KPIFuentes } from "../components/KPIFuentes";
import { MapaNacional } from "../maps/MapaNacional";

export function Inicio() {
  return (
    <>
      <section className="kpis" aria-label="Indicadores principales">
        <KPIFuentes />
      </section>

      <section className="panel">
        <h2 className="panel-titulo">Mapa Nacional</h2>
        <MapaNacional />
        <p>
          <a href="#metodologia" title="¿Cómo se calcula?">¿Cómo se calcula?</a>
        </p>
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
