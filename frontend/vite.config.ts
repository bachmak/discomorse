import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

const BACKEND = "http://localhost:8000";
const API_PREFIX = /^\/api/;

export default defineConfig({
  plugins: [react(), VitePWA({ registerType: "autoUpdate" })],
  server: {
    proxy: {
      "/api": {
        target: BACKEND,
        changeOrigin: true,
        rewrite: (path) => path.replace(API_PREFIX, ""),
      },
      "/ws": { target: BACKEND, ws: true },
    },
  },
});
