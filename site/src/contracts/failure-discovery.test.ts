import { describe, expect, test } from "vitest";

import raw from "../../public/data/failure-discovery.json";
import { parseFailureDiscoveryIndex } from "./failure-discovery";

describe("FailureDiscoveryIndex", () => {
  test("keeps structured failures and Case exclusions distinct", () => {
    const index = parseFailureDiscoveryIndex(raw);

    expect(index.summary).toEqual({
      total_entries: 23,
      structured_failure_count: 12,
      case_exclusion_count: 11,
      entries_with_scenarios: 9,
    });
    expect(index.entries.find((item) => item.entry_id === "structured:FM003")).toMatchObject({
      entry_kind: "structured_failure",
      severity: "high",
      failure_mode_id: "FM003",
      case_id: null,
    });
    expect(index.entries.find((item) => item.entry_id === "case:constrained-design:M_BFGS"))
      .toMatchObject({
        entry_kind: "case_exclusion",
        disposition: "excluded",
        severity: "not_applicable",
        case_id: "constrained-design",
        method_ids: ["M_BFGS"],
      });
  });

  test("rejects a Case exclusion that invents severity", () => {
    const copy = structuredClone(raw);
    const entry = copy.entries.find((item) => item.entry_kind === "case_exclusion");
    if (!entry) throw new Error("fixture lacks a Case exclusion");
    entry.severity = "high";

    expect(() => parseFailureDiscoveryIndex(copy)).toThrow(/Case-exclusion semantics/u);
  });
});
