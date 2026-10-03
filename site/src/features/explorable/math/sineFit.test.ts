import { describe, expect, it } from "vitest";

import { bestAmplitude, gaussNewton, GLOBAL_MINIMUM, levenbergMarquardt, linearizedSse, sse } from "./sineFit";

describe("spring sine fit", () => {
  it("matches the article's best fit and the aliased copy 4π away", () => {
    expect(sse(GLOBAL_MINIMUM)).toBeCloseTo(0.19012, 4);
    expect(sse({ a: GLOBAL_MINIMUM.a, w: GLOBAL_MINIMUM.w + 4 * Math.PI })).toBeCloseTo(0.19012, 4);
    expect(sse({ a: 0, w: 1 })).toBeCloseTo(14.23, 6);
  });

  it("solves the amplitude by linear least squares once ω is fixed", () => {
    expect(bestAmplitude(GLOBAL_MINIMUM.w)).toBeCloseTo(GLOBAL_MINIMUM.a, 3);
  });

  it("takes Gauss–Newton steps to the bottom of the linearized bowl", () => {
    const run = gaussNewton({ a: 1, w: 1.8 });
    expect(run.outcome).toBe("global");
    expect(run.path[1].a).toBeCloseTo(1.8339, 3);
    expect(run.path[1].w).toBeCloseTo(2.1854, 3);
    expect(run.path[1].sse).toBeCloseTo(2.2342, 3);
    // The bowl predicted far less than the true sum of squares at the first step.
    expect(run.path[1].predicted).toBeLessThan(run.path[1].sse);
    expect(linearizedSse({ a: 1, w: 1.8 }, { a: 1, w: 1.8 })).toBeCloseTo(5.42, 2);
  });

  it("lets plain Gauss–Newton fly off from ω = 3", () => {
    const run = gaussNewton({ a: 1, w: 3 });
    expect(run.path[2].w).toBeCloseTo(6.3017, 3);
    expect(run.outcome).toBe("diverged");
  });

  it("damps the step with Levenberg–Marquardt but can still stop in a wrong valley", () => {
    const fromThree = levenbergMarquardt({ a: 1, w: 3 });
    expect(fromThree.outcome).toBe("global");
    const fromFour = levenbergMarquardt({ a: 1, w: 4 });
    expect(fromFour.outcome).toBe("local");
    const last = fromFour.path[fromFour.path.length - 1];
    expect(last.w).toBeCloseTo(4.128, 1);
    expect(last.a).toBeCloseTo(0.417, 2);
    expect(last.sse).toBeCloseTo(13.556, 2);
    fromFour.path.slice(1).forEach((step, index) => expect(step.sse).toBeLessThan(fromFour.path[index].sse));
  });

  it("backs the guided scene's captions", () => {
    expect(gaussNewton({ a: 1, w: 1.8 }).path[3].sse).toBeCloseTo(0.19, 2);
    const flown = gaussNewton({ a: 1, w: 3 });
    expect(flown.path).toHaveLength(4);
    expect(Math.abs(flown.path[3].w)).toBeGreaterThan(12);
    expect(levenbergMarquardt({ a: 1, w: 4 }).path.at(-1)!.sse).toBeCloseTo(13.6, 1);
  });
});
