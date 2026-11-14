import { describe, expect, it } from "vitest";

import { gridMinimum, posterior } from "./bayesOpt";

describe("Bayesian optimisation math", () => {
  it("interpolates the observations and is uncertain far from them", () => {
    const xs = [0.1, 0.45, 0.6];
    const ys = [1, 0.5, 1.1];
    const post = posterior(xs, ys, 0.1, [0.1, 0.45, 0.95]);
    expect(post.mean[0]).toBeCloseTo(1, 3);
    expect(post.mean[1]).toBeCloseTo(0.5, 3);
    expect(post.sd[0]).toBeLessThan(0.01);
    expect(post.sd[2]).toBeGreaterThan(0.9 * Math.max(...post.sd));
  });

  it("places the answer key's minimum in the narrow basin", () => {
    const minimum = gridMinimum();
    expect(minimum.x).toBeCloseTo(0.84, 10);
    expect(minimum.value).toBeCloseTo(-0.1496, 3);
  });
});
