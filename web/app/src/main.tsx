import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { LimiteDeErro } from "./components/LimiteDeErro";
import { temaInicial } from "./hooks/useTema";
import "./estilos.css";

// Aplica o tema antes da primeira pintura para a página não piscar no tema errado.
document.documentElement.dataset.tema = temaInicial();

createRoot(document.getElementById("raiz")!).render(
  <StrictMode>
    <LimiteDeErro>
      <App />
    </LimiteDeErro>
  </StrictMode>,
);
