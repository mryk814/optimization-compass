import { describe, expect, it } from "vitest";

import {
  BEST_X, betaFraction, equilibrium, equilibriumG, gAlpha, gBeta, LOWEST_G_X, objectiveJ, objectiveSlope,
  tangent, X_ALPHA, X_BETA,
} from "./phaseFraction";

const slope = (g: (x: number) => number, x: number) => (g(x + 1e-7) - g(x - 1e-7)) / 2e-7;

describe("two-phase alloy of the external-solver article", () => {
  it("has the common tangent the article derives by hand", () => {
    expect(slope(gAlpha, X_ALPHA)).toBeCloseTo(0.2, 6);
    expect(slope(gBeta, X_BETA)).toBeCloseTo(0.2, 6);
    expect(tangent(X_ALPHA)).toBeCloseTo(gAlpha(X_ALPHA), 12);
    expect(tangent(X_BETA)).toBeCloseTo(gBeta(X_BETA), 12);
    expect(BEST_X).toBeCloseTo(0.35, 12);
  });

  it("compares the three candidates at x = 0.35 and 0.50", () => {
    const at035 = equilibrium(0.35);
    expect(at035.candidates.map((c) => c.g)).toEqual([
      expect.closeTo(0.0625, 12), expect.closeTo(0.1625, 12), expect.closeTo(0.04, 12),
    ]);
    expect(at035.chosen.phases).toBe("α+β");
    expect(at035.chosen.fBeta).toBeCloseTo(0.3, 12);
    const at050 = equilibrium(0.5);
    expect(at050.candidates.map((c) => c.g)).toEqual([
      expect.closeTo(0.16, 12), expect.closeTo(0.11, 12), expect.closeTo(0.07, 12),
    ]);
    expect(at050.chosen.fBeta).toBeCloseTo(0.6, 12);
  });

  it("reproduces the article's table", () => {
    const rows: Array<[number, string, number, number, number]> = [
      [0.1, "α", 0, 0, 0.09],
      [0.2, "α", 0, 0.01, 0.09],
      [0.35, "α+β", 0.3, 0.04, 0],
      [0.5, "α+β", 0.6, 0.07, 0.09],
      [0.7, "β", 1, 0.11, 0.49],
      [0.8, "β", 1, 0.14, 0.49],
    ];
    for (const [x, phases, f, g, j] of rows) {
      expect(equilibrium(x).chosen.phases).toBe(phases);
      expect(betaFraction(x)).toBeCloseTo(f, 12);
      expect(equilibriumG(x)).toBeCloseTo(g, 12);
      expect(objectiveJ(x)).toBeCloseTo(j, 12);
    }
  });

  it("is flat where β is absent or alone and folds at the phase boundaries", () => {
    for (const x of [0, 0.1, 0.15, 0.8, 0.95]) expect(objectiveSlope(x)).toBe(0);
    expect(objectiveSlope(0.2 + 1e-9)).toBeCloseTo(-1.2, 6);
    expect(objectiveSlope(0.7 - 1e-9)).toBeCloseTo(2.8, 6);
    expect(objectiveSlope(0.5)).toBeCloseTo(1.2, 12);
  });

  it("puts the lowest equilibrium Gibbs energy at x = 0.10, away from the target", () => {
    const grid = Array.from({ length: 1001 }, (_, i) => i / 1000);
    const lowest = grid.reduce((best, x) => (equilibriumG(x) < equilibriumG(best) ? x : best));
    expect(lowest).toBeCloseTo(LOWEST_G_X, 12);
    expect(betaFraction(lowest)).toBe(0);
  });
});
