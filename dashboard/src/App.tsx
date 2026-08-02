import { Inicio } from "./pages/Inicio";
import { Footer } from "./components/Footer";

export default function App() {
  return (
    <>
      <header className="observatorio-header">
        <div className="observatorio-header-interior">
          <h1>Observatorio para la Paz en Colombia</h1>
          <nav className="observatorio-nav">
            <a href="#inicio">Inicio</a>
            <a href="#mapa">Mapa Nacional</a>
            <a href="#metodologia">Metodología</a>
            <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">API</a>
          </nav>
        </div>
      </header>
      <main>
        <Inicio />
      </main>
      <Footer />
    </>
  );
}
