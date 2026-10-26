import { describe, expect, it } from "vitest";

import {
  bisectionSteps, bracketWindow, blendWindow, digits, F, fStable, jacobianDet2, newtonSteps, newtonWindow, planeNewtonPath,
  PLANE_ROOTS, residual2, ROOT, SINGULAR_POINT, WIDE_WINDOW,
} from "./rootFinding";

// Expected numbers come from scratchpad/motion_numbers.py (double precision).
describe("root-finding slice F(t) = t² + t − 1", () => {
  it("has the article's positive root", () => {
    expect(ROOT).toBeCloseTo(0.6180339887498949, 15);
    expect(Math.abs(F(ROOT))).toBeLessThan(1e-15);
  });

  it("factors without cancellation, so a plot a millionth wide near the root stays smooth", () => {
    for (const t of [-1, 0, 0.3, 0.7, 1.5]) expect(fStable(t)).toBeCloseTo(F(t), 12);
    expect(fStable(0.6180339887553599)).toBeCloseTo(1.222e-11, 13);
  });

  it("reproduces the article's three Newton steps from 0.7", () => {
    const steps = newtonSteps(0.7, 3);
    expect(steps[0].residual).toBeCloseTo(0.19, 12);
    expect(steps[0].slope).toBeCloseTo(2.4, 12);
    expect(steps[0].next).toBeCloseTo(0.6208333333333333, 12);
    expect(steps[1].residual).toBeCloseTo(0.006267361111111, 12);
    expect(steps[1].next).toBeCloseTo(0.6180374845105329, 12);
    expect(steps[2].residual).toBeCloseTo(7.816770640101e-6, 15);
    expect(steps[2].next).toBeCloseTo(0.6180339887553599, 13);
    expect(steps[2].nextResidual).toBeCloseTo(1.222e-11, 13);
  });

  it("squares the error each step (quadratic convergence)", () => {
    const steps = newtonSteps(0.7, 3);
    const errors = [steps[0].t, steps[1].t, steps[2].t, steps[2].next].map((t) => Math.abs(t - ROOT));
    expect(errors[0]).toBeCloseTo(0.08196601125, 10);
    expect(errors[1]).toBeCloseTo(0.0027993445834, 12);
    expect(errors[2]).toBeCloseTo(3.4957606e-6, 12);
    for (let k = 0; k < 3; k += 1) {
      // e_{k+1} = e_k² / (2 t_k + 1) exactly for this quadratic.
      expect(errors[k + 1]).toBeCloseTo(errors[k] ** 2 / steps[k].slope, 12);
    }
  });

  it("halves the bracket and matches the sign rule", () => {
    const steps = bisectionSteps(0, 1, 8);
    expect(steps.map((s) => s.mid)).toEqual([0.5, 0.75, 0.625, 0.5625, 0.59375, 0.609375, 0.6171875, 0.62109375]);
    expect(steps[0].midResidual).toBeCloseTo(-0.25, 15);
    expect(steps[2].midResidual).toBeCloseTo(0.015625, 15);
    expect(steps[7].nextHi - steps[7].nextLo).toBeCloseTo(1 / 256, 15);
    for (const s of steps) expect(F(s.nextLo)).toBeLessThan(0);
  });

  it("counts correct digits and caps at double precision", () => {
    expect(digits(0.19)).toBeCloseTo(0.7212, 3);
    expect(digits(7.8168e-6)).toBeCloseTo(5.107, 3);
    expect(digits(0)).toBe(16);
    expect(digits(1e-30)).toBe(16);
  });

  it("zooms around the root so each step fills the same view", () => {
    const [a, b, c] = newtonSteps(0.7, 3);
    expect(newtonWindow(b).half / newtonWindow(a).half).toBeCloseTo(0.0027993445834 / 0.08196601125, 6);
    expect(newtonWindow(c).half).toBeLessThan(1e-5);
    // The factors the figure's title shows (and the article quotes): wide half-width over this step's.
    expect([a, b, c].map((s) => Math.round(WIDE_WINDOW.half / newtonWindow(s).half))).toEqual([6, 167, 133495]);
    const mid = blendWindow(newtonWindow(a), newtonWindow(b), 0.5);
    expect(mid.half).toBeCloseTo(Math.sqrt(newtonWindow(a).half * newtonWindow(b).half), 12);
    expect(bracketWindow(0.5, 0.75).half).toBeCloseTo(0.1875, 12);
  });

  it("the two-variable first step from (0.7, 0.7) is (−0.0791667, −0.0791667)", () => {
    expect(residual2(0.7, 0.7)[0]).toBeCloseTo(0.19, 12);
    const path = planeNewtonPath(0.7, 0.7, 3);
    expect(path.stuck).toBe(false);
    expect(path.points[1][0]).toBeCloseTo(0.7 - 0.0791666666667, 10);
    expect(path.points[1][1]).toBeCloseTo(0.7 - 0.0791666666667, 10);
    expect(path.points[3][0]).toBeCloseTo(0.6180339887553599, 12);
  });

  it("three starts reach three different roots", () => {
    const a = planeNewtonPath(0.7, 0.7, 30).points.at(-1)!;
    const b = planeNewtonPath(0.9, 0.1, 30).points.at(-1)!;
    const c = planeNewtonPath(-1, -1, 30).points.at(-1)!;
    expect(a[0]).toBeCloseTo(0.618033988749895, 12);
    expect(b[0]).toBeCloseTo(1, 12);
    expect(b[1]).toBeCloseTo(0, 12);
    expect(c[0]).toBeCloseTo(-1.618033988749895, 12);
    expect(c[1]).toBeCloseTo(-1.618033988749895, 12);
    expect(planeNewtonPath(0.9, 0.1, 1).points[1][0]).toBeCloseTo(1.0125, 12);
    expect(planeNewtonPath(-1, -1, 1).points[1][0]).toBeCloseTo(-2, 12);
    for (const [x1, x2] of PLANE_ROOTS) {
      expect(Math.abs(residual2(x1, x2)[0])).toBeLessThan(1e-12);
      expect(Math.abs(residual2(x1, x2)[1])).toBeLessThan(1e-12);
    }
  });

  it("has no step at (0.5, 0.5), where the Jacobian is [[1, 1], [1, 1]]", () => {
    expect(jacobianDet2(SINGULAR_POINT.x1, SINGULAR_POINT.x2)).toBe(0);
    expect(residual2(0.5, 0.5)[0]).toBeCloseTo(-0.25, 15);
    const path = planeNewtonPath(0.5, 0.5, 3);
    expect(path.stuck).toBe(true);
    expect(path.points).toHaveLength(1);
  });
});
