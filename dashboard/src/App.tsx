import { Inicio } from "./pages/Inicio";

export default function App() {
  return (
    <>
      <header className="observatorio-header">
        <h1>Observatorio para la Paz en Colombia</h1>
        <nav className="observatorio-nav">
          <a href="#inicio">Inicio</a>
          <a href="#mapa">Mapa Nacional</a>
          <a href="#metodologia">Metodología</a>
          <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">API</a>
        </nav>
      </header>
      <main>
        <Inicio />
      </main>
    </>
  );
}
