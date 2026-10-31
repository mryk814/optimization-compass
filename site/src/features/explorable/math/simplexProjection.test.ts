import { describe, expect, it } from "vitest";

import {
  bisectTheta, clippedSum, clippedValues, distance3, divideBySum, halfSquaredDistance, planeShadow, projectionTheta,
  PROJECTED, shadowXY, thetaPath, triangleXY, WISH,
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

  it("draws y's shadow on the plane Σ = 1, directly across the edge from the projected point", () => {
    const shadow = planeShadow(WISH);
    expect(shadow[0]).toBeCloseTo(0.8166666666666667, 12);
    expect(shadow[1]).toBeCloseTo(0.2166666666666667, 12);
    expect(shadow[2]).toBeCloseTo(-0.03333333333333333, 12);
    const [yx, yy] = shadowXY(WISH);
    const [px, py] = triangleXY(PROJECTED);
    expect(px).toBeCloseTo(0.2, 12);
    expect(py).toBeCloseTo(0, 12);
    // Same horizontal position: the edge x₃ = 0 is the x axis, so the segment is perpendicular to it.
    expect(yx).toBeCloseTo(px, 12);
    expect(yy).toBeLessThan(0);
    // The shadow stays put while only the third coordinate is being used up, then walks along that same perpendicular.
    expect(shadowXY(clippedValues(WISH, 0.05))[0]).toBeCloseTo(0.2, 12);
    expect(shadowXY(clippedValues(WISH, 0.2))[0]).toBeCloseTo(0.2, 12);
    expect(shadowXY(clippedValues(WISH, 0.1))[1]).toBeCloseTo(0, 12);
    expect(shadowXY(clippedValues(WISH, 0.3))[0]).toBeCloseTo(0.2, 12);
    expect(shadowXY(clippedValues(WISH, 0.3))[1]).toBeCloseTo((0.4 / 3) * (Math.sqrt(3) / 2), 12);
  });

  it("the divided point is not the one nearest y's shadow", () => {
    const shadow = planeShadow(WISH);
    const divided = divideBySum(WISH);
    const toProjected = distance3(shadow, PROJECTED);
    const toDivided = distance3(shadow, divided);
    expect(toProjected).toBeCloseTo(0.04082482904638631, 12);
    expect(toDivided).toBeLessThan(1);
    expect(toDivided).toBeGreaterThan(toProjected * 2);
    // Moving from the shadow to the divided point is not perpendicular to the edge: its horizontal position differs.
    expect(Math.abs(triangleXY(divided)[0] - shadowXY(WISH)[0])).toBeGreaterThan(0.05);
    // Normal part of y − x is the same for both, so the objective gap equals the in-plane gap.
    expect(distance3(WISH, PROJECTED) ** 2).toBeCloseTo(toProjected ** 2 + 0.25 ** 2 / 3, 12);
  });

  it("projects other wishes onto the simplex too (never negative, total 1)", () => {
    for (const y of [[0.2, 0.2, 0.2], [2, 0, -1], [0.5, 0.5, 0.5, 0.5], [5, 1, 1]]) {
      const x = clippedValues(y, projectionTheta(y));
      expect(x.reduce((a, b) => a + b, 0)).toBeCloseTo(1, 12);
      expect(Math.min(...x)).toBeGreaterThanOrEqual(0);
    }
  });
});
