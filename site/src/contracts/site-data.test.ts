import { describe, expect, test } from "vitest";

import rawSiteData from "../../public/data/recommendation/site-data.json";
import { parseSiteData } from "./site-data";

describe("SiteData boundary", () => {
  test("accepts the generated complete contract", () => {
    const data = parseSiteData(rawSiteData, "0.2.0");
    expect(data.questions).toHaveLength(12);
    expect(data.rules).toHaveLength(78);
    expect(data.questions[0].choices[2]).toEqual({
      value: "binary",
      label_ja: "0-1",
      label_en: "Binary",
    });
  });

  test("rejects incompatible contracts and datasets", () => {
    expect(() => parseSiteData({ contract_version: "2.0.0" })).toThrow(/contract/i);
    expect(() => parseSiteData(rawSiteData, "9.9.9")).toThrow(/dataset mismatch/i);
  });

  test("rejects duplicate IDs, broken refs, and unknown actions", () => {
    const duplicate = structuredClone(rawSiteData);
    duplicate.questions.push(duplicate.questions[0]);
    expect(() => parseSiteData(duplicate)).toThrow(/duplicate question/i);

    const broken = structuredClone(rawSiteData);
    broken.rules[0].action_target_ids = ["M_MISSING"];
    expect(() => parseSiteData(broken)).toThrow(/missing target/i);

    const unknownAction = structuredClone(rawSiteData);
    unknownAction.rules[0].action_type = "invent_method";
    expect(() => parseSiteData(unknownAction)).toThrow(/unsupported recommendation action/i);

    const extraField = structuredClone(rawSiteData) as typeof rawSiteData & {
      legacy_rules?: unknown;
    };
    extraField.legacy_rules = [];
    expect(() => parseSiteData(extraField)).toThrow(/extra=legacy_rules/u);
  });
});
