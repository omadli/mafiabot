/// <reference types="vitest" />
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig(({ mode }) => {
  // Load env from frontend dir AND root (../) so a single .env at the
  // repo root drives both backend and frontend. Root values win.
  const localEnv = loadEnv(mode, process.cwd(), "");
  const rootEnv = loadEnv(mode, path.resolve(process.cwd(), ".."), "");
  const env = { ...localEnv, ...rootEnv };

  const backendPort = env.BACKEND_PORT || "8002";
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
      // Static vendor split keeps the per-page chunks lean. React + router
      // ship together because lazy modules pull them transitively anyway.
      rollupOptions: {
        output: {
          manualChunks: {
            "vendor-react": ["react", "react-dom", "react-router-dom"],
            "vendor-data": ["@tanstack/react-query", "axios", "zustand"],
            "vendor-i18n": ["i18next", "react-i18next"],
          },
        },
      },
      chunkSizeWarningLimit: 600,
    },
    test: {
      globals: true,
      environment: "jsdom",
      setupFiles: ["./src/test/setup.ts"],
      css: false,
    },
  };
});
