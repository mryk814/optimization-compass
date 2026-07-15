import { describe, expect, it } from "vitest";

import fixture from "../../public/data/learning-graph.json";
import { parseLearningGraphIndex, searchTerminology } from "./learning-graph";

describe("learning graph contract", () => {
  it("loads the canonical tranche and resolves aliases", () => {
    const index = parseLearningGraphIndex(fixture);
    expect(index.edges.length).toBeGreaterThanOrEqual(40);
    expect(index.aliases.length).toBeGreaterThanOrEqual(30);
    expect(searchTerminology(index, "ベイズ最適化")[0].target_id).toBe("M_BAYESIAN_OPT_GP");
  });

  it("keeps acronym collisions as disambiguated candidates", () => {
    const index = parseLearningGraphIndex(fixture);
    expect(new Set(searchTerminology(index, "IP").map((row) => row.target_id))).toEqual(new Set([
      "M_INTERIOR_POINT_NLP", "MF_DISCRETE_EXACT",
    ]));
    expect(searchTerminology(index, "IP").every((row) => row.disambiguation_note)).toBe(true);
  });
});
