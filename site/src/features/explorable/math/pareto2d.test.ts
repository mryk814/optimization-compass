import { describe, expect, it } from "vitest";

import { epsilonChoice, isParetoOptimal, objectives, weightedSum, weightedSumChoice } from "./pareto2d";

describe("bracket with a concave or convex Pareto front", () => {
  it("maps designs to weight and deflection", () => {
    expect(objectives([0.5, 0.5], "concave")).toEqual([0.5, 1.25]);
    expect(objectives([0.5, 0], "concave")).toEqual([0.5, 0.75]);
    expect(isParetoOptimal([0.5, 0.5])).toBe(false);
    expect(isParetoOptimal([0.5, 0])).toBe(true);
  });

  it("jumps between the two ends with a weighted sum on the concave front", () => {
    expect(weightedSumChoice(0.49, "concave")).toEqual([1, 0]);
    expect(weightedSumChoice(0.51, "concave")).toEqual([0, 0]);
    // No interior point beats both ends: the sum is concave along the front.
    for (const w of [0.2, 0.5, 0.8]) {
      const ends = Math.min(weightedSum(objectives([0, 0], "concave"), w), weightedSum(objectives([1, 0], "concave"), w));
      for (let x1 = 0.05; x1 < 1; x1 += 0.05) {
        expect(weightedSum(objectives([x1, 0], "concave"), w)).toBeGreaterThanOrEqual(ends - 1e-12);
      }
    }
  });

  it("slides along the convex front as the weight changes", () => {
    expect(weightedSumChoice(0.5, "convex")[0]).toBeCloseTo(0.25, 12);
    expect(weightedSumChoice(0.3, "convex")[0]).toBe(1);
    expect(weightedSumChoice(0.75, "convex")[0]).toBeCloseTo(1 / 36, 12);
  });

  it("reaches every front point with an ε constraint", () => {
    expect(objectives(epsilonChoice(0.6), "concave")).toEqual([0.6, 1 - 0.36]);
  });
});
