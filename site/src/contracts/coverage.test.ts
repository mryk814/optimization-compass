import { describe, expect, test } from "vitest";
import rawCoverage from "../../public/data/coverage.json";
import { parseCoverageReport } from "./coverage";

describe("CoverageReport parser", () => {
  test("parses all four statuses and the complete inventory exactly", () => {
    const report = parseCoverageReport(rawCoverage);
    expect(Object.keys(report.summary.status_counts)).toEqual([
      "available", "partial", "missing", "not_applicable",
    ]);
    expect(report.subjects).toHaveLength(
      Object.values(report.summary.subject_counts).reduce((total, count) => total + count, 0),
    );
    expect(report.priorities).toHaveLength(6);
  });

  test("routes every expected learning artifact to its teaching surface", () => {
    const report = parseCoverageReport(rawCoverage);
    expect(report.summary.status_counts).toMatchObject({
      available: 11,
      partial: 0,
      missing: 0,
    });
    expect(report.expectations.find(({ expectation_id }) =>
      expectation_id === "COV_GD_COMPARISON")).toMatchObject({
      status: "available",
      route_ids: ["/compare/first-order"],
    });
    expect(report.expectations.find(({ expectation_id }) =>
      expectation_id === "COV_NM_SENSITIVITY_NA")).toMatchObject({
      status: "available",
      route_ids: ["/theater/nelder-mead"],
    });
  });

  test("rejects unknown fields and implicit baselines", () => {
    expect(() => parseCoverageReport({ ...rawCoverage, coverage_percent: 42 })).toThrow(/unknown/u);
    expect(() => parseCoverageReport({
      ...rawCoverage,
      summary: { ...rawCoverage.summary, baseline: "0.2.0" },
    })).toThrow(/baseline/u);
  });

  test("scope is optional, counted, and strict", () => {
    const { scope: _scope, ...withoutScope } = rawCoverage;
    expect(parseCoverageReport(withoutScope).scope).toBeNull();
    const parsed = parseCoverageReport(rawCoverage);
    expect(parsed.scope?.units.knowledge_topic.axes.experience.eligible).toBe(0);
    expect(() => parseCoverageReport({
      ...rawCoverage,
      scope: { ...rawCoverage.scope, overall_percent: 40 },
    })).toThrow(/unknown/u);
  });
});
