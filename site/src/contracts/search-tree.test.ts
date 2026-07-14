import { describe, expect, test } from "vitest";

import completeFixture from "../../public/data/search-trees/binary-knapsack-bnb-complete.json";
import budgetFixture from "../../public/data/search-trees/binary-knapsack-bnb-budget.json";
import indexFixture from "../../public/data/search-trees/index.json";
import {
  parseSearchTreeArtifact,
  parseSearchTreeFramePayload,
  parseSearchTreeIndex,
} from "./search-tree";

describe("search-tree contracts", () => {
  test("parses generated mechanism and failure-contrast artifacts exactly", () => {
    const complete = parseSearchTreeArtifact(completeFixture);
    const budget = parseSearchTreeArtifact(budgetFixture);
    const index = parseSearchTreeIndex(indexFixture);
    expect(complete.trace.terminal_status).toBe("completed");
    expect(parseSearchTreeFramePayload(complete.trace.frames.at(-1)!.payload).terminal_state).toBe("optimality_proven");
    expect(budget.trace.terminal_status).toBe("budget_exhausted");
    expect(parseSearchTreeFramePayload(budget.trace.frames.at(-1)!.payload).absolute_gap).toBe(2);
    expect(index.artifacts.map((item) => item.scenario_id)).toEqual([
      "SCENARIO_BINARY_KNAPSACK_BNB_COMPLETE",
      "SCENARIO_BINARY_KNAPSACK_BNB_BUDGET",
    ]);
  });

  test("rejects unknown fields and renderer/version mismatches without fallback", () => {
    expect(() => parseSearchTreeArtifact({ ...completeFixture, legacy: true })).toThrow(/unknown fields/u);
    expect(() => parseSearchTreeArtifact({ ...completeFixture, renderer_family: "method-specific" })).toThrow(/search_tree/u);
    const final = completeFixture.trace.frames.at(-1)!;
    expect(() => parseSearchTreeFramePayload({ ...final.payload, absolute_gap: 1 })).toThrow(/gap/iu);
  });
});
