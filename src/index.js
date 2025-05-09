import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";  // Importa el archivo CSS correctamente

import App from "./App";

const root = createRoot(document.getElementById("root"));
root.render(
  <StrictMode>
    <App />
  </StrictMode>
);
