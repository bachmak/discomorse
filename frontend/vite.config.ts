import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

const BACKEND = "http://localhost:8000";
const PRESENTATION = "http://localhost:8137";
const API_PREFIX = /^\/api/;
const PRESENTATION_PREFIX = /^\/presentation/;

export default defineConfig({
  plugins: [
    react(),
    // The presentation is served by Caddy, not by this bundle, so the app shell
    // must not swallow its navigations.
    VitePWA({
      registerType: "autoUpdate",
      workbox: { navigateFallbackDenylist: [PRESENTATION_PREFIX] },
    }),
  ],
  server: {
    proxy: {
      "/api": {
        target: BACKEND,
        changeOrigin: true,
        rewrite: (path) => path.replace(API_PREFIX, ""),
      },
      "/ws": { target: BACKEND, ws: true },
      "/presentation": {
        target: PRESENTATION,
        rewrite: (path) => path.replace(PRESENTATION_PREFIX, "") || "/",
      },
    },
  },
});
