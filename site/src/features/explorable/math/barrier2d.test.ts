import { describe, expect, it } from "vitest";

import { centralPath, f, F_STAR, LAMBDA_STAR, muAt, MU_STEPS, slack, SOLUTION } from "./barrier2d";

describe("log-barrier central path on the unit disk", () => {
  const decades = centralPath([10, 1, 0.1, 0.01, 0.001, 0.0001]);

  it("matches the Python reference at each decade of μ", () => {
    const rounded = decades.map(({ p }) => [Math.round(p[0] * 1e4) / 1e4, Math.round(p[1] * 1e4) / 1e4]);
    expect(rounded).toEqual([[0.1655, 0.2652], [0.5336, 0.5928], [0.6953, 0.6807], [0.7184, 0.6916], [0.7208, 0.6927], [0.7211, 0.6928]]);
    expect(decades.map((c) => c.newtonSteps)).toEqual([4, 6, 6, 5, 7, 7]);
  });

  it("keeps the gap f(x(μ)) − f* at about μ and the multiplier μ/s near λ*", () => {
    for (const { mu, p } of decades.slice(2)) {
      expect((f(p) - F_STAR) / mu).toBeCloseTo(1, 1);
    }
    const last = decades[decades.length - 1];
    expect(last.mu / slack(last.p)).toBeCloseTo(LAMBDA_STAR, 2);
    expect(f(SOLUTION)).toBeCloseTo(F_STAR, 5);
  });

  it("stays strictly inside the disk along the whole sweep", () => {
    const sweep = centralPath(Array.from({ length: MU_STEPS + 1 }, (_, index) => muAt(index)));
    expect(muAt(0)).toBe(10);
    expect(muAt(MU_STEPS)).toBeCloseTo(1e-4, 12);
    sweep.forEach(({ p }) => expect(slack(p)).toBeGreaterThan(0));
  });
});
