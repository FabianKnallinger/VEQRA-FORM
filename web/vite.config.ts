import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Entwicklungsserver: API-Anfragen an die lokale VEQRA Bridge weiterleiten
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8899",
      "/ws": { target: "ws://127.0.0.1:8899", ws: true },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: false,
  },
});
