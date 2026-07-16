import { describe, expect, test } from "vitest";

import rawJourneys from "../../public/data/learning-journeys.json";
import { parseLearningJourneyIndex } from "./learning-journeys";

describe("LearningJourney parser", () => {
  test("parses the generated case-rooted journeys", () => {
    const index = parseLearningJourneyIndex(rawJourneys);
    const pilot = index.journeys.find((journey) => journey.journey_id === "constrained-design");
    expect(pilot?.case_id).toBe("constrained-design");
    expect(pilot?.scenarios[0]?.scenario_id).toBe("SCENARIO_CONSTRAINED_DISK");
    expect(pilot?.scenarios[0]?.canonical_url).toBe("/theater/learning/SCENARIO_CONSTRAINED_DISK");
    expect(pilot?.status).toBe("partial");
    expect(index.summary.target_complete_journeys).toBe(5);
    expect(index.summary.total_journeys).toBe(index.journeys.length);
    expect(index.assessments.find((item) => item.journey_id === "constrained-design")?.missing_dimensions).toEqual(["alternate_scenario"]);
    expect(index.orphan_assets.some((item) => item.policy === "warning")).toBe(true);
  });

  test("rejects cross-version journeys", () => {
    const changed = structuredClone(rawJourneys);
    changed.journeys[0].dataset_version = "other";
    expect(() => parseLearningJourneyIndex(changed)).toThrow(/dataset version/u);
  });

  test("rejects a complete journey with a missing dimension", () => {
    const changed = structuredClone(rawJourneys);
    const journey = changed.journeys.find((item) => item.journey_id === "constrained-design");
    const assessment = changed.assessments.find((item) => item.journey_id === "constrained-design");
    if (!journey || !assessment) throw new Error("Expected constrained-design fixture.");
    journey.status = "complete";
    journey.completion_reasons = [];
    assessment.status = "complete";
    expect(() => parseLearningJourneyIndex(changed)).toThrow(/missing dimensions/u);
  });

  test("rejects mismatched assessment reasons", () => {
    const changed = structuredClone(rawJourneys);
    changed.journeys[0].completion_reasons = ["unrelated_reason"];
    expect(() => parseLearningJourneyIndex(changed)).toThrow(/completion reasons/u);
  });
});
