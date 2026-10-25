import { describe, expect, it } from "vitest";

import { bestAmplitude, gaussNewton, GLOBAL_MINIMUM, levenbergMarquardt, linearizedSse, sse, stepReading } from "./sineFit";

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

  it("reads each step's promised and actual fall against the article's tables", () => {
    const near = gaussNewton({ a: 1, w: 1.8 }).path;
    const first = stepReading(near, 1)!;
    expect(first.startSse).toBeCloseTo(5.42, 2);
    expect(first.head.w).toBeCloseTo(2.185, 3);
    expect(first.predicted).toBeCloseTo(0.245, 3);
    expect(first.actual).toBeCloseTo(2.234, 3);
    expect(first.predictedDecrease).toBeCloseTo(5.42 - 0.245, 2);
    expect(first.actualDecrease).toBeCloseTo(5.42 - 2.234, 2);
    expect(first.overshoot).toBe(false);
    const third = stepReading(near, 3)!;
    expect(third.index).toBe(2);
    expect(third.predicted).toBeCloseTo(0.19, 3);
    expect(third.actual).toBeCloseTo(0.19, 3);
    expect(third.head.w).toBeCloseTo(2.003, 3);
    expect(stepReading(near, 2)!.head.w).toBeCloseTo(1.987, 3);
  });

  it("starts every step with the bowl and the landscape agreeing, and lets them part on the way", () => {
    const path = gaussNewton({ a: 1, w: 3 }).path;
    for (let index = 0; index < path.length - 1; index += 1) {
      const begin = stepReading(path, index + 1e-7)!;
      expect(begin.index).toBe(index);
      expect(begin.predicted).toBeCloseTo(begin.startSse, 3);
      expect(begin.actual).toBeCloseTo(begin.startSse, 3);
    }
    expect(stepReading(path, 1)!.head.w).toBeCloseTo(2.589, 3);
    expect(stepReading(path, 2)!.head.w).toBeCloseTo(6.302, 3);
    const last = stepReading(path, 3)!;
    expect(last.head.w).toBeCloseTo(401.455, 3);
    expect(last.predicted).toBeCloseTo(12.672, 3);
    expect(last.actual).toBeGreaterThan(1e9);
    expect(last.overshoot).toBe(true);
    expect(last.actualDecrease).toBeLessThan(0);
    // The bowl promises a fall all along the step; the landscape does not give it.
    const half = stepReading(path, 2.5)!;
    expect(half.predicted).toBeLessThan(half.startSse);
    expect(half.actual).toBeGreaterThan(half.startSse);
  });

  it("never lets a Levenberg–Marquardt step end above where it started", () => {
    const path = levenbergMarquardt({ a: 1, w: 3 }).path;
    for (let index = 1; index < path.length; index += 1) {
      const reading = stepReading(path, index)!;
      expect(reading.overshoot).toBe(false);
      expect(reading.actualDecrease).toBeGreaterThan(0);
    }
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

  it("distinguishes a singular start from a settled local valley", () => {
    const run = gaussNewton({ a: 0, w: 1.8 });
    expect(run.path).toHaveLength(1);
    expect(run.outcome).toBe("stalled");
    expect(sse({ a: 0.01, w: 1.8 })).toBeLessThan(run.path[0].sse);
  });

  it("reports budget exhaustion before the fit has settled", () => {
    expect(gaussNewton({ a: 1, w: 1.8 }, 1).outcome).toBe("budget");
    expect(levenbergMarquardt({ a: 1, w: 1.8 }, 1).outcome).toBe("budget");
  });
});
