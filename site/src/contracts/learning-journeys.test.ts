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
  });

  test("rejects cross-version journeys", () => {
    const changed = structuredClone(rawJourneys);
    changed.journeys[0].dataset_version = "other";
    expect(() => parseLearningJourneyIndex(changed)).toThrow(/dataset version/u);
  });
});
