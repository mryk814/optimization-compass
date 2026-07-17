import { describe, expect, test } from "vitest";

import type { ComparisonMember } from "../../contracts/comparisons";
import { firstMemberPerScenario } from "./compare-routes";

describe("comparison Theater routes", () => {
  test("keeps the first routable member when a scenario ID is repeated", () => {
    const reference = {
      member_id: "reference",
      scenario_id: "SCENARIO_SHARED",
      artifact: { artifact_id: "ARTIFACT_PRIMARY" },
    } as ComparisonMember;
    const baseline = {
      member_id: "baseline",
      scenario_id: "SCENARIO_SHARED",
      artifact: { artifact_id: "ARTIFACT_SECONDARY" },
    } as ComparisonMember;

    expect(firstMemberPerScenario([reference, baseline])).toEqual([reference]);
  });
});
