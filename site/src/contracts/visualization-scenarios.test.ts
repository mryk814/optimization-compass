import { describe, expect, test } from "vitest";

import fixture from "./visualization-scenarios.fixture.json";
import { parseVisualizationScenarioIndex } from "./visualization-scenarios";

describe("VisualizationScenario parser", () => {
  test("parses the shared executable simplex fixture exactly", () => {
    const parsed = parseVisualizationScenarioIndex(fixture);

    expect(parsed.scenarios[0].artifact.renderer_family).toBe("simplex_geometry");
    expect(parsed.scenarios[0].lesson.limitations_ja).toContain("教育用");
  });

  test("rejects unknown renderer families and envelope fields", () => {
    const scenario = fixture.scenarios[0];
    expect(() => parseVisualizationScenarioIndex({
      ...fixture,
      scenarios: [{
        ...scenario,
        artifact: { ...scenario.artifact, renderer_family: "universal" },
      }],
    })).toThrow(/renderer_family/u);
    expect(() => parseVisualizationScenarioIndex({ ...fixture, renderer_registry: {} })).toThrow(/unknown/u);
  });
});
