import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const API_TARGET = "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/auth": API_TARGET,
      "/visits": API_TARGET,
      "/insights": API_TARGET,
      "/workers": API_TARGET,
      "/media": API_TARGET,
      "/health": API_TARGET,
    },
  },
});
