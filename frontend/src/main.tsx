import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ATMProvider } from "./state/ATMContext";
import App from "./App";
import "./styles/global.css";
import "./styles/screen.css";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element not found");
}

createRoot(rootElement).render(
  <StrictMode>
    <ATMProvider>
      <App />
    </ATMProvider>
  </StrictMode>,
);
