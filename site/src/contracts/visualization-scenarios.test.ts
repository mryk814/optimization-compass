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

    expect(boScenarios).toHaveLength(5);
    expect(boScenarios.filter((scenario) => scenario.purpose === "mechanism")).toHaveLength(2);
    expect(boScenarios.every((scenario) => scenario.artifact.payload_path.startsWith("visualizations/"))).toBe(true);
  });

  test("requires complete lessons and keeps established scenario deep links", () => {
    const parsed = parseVisualizationScenarioIndex(generated);
    const failureOrSensitivity = parsed.scenarios.filter(
      (scenario) => scenario.purpose === "failure_contrast" || scenario.purpose === "sensitivity",
    );

    expect(parsed.contract_version).toBe("1.2.0");
    expect(parsed.scenarios.every((scenario) => scenario.lesson.primary_observables.length > 0)).toBe(true);
    expect(parsed.scenarios.every((scenario) => scenario.lesson.narration_steps[0].milestone_id === "start")).toBe(true);
    expect(failureOrSensitivity.every((scenario) => scenario.lesson.misconception !== null)).toBe(true);
    expect(failureOrSensitivity.every((scenario) => scenario.lesson.failure_signals.length > 0)).toBe(true);
    expect(parsed.scenarios.find((scenario) => scenario.scenario_id === "SCENARIO_NM_QUADRATIC")?.artifact.payload_path)
      .toBe("traces/nelder-mead-quadratic.json");
  });

  test("fails closed on the replaced 1.0.0 scenario contract", () => {
    expect(() => parseVisualizationScenarioIndex({ ...fixture, contract_version: "1.0.0" }))
      .toThrow(/contract_version/u);
  });
});
