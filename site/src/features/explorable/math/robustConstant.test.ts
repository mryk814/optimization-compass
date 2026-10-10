import { describe, expect, it } from "vitest";

import {
  articleClosedForm,
  BASE_OBSERVATIONS,
  compareFits,
  fitHuber,
  fitSquared,
  huberLoss,
  huberSlope,
} from "./robustConstant";

describe("robust constant fit, the article's four observations", () => {
  it("reproduces the article's table for (0, 0, 0, 10)", () => {
    const { squared, huber } = compareFits(10, 1);
    expect(squared.x).toBeCloseTo(2.5, 12);
    expect(squared.residuals.map((r) => Number(r.toFixed(10)))).toEqual([2.5, 2.5, 2.5, -7.5]);
    expect(squared.objective).toBeCloseTo(37.5, 12);
    expect(squared.slopeSum).toBeCloseTo(0, 12);

    expect(huber.x).toBeCloseTo(1 / 3, 12);
    expect(huber.residuals[0]).toBeCloseTo(1 / 3, 12);
    expect(huber.residuals[3]).toBeCloseTo(-29 / 3, 12);
    expect(huber.objective).toBeCloseTo(28 / 3, 12);
    expect(huber.slopes[0]).toBeCloseTo(1 / 3, 12);
    expect(huber.slopes[3]).toBe(-1);
    expect(huber.slopeSum).toBeCloseTo(0, 12);
    expect(huber.capped).toBe(1);
  });

  it("uses the article's data", () => {
    expect(BASE_OBSERVATIONS).toEqual([0, 0, 0, 10]);
    expect(fitSquared(BASE_OBSERVATIONS)).toBe(2.5);
  });

  it("matches x* = min(m/4, δ/3) and the article's scale sweep", () => {
    const sweep: Array<[number, number]> = [[0.25, 1 / 12], [1, 1 / 3], [3, 1], [7.5, 2.5], [10, 2.5]];
    for (const [delta, expected] of sweep) {
      expect(fitHuber(BASE_OBSERVATIONS, delta)).toBeCloseTo(expected, 12);
      expect(articleClosedForm(10, delta)).toBeCloseTo(expected, 12);
      const slopeSum = compareFits(10, delta).huber.slopeSum;
      expect(Math.abs(slopeSum)).toBeLessThan(1e-9);
    }
    for (const m of [0, 1, 4 / 3, 5, 10, 37, 100]) {
      for (const delta of [0.25, 1, 2.5, 3, 7.5, 10]) {
        expect(fitHuber([0, 0, 0, m], delta)).toBeCloseTo(articleClosedForm(m, delta), 10);
      }
    }
  });

  it("does not move when the last observation goes from 10 to 100 at δ = 1", () => {
    expect(compareFits(100, 1).huber.x).toBeCloseTo(1 / 3, 12);
    expect(compareFits(100, 1).squared.x).toBe(25);
  });

  it("agrees with the squared fit once every residual is quadratic (δ ≥ 7.5 for m = 10)", () => {
    expect(compareFits(10, 7.5).huber.x).toBeCloseTo(2.5, 12);
    expect(compareFits(10, 7.5).huber.capped).toBe(0);
    expect(compareFits(0, 1).huber.x).toBe(0);
  });

  it("joins the quadratic and linear pieces of the loss and caps the slope", () => {
    expect(huberLoss(1, 1)).toBeCloseTo(0.5, 12);
    expect(huberLoss(-3, 1)).toBeCloseTo(2.5, 12);
    expect(huberSlope(-7.5, 1)).toBe(-1);
    expect(huberSlope(0.4, 1)).toBe(0.4);
  });
});
