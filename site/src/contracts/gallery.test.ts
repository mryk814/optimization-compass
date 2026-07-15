import { describe, expect, test } from "vitest";

import raw from "../../public/data/gallery.json";
import { parseGalleryIndex } from "./gallery";

describe("gallery contract", () => {
  test("parses ten cases with explicit method dispositions", () => {
    const index = parseGalleryIndex(raw);
    const canonicalIds = new Set(["EC013", "EC017", "EC019", "EC020", "EC025", "EC026"]);

    expect(index.cases).toHaveLength(10);
    expect(index.cases.every((item) => item.candidate_method_ids.length > 0)).toBe(true);
    expect(index.cases.every((item) => item.conditional_methods.length > 0)).toBe(true);
    expect(index.cases.every((item) => item.excluded_methods.length > 0)).toBe(true);
    expect(index.cases.filter((item) => canonicalIds.has(item.case_id))).toHaveLength(6);
    expect(
      index.cases
        .filter((item) => canonicalIds.has(item.case_id))
        .every((item) => Object.keys(item.question_answers).length === 12),
    ).toBe(true);
  });
});
