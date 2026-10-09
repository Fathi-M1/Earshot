import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "@/App";
import { brand } from "@/lib/brand";
import "./index.css";

document.title = brand.displayName;

const root = document.getElementById("root");
if (!root) throw new Error("Missing root");

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
