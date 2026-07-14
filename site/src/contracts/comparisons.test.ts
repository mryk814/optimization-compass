import { describe, expect, test } from "vitest";

import { parseComparisonIndex } from "./comparisons";

const payload = {
  contract_version: "1.0.0",
  dataset_version: "0.3.0",
  comparisons: [
    {
      comparison_id: "COMPARE_GRADIENT_FAMILY",
      preset_id: "elongated-valley",
      title_ja: "一次法の軌跡比較",
      title_en: "First-order trajectory comparison",
      objective_id: "OBJECTIVE_QUADRATIC_2D",
      objective_expression: "f(x, y) = 100x² + y²",
      initial_point: [-1.6, 1.6],
      budget: 40,
      stopping: "同じ評価予算で停止",
      fairness_note: "同じ初期点・目的関数・評価予算で同期する。",
      caveat: "このpresetだけで一般的な優劣は判断しない。",
      comparability: "comparable_with_caveat",
      synchronization: "oracle_evaluations",
      artifact_kind: "executable_trace",
      renderer_families: ["continuous_trajectory", "generic_metric_history"],
      members: [
        {
          method_id: "M_GRADIENT_DESCENT",
          trace_id: "gradient_descent-quadratic",
          label_ja: "勾配降下法",
          label_en: "Gradient Descent",
          parameters: { learning_rate: 0.003 },
        },
      ],
    },
  ],
};

describe("explanatory comparison contract", () => {
  test("parses the two authored renderer families without inventing a universal renderer", () => {
    const parsed = parseComparisonIndex(payload);

    expect(parsed.comparisons[0].renderer_families).toEqual([
      "continuous_trajectory",
      "generic_metric_history",
    ]);
    expect(parsed.comparisons[0].members[0].label_ja).toBe("勾配降下法");
  });

  test("rejects an undeclared renderer family", () => {
    expect(() => parseComparisonIndex({
      ...payload,
      comparisons: [{ ...payload.comparisons[0], renderer_families: ["universal"] }],
    })).toThrow(/renderer families/u);
  });
});
