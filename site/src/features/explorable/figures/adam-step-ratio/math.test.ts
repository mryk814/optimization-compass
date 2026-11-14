import { describe, expect, it } from "vitest";

import { ADAM_DEFAULTS, runAdam, seededNormal } from "./math";

const VALLEY = { cx: 1, cy: -2, kappa: 20 } as const;

describe("Adam math", () => {
  it("repeats the same noise for the same seed", () => {
    const first = seededNormal(7);
    const second = seededNormal(7);
    expect([first(), first(), first()]).toEqual([second(), second(), second()]);
  });

  it("moves every coordinate by η on the first step, whatever the gradient size", () => {
    const run = runAdam(VALLEY, [4, 3], { ...ADAM_DEFAULTS, eta: 0.08, noise: 0, seed: 1, maxSteps: 3 });
    expect(run.path[1][0]).toBeCloseTo(3.92, 6);
    expect(run.path[1][1]).toBeCloseTo(2.92, 6);
  });
});
