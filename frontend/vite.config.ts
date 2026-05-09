import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const backendPort = env.BACKEND_PORT || "8001";
  const backendURL = `http://localhost:${backendPort}`;

  return {
    plugins: [react()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
        "@admin": path.resolve(__dirname, "./src/modules/admin"),
        "@webapp": path.resolve(__dirname, "./src/modules/webapp"),
        "@shared": path.resolve(__dirname, "./src/shared"),
      },
    },
    server: {
      host: "0.0.0.0",
      port: 5173,
      proxy: {
        "/api": {
          target: backendURL,
          changeOrigin: true,
        },
        "/health": {
          target: backendURL,
          changeOrigin: true,
        },
        "/ws": {
          target: backendURL.replace("http", "ws"),
          ws: true,
          changeOrigin: true,
        },
      },
    },
    build: {
      outDir: "dist",
      sourcemap: false,
      target: "es2022",
    },
  };
});
