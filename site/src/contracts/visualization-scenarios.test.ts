import { describe, expect, test } from "vitest";

import fixture from "./visualization-scenarios.fixture.json";
import generated from "../../public/data/visualization-scenarios.json";
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

  test("parses BO scenarios from the single generated scenario authority", () => {
    const parsed = parseVisualizationScenarioIndex(generated);
    const boScenarios = parsed.scenarios.filter(
      (scenario) => scenario.artifact.renderer_family === "surrogate_uncertainty",
    );

    expect(boScenarios).toHaveLength(4);
    expect(boScenarios.filter((scenario) => scenario.purpose === "mechanism")).toHaveLength(1);
    expect(boScenarios.every((scenario) => scenario.artifact.payload_path.startsWith("visualizations/"))).toBe(true);
  });
});
