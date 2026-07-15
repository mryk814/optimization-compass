import { describe, expect, test } from "vitest";

import rawSiteData from "../../public/data/recommendation/site-data.json";
import { parseSiteData } from "./site-data";

describe("SiteData boundary", () => {
  test("accepts the generated complete contract", () => {
    const data = parseSiteData(rawSiteData, rawSiteData.dataset_version);
    expect(data.questions).toHaveLength(12);
    expect(data.rules).toHaveLength(78);
    expect(data.questions[0].choices[2]).toEqual({
      value: "binary",
      label_ja: "0-1",
      label_en: "Binary",
    });
  });

  test("rejects incompatible contracts and datasets", () => {
    expect(() => parseSiteData({ contract_version: "1.0.0" })).toThrow(/contract/i);
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

  test("rejects duplicate feature values and non-integer ordering metadata", () => {
    const duplicateValue = structuredClone(rawSiteData);
    duplicateValue.feature_values.push(duplicateValue.feature_values[0]);
    expect(() => parseSiteData(duplicateValue)).toThrow(/Duplicate feature value/u);

    const fractionalSequence = structuredClone(rawSiteData);
    fractionalSequence.questions[0].sequence = 1.5;
    expect(() => parseSiteData(fractionalSequence)).toThrow(/sequence.*integer/u);

    const zeroSequence = structuredClone(rawSiteData);
    zeroSequence.questions[0].sequence = 0;
    expect(() => parseSiteData(zeroSequence)).toThrow(/sequence.*at least 1/u);

    const fractionalSortOrder = structuredClone(rawSiteData);
    fractionalSortOrder.feature_values[0].sort_order = 1.5;
    expect(() => parseSiteData(fractionalSortOrder)).toThrow(/sort_order.*integer/u);
  });
});
