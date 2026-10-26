import { describe, expect, it } from "vitest";

import { QP_ARTICLE_LIMIT, QP_ARTICLE_TARGET, balanceArrows, relaxSumLimit, solveConvexQp } from "./convexQp";

// Reference values come from scipy.optimize.minimize (SLSQP, ftol 1e-14) on
// min ||x - p||^2 s.t. x1 + x2 <= b, x >= 0.
const REFERENCE: ReadonlyArray<{ p: [number, number]; b: number; x: [number, number]; f: number }> = [
  { p: [3, 2], b: 3, x: [2, 1], f: 2 },
  { p: [1, 1], b: 3, x: [1, 1], f: 0 },
  { p: [5, 0], b: 3, x: [3, 0], f: 4 },
  { p: [-1, 1.5], b: 3, x: [0, 1.5], f: 1 },
  { p: [3, 2], b: 5, x: [3, 2], f: 0 },
  { p: [3, 2], b: 3.1, x: [2.05, 1.05], f: 1.805 },
  { p: [0, 5], b: 3, x: [0, 3], f: 4 },
  { p: [4, 4], b: 2, x: [1, 1], f: 18 },
];

describe("solveConvexQp", () => {
  it.each(REFERENCE)("matches the SciPy solution for p=$p, b=$b", ({ p, b, x, f }) => {
    const s = solveConvexQp(p, b);
    expect(s.x[0]).toBeCloseTo(x[0], 6);
    expect(s.x[1]).toBeCloseTo(x[1], 6);
    expect(s.value).toBeCloseTo(f, 6);
  });

  it("article example: (2, 1), multiplier 2 on the sum limit, active set {sum}", () => {
    const s = solveConvexQp(QP_ARTICLE_TARGET, QP_ARTICLE_LIMIT);
    expect(s.multipliers[0]).toBeCloseTo(2, 9);
    expect(s.multipliers[1]).toBe(0);
    expect(s.multipliers[2]).toBe(0);
    expect(s.activeSet).toEqual([0]);
    expect(s.atVertex).toBe(false);
    expect(s.targetInside).toBe(false);
    // The best vertex is (3, 0) with 4, so comparing vertices alone misses 2 by 2.
    expect(s.bestVertex).toEqual([3, 0]);
    expect(s.bestVertexValue).toBe(4);
    expect(s.vertexValues).toEqual([13, 4, 10]);
    expect(s.vertexGap).toBeCloseTo(2, 9);
  });

  it("target inside: nothing is active and every multiplier is 0", () => {
    const s = solveConvexQp([1, 1], 3);
    expect(s.activeSet).toEqual([]);
    expect(s.multipliers).toEqual([0, 0, 0]);
    expect(s.targetInside).toBe(true);
  });

  it("target exactly on the boundary x1+x2=5: tight but multiplier 0", () => {
    const s = solveConvexQp([3, 2], 5);
    expect(s.tight).toEqual([0]);
    expect(s.multipliers[0]).toBe(0);
    expect(s.targetInside).toBe(false);
  });

  it("target (5, 0): vertex (3, 0), multipliers 4 on the sum limit and 4 on x2 >= 0", () => {
    const s = solveConvexQp([5, 0], 3);
    expect(s.atVertex).toBe(true);
    expect(s.activeSet).toEqual([0, 2]);
    expect(s.multipliers[0]).toBeCloseTo(4, 9);
    expect(s.multipliers[2]).toBeCloseTo(4, 9);
  });

  it("satisfies the KKT conditions for a grid of targets and limits", () => {
    for (let p1 = -1; p1 <= 5; p1 += 0.5) {
      for (let p2 = -1; p2 <= 5; p2 += 0.5) {
        for (const b of [1, 2.5, 3, 5]) {
          const s = solveConvexQp([p1, p2], b);
          const grad = [2 * (s.x[0] - p1), 2 * (s.x[1] - p2)];
          const [l0, l1, l2] = s.multipliers;
          expect(grad[0] + l0 - l1).toBeCloseTo(0, 8);
          expect(grad[1] + l0 - l2).toBeCloseTo(0, 8);
          expect(s.x[0] + s.x[1]).toBeLessThanOrEqual(b + 1e-9);
          expect(Math.min(s.x[0], s.x[1])).toBeGreaterThanOrEqual(-1e-9);
          expect(l0 * (s.x[0] + s.x[1] - b)).toBeCloseTo(0, 8);
          expect(l1 * s.x[0]).toBeCloseTo(0, 8);
          expect(l2 * s.x[1]).toBeCloseTo(0, 8);
          // The true minimum is never worse than the best vertex.
          expect(s.vertexGap).toBeGreaterThanOrEqual(-1e-9);
        }
      }
    }
  });
});

describe("relaxSumLimit", () => {
  it("loosening b from 3 to 3.1: prediction 0.2, exact 0.195 (2 - 1.805)", () => {
    const r = relaxSumLimit(QP_ARTICLE_TARGET, QP_ARTICLE_LIMIT, 0.1);
    expect(r.predicted).toBeCloseTo(0.2, 9);
    expect(r.actual).toBeCloseTo(0.195, 9);
  });

  it("at b = 3.5 the multiplier is 1.5: prediction 0.150, exact 0.145 (1.125 - 0.98)", () => {
    const r = relaxSumLimit(QP_ARTICLE_TARGET, 3.5, 0.1);
    expect(solveConvexQp(QP_ARTICLE_TARGET, 3.5).multipliers[0]).toBeCloseTo(1.5, 9);
    expect(r.predicted).toBeCloseTo(0.15, 9);
    expect(r.actual).toBeCloseTo(0.145, 9);
  });

  it("with the target at (5, 0) the answer is the vertex (3, 0) with lambda 4, and v(eps) = (2 - eps)^2", () => {
    const s = solveConvexQp([5, 0], 3);
    expect(s.multipliers[0]).toBeCloseTo(4, 9);
    expect(s.multipliers[2]).toBeCloseTo(4, 9);
    expect(relaxSumLimit([5, 0], 3, 0.1).actual).toBeCloseTo(4 - 1.9 ** 2, 9);
  });
});

describe("balanceArrows", () => {
  it("at the article example the gradient (-2, -2) points toward the origin side and λ·a = (2, 2) pushes back", () => {
    const { gradient, pushes } = balanceArrows(solveConvexQp([3, 2], 3));
    expect(gradient[0]).toBeCloseTo(-2, 9);
    expect(gradient[1]).toBeCloseTo(-2, 9);
    expect(pushes).toHaveLength(1);
    expect(pushes[0].index).toBe(0);
    expect(pushes[0].vector[0]).toBeCloseTo(2, 9);
    expect(pushes[0].vector[1]).toBeCloseTo(2, 9);
  });

  it("the arrows cancel at a vertex too, and there are none when the target is inside", () => {
    const vertex = balanceArrows(solveConvexQp([5, 0], 3));
    expect(vertex.pushes).toHaveLength(2);
    const sx = vertex.gradient[0] + vertex.pushes.reduce((sum, p) => sum + p.vector[0], 0);
    const sy = vertex.gradient[1] + vertex.pushes.reduce((sum, p) => sum + p.vector[1], 0);
    expect(Math.abs(sx)).toBeLessThan(1e-9);
    expect(Math.abs(sy)).toBeLessThan(1e-9);
    const inside = balanceArrows(solveConvexQp([1, 1], 3));
    expect(inside.pushes).toHaveLength(0);
    expect(inside.gradient).toEqual([0, 0]);
  });
});
