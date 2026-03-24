/// <reference types="vitest" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
  },
  server: {
    proxy: {
      "/gateway-ws": {
        target: "ws://localhost:18790",
        ws: true,
      },
    },
  },
});
