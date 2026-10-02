import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  base: "/optimization-compass/",
  plugins: [react()],
  // Existing tailnet-only Serve route for temporary phone review.
  server: { allowedHosts: ["desktop-55avlhd.tail4d1e1e.ts.net"] },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
  },
});
