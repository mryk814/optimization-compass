import { describe, expect, it } from "vitest";

import {
  bisectTheta, clippedSum, clippedValues, divideBySum, halfSquaredDistance, projectionTheta, thetaPath, WISH,
} from "./simplexProjection";

// Expected numbers come from scratchpad/motion_numbers.py.
describe("simplex projection by subtract-and-clip", () => {
  it("finds θ = 0.1 and the article's allocation (0.8, 0.2, 0)", () => {
    const theta = projectionTheta(WISH);
    expect(theta).toBeCloseTo(0.1, 12);
    const x = clippedValues(WISH, theta);
    expect(x[0]).toBeCloseTo(0.8, 12);
    expect(x[1]).toBeCloseTo(0.2, 12);
    expect(x[2]).toBe(0);
    expect(clippedSum(WISH, theta)).toBeCloseTo(1, 12);
    expect(halfSquaredDistance(x, WISH)).toBeCloseTo(0.01125, 12);
  });

  it("shows the total before any shift is 1.25 and which activity goes negative first", () => {
    expect(clippedSum(WISH, 0)).toBeCloseTo(1.25, 12);
    expect(clippedValues(WISH, 0.05)[2]).toBe(0);
    expect(clippedSum(WISH, 0.05)).toBeCloseTo(1.1, 12);
    expect(clippedSum(WISH, 0.2)).toBeCloseTo(0.8, 12);
    expect(clippedSum(WISH, 0.9)).toBe(0);
  });

  it("differs from dividing by the total", () => {
    const d = divideBySum(WISH);
    expect(d[0]).toBeCloseTo(0.72, 12);
    expect(d[1]).toBeCloseTo(0.24, 12);
    expect(d[2]).toBeCloseTo(0.04, 12);
    expect(halfSquaredDistance(d, WISH)).toBeCloseTo(0.01805, 12);
  });

  it("bisection homes in on the same θ with the totals the figure shows", () => {
    const probes = bisectTheta(WISH, 14);
    expect(probes.slice(0, 3).map((p) => p.mid)).toEqual([0.45, 0.225, 0.1125]);
    expect(probes.slice(0, 3).map((p) => Number(p.sum.toFixed(6)))).toEqual([0.45, 0.75, 0.975]);
    expect(probes[13].mid).toBeCloseTo(0.100030517578125, 12);
    expect(probes[13].sum).toBeCloseTo(0.99993896484375, 12);
    expect(Math.abs(probes[13].mid - projectionTheta(WISH))).toBeLessThan(0.9 / 2 ** 14);
    expect(thetaPath(WISH, 14)).toHaveLength(15);
    expect(thetaPath(WISH, 14)[0]).toBe(0);
  });

  it("projects other wishes onto the simplex too (never negative, total 1)", () => {
    for (const y of [[0.2, 0.2, 0.2], [2, 0, -1], [0.5, 0.5, 0.5, 0.5], [5, 1, 1]]) {
      const x = clippedValues(y, projectionTheta(y));
      expect(x.reduce((a, b) => a + b, 0)).toBeCloseTo(1, 12);
      expect(Math.min(...x)).toBeGreaterThanOrEqual(0);
    }
  });
});
