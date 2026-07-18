import { describe, expect, test } from "vitest";

import rawJourneys from "../../public/data/learning-journeys.json";
import { parseLearningJourneyIndex } from "./learning-journeys";

describe("LearningJourney parser", () => {
  test("parses the generated case-rooted journeys", () => {
    const index = parseLearningJourneyIndex(rawJourneys);
    const pilot = index.journeys.find((journey) => journey.journey_id === "constrained-design");
    expect(pilot?.case_id).toBe("constrained-design");
    expect(pilot?.scenarios.find((scenario) => scenario.role === "primary")?.scenario_id)
      .toBe("SCENARIO_CONSTRAINED_DISK_FEASIBLE_PATH");
    expect(pilot?.scenarios.find((scenario) => scenario.role === "primary")?.canonical_url)
      .toBe("/theater/learning/SCENARIO_CONSTRAINED_DISK_FEASIBLE_PATH");
    expect(pilot?.scenarios.find((scenario) => scenario.role === "failure_contrast")?.scenario_id)
      .toBe("SCENARIO_CONSTRAINED_DISK");
    expect(pilot?.status).toBe("complete");
    expect(index.summary.target_complete_journeys).toBe(5);
    expect(index.summary.total_journeys).toBe(index.journeys.length);
    expect(index.summary.status_counts).toEqual({ complete: 5, partial: 10, draft: 0 });
    const parameterEstimation = index.journeys.find((journey) => journey.journey_id === "EC013");
    expect(parameterEstimation?.status).toBe("complete");
    expect(parameterEstimation?.scenarios.find((scenario) => scenario.role === "primary")?.scenario_id)
      .toBe("SCENARIO_EXPONENTIAL_FIT_TRF");
    expect(parameterEstimation?.comparisons[0]?.comparison_id)
      .toBe("COMPARE_EXPONENTIAL_FIT_SOLVER_CONDITIONS");
    const discreteAllocation = index.journeys.find(
      (journey) => journey.journey_id === "budget-allocation",
    );
    expect(discreteAllocation?.status).toBe("complete");
    expect(Object.fromEntries(
      discreteAllocation?.scenarios.map((scenario) => [scenario.role, scenario.scenario_id]) ?? [],
    )).toEqual({
      failure_contrast: "SCENARIO_BINARY_KNAPSACK_BNB_BUDGET",
      primary: "SCENARIO_BINARY_KNAPSACK_BNB_COMPLETE",
    });
    expect(discreteAllocation?.comparisons[0]?.comparison_id)
      .toBe("COMPARE_KNAPSACK_BNB_BUDGET");
    expect(index.assessments.find((item) => item.journey_id === "constrained-design")?.missing_dimensions).toEqual([]);
    expect(index.orphan_assets.some((item) => item.policy === "warning")).toBe(true);
  });

  test("rejects cross-version journeys", () => {
    const changed = structuredClone(rawJourneys);
    changed.journeys[0].dataset_version = "other";
    expect(() => parseLearningJourneyIndex(changed)).toThrow(/dataset version/u);
  });

  test("rejects a complete journey with a missing dimension", () => {
    const changed = structuredClone(rawJourneys);
    const journey = changed.journeys.find((item) => item.status === "partial");
    const assessment = changed.assessments.find((item) => item.journey_id === journey?.journey_id);
    if (!journey || !assessment) throw new Error("Expected a partial journey fixture.");
    journey.status = "complete";
    journey.completion_reasons = [];
    assessment.status = "complete";
    expect(() => parseLearningJourneyIndex(changed)).toThrow(/incomplete|missing dimensions/u);
  });

  test("rejects mismatched assessment reasons", () => {
    const changed = structuredClone(rawJourneys);
    changed.journeys[0].completion_reasons = ["unrelated_reason"];
    expect(() => parseLearningJourneyIndex(changed)).toThrow(/completion reasons/u);
  });
});
