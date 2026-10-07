import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// O build vai para web/dist, de onde web/servidor.py serve a página.
// Em desenvolvimento (`npm run dev`), as chamadas /api vão para o servidor Python.
export default defineConfig({
  plugins: [react()],
  build: { outDir: "../dist", emptyOutDir: true },
  server: { proxy: { "/api": "http://127.0.0.1:8000" } },
});
