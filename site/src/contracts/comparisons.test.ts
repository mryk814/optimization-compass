import rawComparisons from "../../public/data/comparisons.json";
import { describe, expect, test } from "vitest";

import { parseComparisonIndex } from "./comparisons";

describe("case-bound comparison contract", () => {
  test("parses multiple modes and renderer families", () => {
    const parsed = parseComparisonIndex(rawComparisons);

    expect(new Set(parsed.comparisons.map((comparison) => comparison.mode))).toEqual(new Set([
      "method_contrast", "parameter_sensitivity", "initial_condition_sensitivity", "failure_contrast", "result_tradeoff", "strategy_contrast",
    ]));
    expect(new Set(parsed.comparisons.flatMap((comparison) => (
      comparison.members.map((member) => member.artifact.renderer_family)
    )))).toEqual(new Set([
      "continuous_trajectory", "feasible_region", "generic_metric_history", "pareto_front", "search_tree", "simplex_geometry", "surrogate_uncertainty", "field_evolution",
    ]));
  });

  test("keeps the BO comparison non-ranking and synchronized", () => {
    const parsed = parseComparisonIndex(rawComparisons);
    const comparison = parsed.comparisons.find(
      (item) => item.comparison_id === "COMPARE_BO_ACQUISITION_NOISE_BASELINE",
    )!;

    expect(comparison.comparability).toBe("contrast_only");
    expect(comparison.ranking_eligible).toBe(false);
    expect(comparison.synchronization_axis).toBe("oracle_evaluations");
    expect(new Set(comparison.members.map((member) => member.role))).toEqual(new Set([
      "reference_acquisition", "acquisition_sensitivity", "noise_sensitivity", "random_baseline",
    ]));
  });

  test("keeps initial-simplex sensitivity as a non-ranking geometry comparison", () => {
    const parsed = parseComparisonIndex(rawComparisons);
    const parsedComparison = parsed.comparisons.find(
      (comparison) => comparison.comparison_id === "COMPARE_NELDER_MEAD_INITIAL_SIMPLEX",
    )!;

    expect(parsedComparison.mode).toBe("initial_condition_sensitivity");
    expect(parsedComparison.ranking_eligible).toBe(false);
    expect(parsedComparison.budget).toEqual({ metric: "oracle_evaluations", value: 80 });
    expect(new Set(parsedComparison.members.map((member) => member.artifact.renderer_family))).toEqual(
      new Set(["simplex_geometry"]),
    );
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
