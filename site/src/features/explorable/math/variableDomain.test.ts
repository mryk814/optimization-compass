import { describe, expect, it } from "vitest";

import { solveDomains, type Domain } from "./variableDomain";

// Reference values come from an exact-rational script (fractions.Fraction vertex enumeration,
// a full lattice listing, and closed-form slices), not from this module.
const CASES: Array<{
  d1: Domain; d2: Domain; relaxed: number; best: [number, number]; value: number; gap: number; count: number;
}> = [
  { d1: "continuous", d2: "continuous", relaxed: 21, best: [3, 1.5], value: 21, gap: 0, count: 0 },
  { d1: "continuous", d2: "integer", relaxed: 21, best: [10 / 3, 1], value: 62 / 3, gap: 1 / 3, count: 4 },
  { d1: "continuous", d2: "binary", relaxed: 62 / 3, best: [10 / 3, 1], value: 62 / 3, gap: 0, count: 2 },
  { d1: "integer", d2: "continuous", relaxed: 21, best: [3, 1.5], value: 21, gap: 0, count: 5 },
  { d1: "integer", d2: "integer", relaxed: 21, best: [4, 0], value: 20, gap: 1, count: 13 },
  { d1: "integer", d2: "binary", relaxed: 62 / 3, best: [4, 0], value: 20, gap: 2 / 3, count: 9 },
  { d1: "binary", d2: "continuous", relaxed: 15, best: [1, 2.5], value: 15, gap: 0, count: 2 },
  { d1: "binary", d2: "integer", relaxed: 15, best: [1, 2], value: 13, gap: 2, count: 7 },
  { d1: "binary", d2: "binary", relaxed: 9, best: [1, 1], value: 9, gap: 0, count: 4 },
];

describe("solveDomains", () => {
  for (const row of CASES) {
    it(`${row.d1} x ${row.d2}: optimum ${row.value.toFixed(3)} at ${row.best.join(", ")}`, () => {
      const s = solveDomains(row.d1, row.d2);
      expect(s.relaxedValue).toBeCloseTo(row.relaxed, 9);
      expect(s.best[0]).toBeCloseTo(row.best[0], 9);
      expect(s.best[1]).toBeCloseTo(row.best[1], 9);
      expect(s.bestValue).toBeCloseTo(row.value, 9);
      expect(s.gap).toBeCloseTo(row.gap, 9);
      expect(s.candidateCount).toBe(row.count);
    });
  }

  it("the article's three cases: 13 integer plans, 4 binary plans, shapes region / points / points", () => {
    expect(solveDomains("continuous", "continuous").feasible.kind).toBe("region");
    const integer = solveDomains("integer", "integer").feasible;
    const binary = solveDomains("binary", "binary").feasible;
    expect(integer.kind).toBe("points");
    expect(binary.kind).toBe("points");
    expect(integer.kind === "points" ? integer.points.length : 0).toBe(13);
    expect(binary.kind === "points" ? binary.points.length : 0).toBe(4);
    expect(solveDomains("integer", "continuous").feasible.kind).toBe("segments");
  });

  it("a restricted domain never beats a larger one on the same constraints", () => {
    const domains: Domain[] = ["continuous", "integer", "binary"];
    for (const d1 of domains) {
      for (const d2 of domains) {
        const s = solveDomains(d1, d2);
        expect(s.bestValue).toBeLessThanOrEqual(s.relaxedValue + 1e-9);
        expect(s.bestValue).toBeLessThanOrEqual(21 + 1e-9);
      }
    }
  });

  it("flags a fractional optimum only when a continuous variable remains", () => {
    expect(solveDomains("integer", "integer").bestHasFraction).toBe(false);
    expect(solveDomains("binary", "binary").bestHasFraction).toBe(false);
    expect(solveDomains("integer", "continuous").bestHasFraction).toBe(true);
  });
});
