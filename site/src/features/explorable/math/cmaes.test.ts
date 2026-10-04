import { describe, expect, it } from "vitest";

import { axisRatio, defaultParameters, eigen2, runCmaes, valley } from "./cmaes";

const narrow = (adaptShape: boolean, seed = 1, count = 71) =>
  runCmaes({ mean: [3, 1], sigma: 1, ratio: 10, seed, adaptShape, count });

describe("two-dimensional CMA-ES (Hansen's tutorial defaults)", () => {
  it("uses λ = 6, μ = 3 and log weights", () => {
    const p = defaultParameters(true);
    expect([p.lambda, p.mu]).toEqual([6, 3]);
    expect(p.weights.map((w) => Math.round(w * 1000) / 1000)).toEqual([0.637, 0.285, 0.078]);
    expect(p.muEff).toBeCloseTo(2.029, 3);
    expect(p.c1).toBeCloseTo(0.1548, 4);
    expect(p.cMu).toBeCloseTo(0.0579, 4);
  });

  it("matches the Python reference for the first generation", () => {
    const [g0, g1] = narrow(true).generations;
    expect(valley([3, 1], 10)).toBeCloseTo(208, 9);
    expect(g0.samples.map((s) => Math.round(s.f * 1000) / 1000)).toEqual([182.88, 188.347, 234.305, 238.867, 524.303, 1046.726]);
    expect(g0.samples[0].x[0]).toBeCloseTo(2.958, 3);
    expect(g1.mean[0]).toBeCloseTo(3.244, 3);
    expect(g1.mean[1]).toBeCloseTo(1.362, 3);
    expect(g1.sigma).toBeCloseTo(0.834, 3);
  });

  it("learns the valley's direction and its 10 : 1 shape", () => {
    const { generations } = narrow(true);
    expect(generations[30].samples[0].f).toBeCloseTo(2.26e-3, 4);
    expect(axisRatio(generations[70].cov)).toBeCloseTo(9.93, 1);
    const [axis] = eigen2(generations[70].cov).vectors;
    expect(Math.abs(axis[0])).toBeCloseTo(Math.SQRT1_2, 1);
    expect(Math.abs(axis[1])).toBeCloseTo(Math.SQRT1_2, 1);
    expect(generations.findIndex((g) => g.samples[0].f < 1e-6)).toBe(42);
  });

  it("stays round and slow when only σ adapts", () => {
    const { generations } = narrow(false, 1, 60);
    expect(axisRatio(generations[59].cov)).toBe(1);
    expect(generations[59].samples[0].f).toBeCloseTo(0.121, 2);
    expect(generations.some((g) => g.samples[0].f < 1e-3)).toBe(false);
  });

  it("gains little from shape learning in a round valley", () => {
    const round = (adaptShape: boolean) => runCmaes({ mean: [3, 1], sigma: 1, ratio: 1, seed: 1, adaptShape, count: 60 })
      .generations.findIndex((g) => g.samples[0].f < 1e-6);
    expect(round(true)).toBe(37);
    expect(round(false)).toBe(42);
  });
});
