import { describe, expect, it } from "vitest";

import { boundaryS, determinant, eigenvalues, objective, psdState, R_LIMIT } from "./psdSlice";

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
