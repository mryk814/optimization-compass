import { describe, expect, test } from "vitest";
import rawCoverage from "../../public/data/coverage.json";
import { parseCoverageReport } from "./coverage";

describe("CoverageReport parser", () => {
  test("parses all four statuses and the complete inventory exactly", () => {
    const report = parseCoverageReport(rawCoverage);
    expect(Object.keys(report.summary.status_counts)).toEqual([
      "available", "partial", "missing", "not_applicable",
    ]);
    expect(report.subjects).toHaveLength(165);
    expect(report.priorities).toHaveLength(5);
  });

  test("rejects unknown fields and implicit baselines", () => {
    expect(() => parseCoverageReport({ ...rawCoverage, coverage_percent: 42 })).toThrow(/unknown/u);
    expect(() => parseCoverageReport({
      ...rawCoverage,
      summary: { ...rawCoverage.summary, baseline: "0.2.0" },
    })).toThrow(/baseline/u);
  });
});
