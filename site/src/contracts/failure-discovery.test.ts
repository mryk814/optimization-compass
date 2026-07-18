import raw from "../../public/data/failure-discovery.json";
import { describe, expect, test } from "vitest";
import { parseFailureDiscoveryIndex } from "./failure-discovery";

describe("failure discovery contract", () => {
  test("parses structured failures and Case-specific exclusions together", () => {
    const index = parseFailureDiscoveryIndex(raw);
    expect(index.summary).toEqual({
      total_entries: 25,
      structured_failure_count: 12,
      case_exclusion_count: 13,
      entries_with_scenarios: 11,
    });
    expect(index.entries.some((entry) => entry.entry_kind === "case_exclusion")).toBe(true);
    expect(index.entries.filter((entry) => entry.entry_kind === "structured_failure").every((entry) => entry.diagnostics.length > 0)).toBe(true);
  });
});
