// Configuración de Vite. "npm run dev" abre la vista en :5173 y reenvía /api al backend Flask (:5000).
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: { port: 5173, proxy: { "/api": "http://127.0.0.1:5000" } },
  build: { outDir: "dist", emptyOutDir: true }   // Flask sirve esta carpeta en http://127.0.0.1:5000/
});
