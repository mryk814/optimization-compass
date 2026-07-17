import rawComparisons from "../../public/data/comparisons.json";
import { describe, expect, test } from "vitest";

import { parseComparisonIndex } from "./comparisons";

describe("case-bound comparison contract", () => {
  test("parses multiple modes and renderer families", () => {
    const parsed = parseComparisonIndex(rawComparisons);

    expect(new Set(parsed.comparisons.map((comparison) => comparison.mode))).toEqual(new Set([
      "method_contrast", "parameter_sensitivity", "failure_contrast", "result_tradeoff",
    ]));
    expect(new Set(parsed.comparisons.flatMap((comparison) => (
      comparison.members.map((member) => member.artifact.renderer_family)
    )))).toEqual(new Set([
      "continuous_trajectory", "feasible_region", "generic_metric_history", "pareto_front",
    ]));
  });

  test("rejects an unfair member budget", () => {
    const payload = structuredClone(rawComparisons);
    payload.comparisons[0].members[0].budget.value += 1;

    expect(() => parseComparisonIndex(payload)).toThrow(/aligned budget/u);
  });

  test("rejects an incompatible artifact kind", () => {
    const payload = structuredClone(rawComparisons);
    const comparison = payload.comparisons.find((item) => item.mode === "failure_contrast")!;
    comparison.members[0].artifact.artifact_kind = "result_visualization";

    expect(() => parseComparisonIndex(payload)).toThrow(/incompatible artifact kind/u);
  });

  test("keeps derived identity explicit", () => {
    const payload = structuredClone(rawComparisons);
    const comparison = payload.comparisons.find((item) => item.identity_status === "derived")!;
    comparison.canonical_comparison_id = comparison.comparison_id;

    expect(() => parseComparisonIndex(payload)).toThrow(/canonical identity/u);
  });
});
