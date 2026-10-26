import { describe, expect, it } from "vitest";

import {
  boundaryS, determinant, eigenProduct, eigenSum, eigenvalues, objective, psdState, R_LIMIT,
  smallestWeightedVariance, SWEEP_HOLD_STEPS, SWEEP_LENGTH, sweepR, weightedDifferenceVariance,
} from "./psdSlice";

// Expected numbers come from scratchpad/motion_numbers.py (numpy eigvalsh / det).
describe("2×2 slice [[1, r], [r, 4]]", () => {
  it("matches the article's table of determinants and eigenvalues", () => {
    const table: Array<[number, number, number, number]> = [
      [-2, 0, 0, 5],
      [0, 4, 1, 4],
      [2, 0, 0, 5],
      [3, -5, -0.85410197, 5.85410197],
    ];
    for (const [r, det, low, high] of table) {
      expect(determinant(r)).toBeCloseTo(det, 12);
      const [l, h] = eigenvalues(r);
      expect(l).toBeCloseTo(low, 7);
      expect(h).toBeCloseTo(high, 7);
    }
    expect(eigenvalues(1)[0]).toBeCloseTo(0.69722436, 7);
    expect(eigenvalues(2.5)[0]).toBeCloseTo(-0.41547595, 7);
  });

  it("is semidefinite exactly on −2 ≤ r ≤ 2, with an eigenvalue 0 at both ends", () => {
    expect(R_LIMIT).toBe(2);
    expect(psdState(0)).toBe("inside");
    expect(psdState(2)).toBe("boundary");
    expect(psdState(-2)).toBe("boundary");
    expect(psdState(2.05)).toBe("outside");
    expect(psdState(3)).toBe("outside");
    for (let r = -3; r <= 3; r += 0.05) {
      const feasible = eigenvalues(r)[0] >= -1e-12;
      expect(feasible).toBe(Math.abs(r) <= 2 + 1e-9);
    }
  });

  it("keeps the trace at 5 and lets the larger eigenvalue grow as the smaller falls", () => {
    for (const r of [0, 1, 2, 3]) {
      const [l, h] = eigenvalues(r);
      expect(l + h).toBeCloseTo(5, 12);
    }
    expect(eigenvalues(3)[1]).toBeGreaterThan(eigenvalues(2)[1]);
  });

  it("puts the diagonal-4 line on the parabola s = r² at r = ±2, and the best objective is −2", () => {
    expect(boundaryS(2)).toBe(4);
    expect(boundaryS(-2)).toBe(4);
    expect(objective(2)).toBe(-2);
  });
});

describe("sweep, product and weighted variance used by the figure", () => {
  it("rests on r = 2 for the hold steps and ends at 3", () => {
    expect(sweepR(0)).toBe(0);
    expect(sweepR(40)).toBeCloseTo(2, 12);
    expect(sweepR(40 + SWEEP_HOLD_STEPS / 2)).toBeCloseTo(2, 12);
    expect(sweepR(40 + SWEEP_HOLD_STEPS)).toBeCloseTo(2, 12);
    expect(sweepR(SWEEP_LENGTH)).toBeCloseTo(3, 12);
  });

  it("product of the eigenvalues is 4 − r² and the sum is 5", () => {
    for (const r of [-3, -1, 0, 1, 2, 2.5, 3]) {
      expect(eigenProduct(r)).toBeCloseTo(4 - r * r, 10);
      expect(eigenSum(r)).toBeCloseTo(5, 12);
    }
  });

  it("a plain difference stays positive past r = 2 but a weighted one does not", () => {
    expect(weightedDifferenceVariance(2.1, 1)).toBeCloseTo(0.8, 12);
    expect(weightedDifferenceVariance(2.5, 1)).toBeCloseTo(0, 12);
    expect(smallestWeightedVariance(2.5)).toBeCloseTo(-0.5625, 12);
    expect(smallestWeightedVariance(3)).toBeCloseTo(-1.25, 12);
    expect(smallestWeightedVariance(2)).toBeCloseTo(0, 12);
  });
});
