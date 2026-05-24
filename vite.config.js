import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";

const rootDir = path.dirname(fileURLToPath(import.meta.url));
const runnerRoot = path.resolve(rootDir, "submodules/v86-runner");

export default defineConfig({
  base: process.env.VITE_BASE ?? "./",
  root: rootDir,
  publicDir: path.join(runnerRoot, "public"),
  assetsInclude: ["**/*.md"],
  resolve: {
    alias: {
      "@runner": path.join(runnerRoot, "src"),
      "/src": path.join(runnerRoot, "src"),
    },
  },
  server: {
    port: 5173,
    fs: { allow: [rootDir, runnerRoot] },
    headers: {
      "Cross-Origin-Opener-Policy": "same-origin",
      "Cross-Origin-Embedder-Policy": "require-corp",
    },
  },
  preview: {
    port: 4173,
    headers: {
      "Cross-Origin-Opener-Policy": "same-origin",
      "Cross-Origin-Embedder-Policy": "require-corp",
    },
  },
  build: {
    outDir: path.join(rootDir, "dist"),
    emptyOutDir: true,
    rollupOptions: {
      input: path.join(rootDir, "index.html"),
    },
  },
});
