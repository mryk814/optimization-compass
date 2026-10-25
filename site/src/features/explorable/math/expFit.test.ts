import { describe, expect, it } from "vitest";

import { alongStep, cost, pointAfter, runTrials, trialAt } from "./expFit";

// Expected values come from numpy / scipy (scratchpad gnlm_ref.py), the same arithmetic as the articles.
const FAR = { a: 1, k: 0.1 };
const NEAR = { a: 5, k: 0.3 };

describe("exponential fit running example", () => {
  it("starts at cost 11.2494 and ends at the scipy optimum 0.00408177", () => {
    expect(cost(FAR)).toBeCloseTo(11.2494, 4);
    const run = runTrials("lm", FAR, 0.01);
    const end = pointAfter(run, FAR, run.trials.length);
    expect(end.a).toBeCloseTo(5.07867619, 5);
    expect(end.k).toBeCloseTo(0.50493273, 5);
    expect(cost(end)).toBeCloseTo(0.004081770467869126, 9);
  });

  it("Gauss–Newton from the far start overshoots at trial 2: predicted 2.589, actual −26.451", () => {
    const run = runTrials("gn", FAR, 99);
    const [one, two, three] = run.trials;
    expect(one.step.a).toBeCloseTo(3.7459, 4);
    expect(one.step.k).toBeCloseTo(1.0522, 4);
    expect(one.costAfter).toBeCloseTo(2.87032, 5);
    expect(one.rho).toBeCloseTo(0.7595, 4);
    expect(two.predicted).toBeCloseTo(2.58871, 5);
    expect(two.actual).toBeCloseTo(-26.4508, 4);
    expect(two.rho).toBeCloseTo(-10.22, 2);
    expect(two.accepted).toBe(true);
    expect(three.from.k).toBeCloseTo(-0.0253, 4);
    expect(three.costBefore).toBeCloseTo(29.3211, 4);
    expect(run.outcome).toBe("converged");
    expect(run.trials).toHaveLength(8);
  });

  it("Gauss–Newton from the near start converges in 5 steps without any rise", () => {
    const run = runTrials("gn", NEAR, 0);
    expect(run.trials).toHaveLength(5);
    expect(run.trials[0].costAfter).toBeCloseTo(0.0545306, 6);
    expect(run.trials.every((t) => t.rho > 0.9)).toBe(true);
  });

  it("LM at λ=0.01 reproduces the article table: three rejections at one point, then accept at λ=3.33", () => {
    const run = runTrials("lm", FAR, 0.01);
    const rows = run.trials.slice(0, 6);
    expect(rows.map((t) => t.accepted)).toEqual([true, false, false, false, true, true]);
    expect(rows.map((t) => Number(t.lambda.toPrecision(3)))).toEqual([0.01, 0.00333, 0.0333, 0.333, 3.33, 1.11]);
    expect(rows[1].rho).toBeCloseTo(-9.42, 2);
    expect(rows[2].rho).toBeCloseTo(-8.661, 3);
    expect(rows[3].rho).toBeCloseTo(-3.707, 3);
    expect(rows[4].rho).toBeCloseTo(1.395, 3);
    expect(rows[4].costAfter).toBeCloseTo(0.0854991, 6);
    expect(rows[5].rho).toBeCloseTo(1.001, 3);
    // rejected trials leave the current point where it was
    expect(rows[1].from).toEqual(rows[3].from);
    expect(run.trials).toHaveLength(11);
    expect(run.outcome).toBe("converged");
  });

  it("LM at λ=1 never has to reject from the far start", () => {
    const run = runTrials("lm", FAR, 1);
    expect(run.trials.slice(0, 5).every((t) => t.accepted)).toBe(true);
    expect(run.trials[0].costAfter).toBeCloseTo(3.13068, 5);
    expect(run.trials[3].costAfter).toBeCloseTo(0.00408463, 7);
  });

  it("λ turns the Gauss–Newton step into a short steepest-descent step", () => {
    const expected: Array<[number, number, number]> = [
      [0, 3.8909, 48.066],
      [1, 2.216, 44.287],
      [10, 0.50793, 24.769],
      [100, 0.076345, 4.209],
      [1000, 0.0083861, 0.448],
    ];
    for (const [lambda, length, angle] of expected) {
      const trial = trialAt(FAR, lambda, "lm")!;
      expect(trial.stepLength).toBeCloseTo(length, 3);
      expect(trial.descentAngleDeg).toBeCloseTo(angle, 2);
    }
  });

  it("along the Gauss–Newton step the linear model dips to 0.2816 while the true cost climbs to 29.32", () => {
    const two = runTrials("gn", FAR, 0).trials[1];
    expect(alongStep(two, 0).actual).toBeCloseTo(2.87032, 5);
    expect(alongStep(two, 0).model).toBeCloseTo(2.87032, 5);
    expect(alongStep(two, 1).model).toBeCloseTo(0.281608, 5);
    expect(alongStep(two, 1).actual).toBeCloseTo(29.321084, 5);
    expect(alongStep(two, 1).model).toBeCloseTo(two.costBefore - two.predicted, 10);
  });

  it("the steepest-descent direction at the far start is (0.8446, −0.5355)", () => {
    const one = trialAt(FAR, 1000, "lm")!;
    expect(one.gradDir.a).toBeCloseTo(0.84455, 4);
    expect(one.gradDir.k).toBeCloseTo(-0.53548, 4);
  });
});
