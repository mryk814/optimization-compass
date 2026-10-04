import { describe, expect, it } from "vitest";

import { correctDigits, gradientRun, limitOf, newtonRun } from "./newton1d";

describe("Newton's method on x⁴/4 − x²/2", () => {
  it("doubles the correct digits near the valley at x = 1", () => {
    const xs = newtonRun(2, "newton").map((step) => step.x);
    expect(xs[1]).toBeCloseTo(1.454545, 5);
    expect(xs[2]).toBeCloseTo(1.151047, 5);
    expect(xs[3]).toBeCloseTo(1.025326, 5);
    const digits = xs.slice(3, 7).map((x) => correctDigits(x, 1));
    expect(digits.map((d) => Math.round(d * 10) / 10)).toEqual([1.6, 3, 5.9, 11.6]);
    expect(limitOf(xs)).toBe(1);
  });

  it("adds about a tenth of a digit per step with gradient descent (η = 0.1)", () => {
    const xs = gradientRun(2);
    expect(xs[7]).toBeCloseTo(1.06297, 4);
    expect(correctDigits(xs[7], 1)).toBeCloseTo(1.2, 1);
  });

  it("heads to the hill at x = 0 where the curvature is negative", () => {
    const xs = newtonRun(0.3, "newton").map((step) => step.x);
    expect(xs[1]).toBeCloseTo(-0.07397, 4);
    expect(limitOf(xs)).toBe(0);
  });

  it("leaps far where the curvature is almost zero", () => {
    expect(newtonRun(0.6, "newton")[1].x).toBeCloseTo(5.4, 10);
  });

  it("falls back to −f' and a line search when the curvature is not positive enough", () => {
    const fromHill = newtonRun(0.3, "safeguarded");
    expect(fromHill[1].fallback).toBe(true);
    expect(fromHill[1].x).toBeCloseTo(0.573, 3);
    expect(limitOf(fromHill.map((step) => step.x))).toBe(1);
    expect(newtonRun(0.6, "safeguarded")[1].x).toBeCloseTo(0.984, 3);
  });
});
