import { describe, expect, it } from "vitest";

import fixture from "./inverseProblem.fixture.json";
import {
  bestAlphaOnGrid, discrepancyAlpha, INVERSE_DATA, INVERSE_DELTA, INVERSE_N, INVERSE_TRUTH, tikhonov,
} from "./inverseProblem";

// Numbers asserted here are the ones printed in content/concepts/inverse-problem.md.
describe("inverse problem (rod example)", () => {
  it("imports the example from the Python fixture", () => {
    expect(INVERSE_N).toBe(40);
    expect(INVERSE_TRUTH).toHaveLength(40);
    expect(INVERSE_DATA).toHaveLength(40);
    expect(fixture.blur).toHaveLength(40);
    for (const row of fixture.blur) expect(row.reduce((a, b) => a + b, 0)).toBeCloseTo(1, 12);
    expect(INVERSE_DELTA).toBeCloseTo(0.00632, 5);
    expect(Math.sqrt(INVERSE_TRUTH.reduce((s, v) => s + v * v, 0))).toBeCloseTo(2.257, 3);
  });

  it("reproduces the relative errors of the alpha table", () => {
    expect(tikhonov(1e-10).relativeError).toBeCloseTo(43.9, 1);
    expect(tikhonov(1e-6).relativeError).toBeCloseTo(0.612, 3);
    expect(tikhonov(1e-3).relativeError).toBeCloseTo(0.0182, 4);
    expect(tikhonov(1e-1).relativeError).toBeCloseTo(0.19, 3);
  });

  it("reproduces residual and length columns", () => {
    expect(tikhonov(1e-3).residual).toBeCloseTo(0.00687, 4);
    expect(tikhonov(1e-3).length).toBeCloseTo(2.253, 2);
    expect(tikhonov(1e-1).residual).toBeCloseTo(0.2426, 3);
    expect(tikhonov(1e-6).length).toBeCloseTo(2.65, 2);
    expect(tikhonov(1e-10).residual).toBeCloseTo(0.0029, 4);
  });

  it("keeps the residual increasing in alpha while the error is U-shaped", () => {
    const alphas = [1e-10, 1e-8, 1e-6, 1e-4, 1e-3, 1e-2, 1e-1];
    const readings = alphas.map(tikhonov);
    for (let i = 1; i < readings.length; i += 1) expect(readings[i].residual).toBeGreaterThan(readings[i - 1].residual);
    const errors = readings.map(r => r.relativeError);
    expect(errors.indexOf(Math.min(...errors))).toBe(alphas.indexOf(1e-3));
  });

  it("selects alpha by the discrepancy principle", () => {
    const alpha = discrepancyAlpha();
    expect(alpha).toBeCloseTo(7.25e-4, 6);
    const reading = tikhonov(alpha);
    expect(reading.residual).toBeCloseTo(0.00632, 5);
    expect(reading.relativeError).toBeCloseTo(0.0199, 4);
  });

  it("finds the best alpha only because the truth is known", () => {
    const best = bestAlphaOnGrid();
    expect(best.alpha).toBeCloseTo(1.26e-3, 5);
    expect(best.relativeError).toBeCloseTo(0.0177, 4);
  });
});
