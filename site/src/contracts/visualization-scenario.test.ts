import { describe, expect, test } from "vitest";

import index from "../../public/data/visualizations/index.json";
import scenario from "../../public/data/visualizations/bo-explore-noiseless.json";
import { parseVisualizationScenario, parseVisualizationScenarioIndex } from "./visualization-scenario";

describe("VisualizationScenario contract", () => {
  test("parses the generated common envelope and surrogate payload", () => {
    const parsedIndex = parseVisualizationScenarioIndex(index);
    const parsed = parseVisualizationScenario(scenario);
    expect(parsedIndex.scenarios).toHaveLength(4);
    expect(parsed.payload.renderer_family).toBe("surrogate_uncertainty");
    expect(parsed.payload.frames.at(-1)?.oracle_evaluations).toBe(parsed.payload.evaluation_budget);
    expect(parsed.payload.random_history).toHaveLength(parsed.payload.evaluation_budget);
  });

  test("rejects unknown envelope fields and unsupported renderer families", () => {
    expect(() => parseVisualizationScenario({ ...scenario, legacy: true })).toThrow(/unknown/u);
    expect(() => parseVisualizationScenario({ ...scenario, payload: { ...scenario.payload, renderer_family: "bo_only" } })).toThrow(/unsupported/iu);
  });
});
