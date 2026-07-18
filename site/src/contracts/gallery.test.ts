import { describe, expect, test } from "vitest";

import raw from "../../public/data/gallery.json";
import { parseGalleryIndex } from "./gallery";

describe("gallery contract", () => {
  test("parses twelve cases with explicit method dispositions", () => {
    const index = parseGalleryIndex(raw);
    const canonicalIds = new Set(["EC013", "EC017", "EC019", "EC020", "EC025", "EC026"]);

    expect(index.contract_version).toBe("2.0.0");
    expect(index.cases).toHaveLength(13);
    expect(index.cases.find((item) => item.case_id === "constrained-design")?.visualization_ids)
      .toContain("constrained-disk-feasible-region");
    expect(index.cases.every((item) => item.candidate_methods.length > 0)).toBe(true);
    expect(index.cases.every((item) => item.candidate_methods.every((entry) => entry.reason.length > 0))).toBe(true);
    expect(index.cases.every((item) => item.conditional_methods.length > 0)).toBe(true);
    expect(index.cases.every((item) => item.excluded_methods.length > 0)).toBe(true);
    expect(index.cases.every((item) => item.limitations.length > 0)).toBe(true);
    expect(index.cases.filter((item) => canonicalIds.has(item.case_id))).toHaveLength(6);
    expect(
      index.cases
        .filter((item) => canonicalIds.has(item.case_id))
        .every((item) => Object.keys(item.question_answers).length === 12),
    ).toBe(true);
  });

  test("rejects the replaced v1 shape and empty learning cautions", () => {
    expect(() => parseGalleryIndex({ ...structuredClone(raw), contract_version: "1.0.0" }))
      .toThrow(/Unsupported gallery contract/u);

    const invalid = structuredClone(raw) as unknown as { cases: Array<Record<string, unknown>> };
    invalid.cases[0].limitations = [];
    expect(() => parseGalleryIndex(invalid)).toThrow(/limitations must not be empty/u);

    const legacy = structuredClone(raw) as unknown as { cases: Array<Record<string, unknown>> };
    legacy.cases[0].candidate_method_ids = ["M_CP_SAT"];
    expect(() => parseGalleryIndex(legacy)).toThrow(/candidate_method_ids has been replaced/u);
  });
});
