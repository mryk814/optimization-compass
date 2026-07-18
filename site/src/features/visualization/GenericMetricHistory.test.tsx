import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import type { AlgorithmTrace } from "../../contracts/trace";
import { algorithmTraceFixture, traceFrameFixture } from "../../contracts/trace.fixtures";
import { GenericMetricHistory } from "./GenericMetricHistory";

function metricTrace(traceId: string, methodId: string, values: number[]): AlgorithmTrace {
  return {
    ...(algorithmTraceFixture as AlgorithmTrace),
    trace_id: traceId,
    method_id: methodId,
    evaluation_budget: 12,
    frames: values.map((value, index) => ({
      ...traceFrameFixture,
      frame_index: index,
      iteration: index,
      oracle_evaluations: index + 1,
      elapsed_steps: index,
      elapsed_time_ms: index * 100,
      metrics: [{
        metric_id: "residual_norm",
        label_ja: "残差norm",
        label_en: "Residual norm",
        value,
        unit: "response",
      }],
    })) as AlgorithmTrace["frames"],
  };
}

describe("GenericMetricHistory", () => {
  test("aligns multiple traces on one oracle-evaluation axis with a text alternative", () => {
    render(
      <GenericMetricHistory
        budget={12}
        evaluation={2}
        labels={{ trf: "TRF", lm: "LM" }}
        metricIds={["residual_norm"]}
        traces={[metricTrace("trf", "M_TRUST_REGION_REFLECTIVE", [2, 0.5]), metricTrace("lm", "M_LEVENBERG_MARQUARDT", [2, 0.25])]}
      />,
    );

    expect(screen.getByRole("heading", { level: 2, name: /指標の履歴/u })).toBeVisible();
    expect(screen.getByRole("img", { name: "残差normを評価回数ごとに比較" })).toBeVisible();
    expect(screen.getAllByText(/TRF/)[0]).toBeVisible();
    expect(screen.getAllByText(/LM/)[0]).toBeVisible();
    expect(screen.getByText(/0.50000 response/u)).toBeVisible();
    expect(screen.getByText(/0.25000 response/u)).toBeVisible();
  });
});
