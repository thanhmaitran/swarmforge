import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// The API runs on :8000 during development; proxying avoids CORS and keeps WebSocket URLs relative.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
      "/ws": { target: "ws://localhost:8000", ws: true },
    },
  },
  test: { environment: "node" },
});
