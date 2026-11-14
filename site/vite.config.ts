import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// Every figure's component file is figures/<id>/Figure.tsx, so its lazy chunk would be named
// "Figure" like all the others; name it after the folder instead (figure-<id>-<hash>.js) so the
// network log and e2e routes can tell figures apart.
const FIGURE_COMPONENT = /[\\/]features[\\/]explorable[\\/]figures[\\/]([^\\/]+)[\\/]Figure\.tsx$/u;

export default defineConfig({
  base: "/optimization-compass/",
  plugins: [react()],
  build: {
    rolldownOptions: {
      output: {
        chunkFileNames: (chunk) => {
          const figure = chunk.facadeModuleId ? FIGURE_COMPONENT.exec(chunk.facadeModuleId) : null;
          return figure ? `assets/figure-${figure[1]}-[hash].js` : "assets/[name]-[hash].js";
        },
      },
    },
  },
  // Existing tailnet-only Serve route for temporary phone review.
  server: { allowedHosts: ["desktop-55avlhd.tail4d1e1e.ts.net"] },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
  },
});
