import { describe, expect, it } from "vitest";

import {
  ARTICLE_QUADRATIC, coordinateEllipse, coordinateGeometry, coordinatePoint,
  coordinateUpdate, rotatedQuadratic, runCoordinateDescent,
} from "./coordinateDescent";

describe("exact cyclic coordinate descent", () => {
  it("reproduces the article's worked path and sweep counts", () => {
    const run = runCoordinateDescent(ARTICLE_QUADRATIC, [4, 3]);
    const expected = [[4, 3, 569], [-9, 3, 400], [-9, -1, 80], [-1, -1, 16], [-1, -1.8, 3.2], [0.6, -1.8, 0.64], [0.6, -1.96, 0.128]];
    expected.forEach(([x, y, f], i) => {
      expect(run.points[i].x).toBeCloseTo(x, 12);
      expect(run.points[i].y).toBeCloseTo(y, 12);
      expect(run.points[i].f).toBeCloseTo(f, 12);
    });
    expect([0, 4, 8].map(c => (runCoordinateDescent({ a: 1, b: c / 2, d: 20 }, [4, 3]).points.length - 1) / 2)).toEqual([1, 12, 73]);
    // For c=4, gx at sweep s is 16·0.2^(s-1): sweep 11 still fails the tolerance.
    expect(16 * 0.2 ** 10).toBeGreaterThan(1e-6);
    expect(16 * 0.2 ** 11).toBeLessThan(1e-6);
  });

  it("minimizes one coordinate while holding the other fixed, without mistaking it for convergence", () => {
    const p = coordinateUpdate(ARTICLE_QUADRATIC, coordinatePoint(ARTICLE_QUADRATIC, 4, 3), "x");
    expect(p.y).toBe(3);
    expect(p.gx).toBe(0);
    expect(p.gy).toBe(160);
    expect(runCoordinateDescent(ARTICLE_QUADRATIC, [4, 3], 1).outcome).toBe("budget");
  });

  it("distinguishes an optimal start, a complete sweep, and a budget stop", () => {
    expect(runCoordinateDescent(ARTICLE_QUADRATIC, [1, -2]).points).toHaveLength(1);
    expect(runCoordinateDescent(ARTICLE_QUADRATIC, [1, -2]).outcome).toBe("converged");
    const separated = runCoordinateDescent({ a: 1, b: 0, d: 20 }, [4, 3]);
    expect(separated.points).toHaveLength(3);
    expect(separated.outcome).toBe("converged");
    const slow = runCoordinateDescent(rotatedQuadratic(1, 100, 45), [4, 3]);
    expect(slow.points).toHaveLength(201);
    expect(slow.outcome).toBe("budget");
  });

  it("stays monotone across orientations and curvature scales", () => {
    for (const angle of [-90, -45, 0, 20, 45, 90]) {
      for (const kappa of [1, 20, 100]) {
        const q = rotatedQuadratic(0.8, kappa, angle);
        const { points } = runCoordinateDescent(q, [4, 3]);
        points.slice(1).forEach((p, i) => {
          const previous = points[i];
          expect(p.f).toBeLessThanOrEqual(previous.f + 1e-10);
          expect(i % 2 === 0 ? p.y : p.x).toBe(i % 2 === 0 ? previous.y : previous.x);
          expect(i % 2 === 0 ? p.gx : p.gy).toBeCloseTo(0, 10);
        });
      }
    }
  });

  it("connects orientation, curvature ratio, correlation and sweep contraction", () => {
    const g = coordinateGeometry(ARTICLE_QUADRATIC);
    const restored = rotatedQuadratic(g.gentle, g.kappa, g.angle);
    expect(restored.a).toBeCloseTo(1, 12);
    expect(restored.b).toBeCloseTo(2, 12);
    expect(restored.d).toBeCloseTo(20, 12);
    expect(g.sweepFactor).toBeCloseTo(0.2, 12);
    expect(coordinateGeometry(rotatedQuadratic(1, 100, 0)).rho).toBeCloseTo(0, 12);
    expect(Math.abs(coordinateGeometry(rotatedQuadratic(1, 100, 45)).rho)).toBeCloseTo(99 / 101, 12);
    const points = runCoordinateDescent(ARTICLE_QUADRATIC, [4, 3]).points;
    expect((points[4].y + 2) / (points[2].y + 2)).toBeCloseTo(g.sweepFactor, 12);
  });

  it("does not claim a change of coordinate units accelerates exact minimization", () => {
    // Scaling the x error by s changes a→a/s², b→b/s; map the path back afterwards.
    const s = 10;
    const q = ARTICLE_QUADRATIC;
    const scaled = { a: q.a / s ** 2, b: q.b / s, d: q.d };
    const original = runCoordinateDescent(q, [4, 3], 10).points;
    const changed = runCoordinateDescent(scaled, [1 + 3 * s, 3], 10).points;
    changed.forEach((p, i) => {
      expect(1 + (p.x - 1) / s).toBeCloseTo(original[i].x, 10);
      expect(p.y).toBeCloseTo(original[i].y, 10);
    });
    expect(coordinateGeometry(scaled).sweepFactor).toBeCloseTo(coordinateGeometry(q).sweepFactor, 12);
  });

  it("draws level sets of the same quadratic and rejects unsupported models", () => {
    for (const p of coordinateEllipse(ARTICLE_QUADRATIC, 80)) expect(coordinatePoint(ARTICLE_QUADRATIC, ...p).f).toBeCloseTo(80, 10);
    expect(() => runCoordinateDescent({ a: 1, b: 2, d: 1 }, [4, 3])).toThrow(/positive-definite/);
  });
});
