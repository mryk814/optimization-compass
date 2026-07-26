import raw from "../../public/data/failure-discovery.json";
import { describe, expect, test } from "vitest";
import { parseFailureDiscoveryIndex } from "./failure-discovery";

describe("failure discovery contract", () => {
  test("parses structured failures and Case-specific exclusions together", () => {
    const index = parseFailureDiscoveryIndex(raw);
    expect(index.summary).toEqual({
      total_entries: index.entries.length,
      structured_failure_count: index.entries.filter(
        (entry) => entry.entry_kind === "structured_failure",
      ).length,
      case_exclusion_count: index.entries.filter(
        (entry) => entry.entry_kind === "case_exclusion",
      ).length,
      entries_with_scenarios: index.entries.filter(
        (entry) => entry.scenario_ids.length > 0,
      ).length,
    });
    expect(index.entries.some((entry) =>
      entry.entry_kind === "case_exclusion" &&
      entry.case_id === "traffic-signal-tradeoff")).toBe(true);
    expect(index.entries.some((entry) => entry.entry_kind === "case_exclusion")).toBe(true);
    expect(index.entries.filter((entry) => entry.entry_kind === "structured_failure").every((entry) => entry.diagnostics.length > 0)).toBe(true);
  });
});
