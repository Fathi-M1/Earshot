import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig, type Plugin } from "vite";
import tokens from "../design/tokens.json";

const root = path.dirname(fileURLToPath(import.meta.url));
const designDir = path.resolve(root, "../design");

function themeBlock() {
  const colors = Object.entries(tokens.color)
    .map(([name, value]) => `  --color-${name}: ${value};`)
    .join("\n");
  const radii = Object.entries(tokens.radius)
    .filter(([name]) => name !== "full" && name !== "icon")
    .map(([name, value]) => `  --radius-${name}: ${value};`)
    .join("\n");
  return `@theme {
${colors}
  --color-bezel: #0B130E;
${radii}
  --font-sans: "Host Grotesk", ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-mono: "Fragment Mono", ui-monospace, "SF Mono", Consolas, monospace;
}
`;
}

function earshotTokens(): Plugin {
  return {
    name: "earshot-tokens",
    enforce: "pre",
    transform(code, id) {
      const file = id.split("?")[0]?.replaceAll("\\", "/");
      if (!file?.endsWith("/src/index.css")) return null;
      return code.replace("/* @earshot-theme */", themeBlock());
    },
    transformIndexHtml(html) {
      return html
        .replaceAll("__BRAND__", tokens.brand.displayName)
        .replaceAll("__THEME__", tokens.color.paper);
    },
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const url = req.url?.split("?")[0];
        if (url !== "/favicon.svg") return next();
        res.setHeader("Content-Type", "image/svg+xml");
        fs.createReadStream(path.join(designDir, "favicon.svg")).pipe(res);
      });
    },
    configurePreviewServer(server) {
      server.middlewares.use((req, res, next) => {
        const url = req.url?.split("?")[0];
        if (url !== "/favicon.svg") return next();
        res.setHeader("Content-Type", "image/svg+xml");
        fs.createReadStream(path.join(designDir, "favicon.svg")).pipe(res);
      });
    },
    generateBundle() {
      this.emitFile({
        type: "asset",
        fileName: "favicon.svg",
        source: fs.readFileSync(path.join(designDir, "favicon.svg")),
      });
    },
  };
}

export default defineConfig({
  plugins: [earshotTokens(), react(), tailwindcss()],
  resolve: {
    alias: { "@": path.resolve(root, "src") },
  },
  server: {
    fs: { allow: [path.resolve(root, "..")] },
  },
});
