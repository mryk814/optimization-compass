import { describe, expect, test } from "vitest";

import entityLinks from "../../../public/data/entity-links.json";
import scenarios from "../../../public/data/visualization-scenarios.json";
import { parseEntityLinkIndex } from "../../contracts/entity-links";
import { parseVisualizationScenarioIndex } from "../../contracts/visualization-scenarios";
import { buildTheaterCatalog, validatePublicScenarioReachability } from "./scenario-catalog";

describe("scenario catalog", () => {
  test("makes all 18 public scenarios reachable across every renderer family", () => {
    const catalog = buildTheaterCatalog(
      parseVisualizationScenarioIndex(scenarios).scenarios,
      parseEntityLinkIndex(entityLinks),
    );
    expect(catalog).toHaveLength(18);
    expect(new Set(catalog.map((entry) => entry.scenario.artifact.renderer_family))).toEqual(new Set([
      "simplex_geometry", "continuous_trajectory", "search_tree", "surrogate_uncertainty",
      "feasible_region", "pareto_front",
    ]));
    expect(catalog.every((entry) => entry.route.startsWith("/"))).toBe(true);
  });

  test("rejects an unreachable public scenario", () => {
    const catalog = buildTheaterCatalog(
      parseVisualizationScenarioIndex(scenarios).scenarios,
      parseEntityLinkIndex(entityLinks),
    );
    expect(() => validatePublicScenarioReachability([
      { ...catalog[0], route: "" },
      ...catalog.slice(1),
    ])).toThrow(/unreachable/u);
  });
});
