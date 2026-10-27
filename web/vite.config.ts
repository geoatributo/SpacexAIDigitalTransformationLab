import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/chat": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000",
      "/questions": "http://127.0.0.1:8000",
      "/results": "http://127.0.0.1:8000",
      "/run": "http://127.0.0.1:8000",
      "/evaluations": "http://127.0.0.1:8000",
      "/session": "http://127.0.0.1:8000",
      "/dashboard": "http://127.0.0.1:8000",
      "/human": "http://127.0.0.1:8000",
      "/blind": "http://127.0.0.1:8000",
      "/metrics": "http://127.0.0.1:8000",
    },
  },
});
