/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/health": { target: "http://localhost:8000" },
      "/ready": { target: "http://localhost:8000" },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/__tests__/setup.ts"],
    css: true,
    coverage: {
      provider: "v8",
      reporter: ["text", "text-summary", "lcov"],
      include: ["src/**/*.{ts,tsx}"],
      exclude: [
        "src/__tests__/**",
        "src/main.tsx",
        "src/vite-env.d.ts",
      ],
      thresholds: {
        // Overall project minimums.
        // Note: v8 counts each useCallback/arrow function inside React
        // components as a separate function entry, inflating the denominator.
        // Lines and statements are the primary quality gate for React code.
        // The static property pattern (e.g. Screen.keypadHandlers = { onDigit: () => {} })
        // creates 22+ placeholder arrow functions that are never called at runtime
        // (immediately replaced when the component renders), further reducing
        // the measurable function coverage percentage.
        lines: 90,
        functions: 48,
        branches: 85,
        statements: 90,
      },
    },
  },
});
