import { defineConfig } from "vitest/config";

export default defineConfig({
  define: {
    "process.env.RUN_RECOMMENDATION_PARITY": JSON.stringify("1"),
  },
  test: {
    environment: "node",
    include: ["src/features/diagnose/recommend.parity.test.ts"],
  },
});
