import { describe, expect, test } from "vitest";

import rawSiteData from "../../../public/data/recommendation/site-data.json";
import { parseSiteData } from "../../contracts/site-data";
import { recommend } from "./recommend";

const data = parseSiteData(rawSiteData);

describe("offline recommendation evaluator", () => {
  test("matches alternative-first, domain gate, and exclusion precedence", () => {
    const result = recommend(data, {
      Q02: ["explicit_algebraic"],
      Q04: ["none"],
      Q05: ["autodiff", "not_differentiable"],
      Q09: ["local_is_fine"],
    });

    expect(result.alternatives_first.map((item) => item.entity_id)).toContain("ALT_SPECIALIZED");
    expect(result.excluded_methods.map((item) => item.entity_id)).toContain("M_BFGS");
    expect(result.first_choices.map((item) => item.entity_id)).not.toContain("M_BFGS");
    expect(result.warnings).toContain(
      "一部の手法に支持規則と除外規則が同時に一致しました。除外を優先しています。",
    );
  });

  test("keeps canonical unknown as data and emits its follow-up trace", () => {
    const result = recommend(data, { Q02: ["unknown"] });
    expect(result.answered_question_count).toBe(1);
    expect(result.followups.map((item) => item.question_id)).toEqual(["Q02"]);
    expect(result.trace.map((item) => item.rule_id)).toEqual(["R012"]);
  });

  test.each([
    [{ Q01: ["binary", "continuous"] }, /single_choice/u],
    [{ Q01: ["binary", "binary"] }, /duplicate/u],
    [{ Q01: [] }, /non-empty/u],
    [{ Q07: ["unknown", "small_noise"] }, /sole value/u],
    [{ Q01: ["unknown"] }, /invalid answers/u],
  ] as const)("rejects non-canonical answer shapes %#", (answers, error) => {
    expect(() => recommend(data, answers)).toThrow(error);
  });

  test("rejects an internally incompatible dataset", () => {
    expect(() => recommend(data, {}, { expected_dataset_version: "9.9.9" })).toThrow(
      /dataset mismatch/u,
    );
  });
});
