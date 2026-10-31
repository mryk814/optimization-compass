import { describe, expect, it } from "vitest";

import { acceptedPath, alongStep, cost, costHistory, observationReadings, pointAfter, runTrials, trialAt } from "./expFit";

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

  it("LM trial 2 along its step: the linear model ends at 0.2707 while the true cost dips to 0.0227 near s=0.57 and ends at 27.19", () => {
    const two = runTrials("lm", FAR, 0.01).trials[1];
    expect(alongStep(two, 1).model).toBeCloseTo(0.2707, 4);
    expect(alongStep(two, 1).actual).toBeCloseTo(27.1935, 4);
    expect(alongStep(two, 0.568).actual).toBeCloseTo(0.0227, 3);
    // the true cost comes back up to the starting cost at s≈0.78: only about three quarters of the step is safe
    expect(alongStep(two, 0.784).actual).toBeCloseTo(two.costBefore, 1);
  });

  it("the first trial's angle to steepest descent is 48.06° at λ=0.001 and 48.03° at the default λ=0.01", () => {
    expect(trialAt(FAR, 0.001, "lm")!.descentAngleDeg).toBeCloseTo(48.06, 2);
    expect(trialAt(FAR, 0.01, "lm")!.descentAngleDeg).toBeCloseTo(48.03, 2);
  });

  it("the damping-free steps scale by μ/(μ+λ) along the eigen-directions of JᵀJ (0.970 and 3.590 at the trial 2–4 point)", () => {
    const point = runTrials("lm", FAR, 0.01).trials[1].from;
    const step = (lambda: number) => trialAt(point, lambda, "lm")!.stepLength;
    expect(step(0)).toBeCloseTo(1.2002, 3);
    expect(step(0.0033333) / step(0)).toBeCloseTo(0.9993, 3);
    expect(step(0.33333) / step(0)).toBeCloseTo(0.9148, 3);
    expect(step(3.3333)).toBeCloseTo(0.6221, 3);
  });

  it("LM from the near start never rejects and ends in 5 trials with ρ between 0.975 and 1.010", () => {
    const run = runTrials("lm", NEAR, 0.01);
    expect(run.trials).toHaveLength(5);
    expect(run.trials.every((t) => t.accepted)).toBe(true);
    const rho = run.trials.map((t) => t.rho);
    expect(Math.min(...rho)).toBeCloseTo(0.975, 3);
    expect(Math.max(...rho)).toBeCloseTo(1.01, 2);
  });

  it("acceptedPath lists the start and each accepted candidate; the Gauss–Newton path overshoots to k=−0.025", () => {
    const gn = runTrials("gn", FAR, 0);
    const path = acceptedPath(gn, FAR);
    expect(path).toHaveLength(gn.trials.length + 1);
    expect(path[2].k).toBeCloseTo(-0.0253, 4);
    expect(path[2].a).toBeCloseTo(5.0331, 4);
    const lm = runTrials("lm", FAR, 0.01);
    expect(acceptedPath(lm, FAR, 5)).toHaveLength(3);
  });

  it("costHistory keeps the accepted line flat across rejections and lists the rejected costs apart", () => {
    const lm = runTrials("lm", FAR, 0.01);
    const history = costHistory(lm, FAR, 5);
    expect(history.current.map((p) => p.n)).toEqual([0, 1, 2, 3, 4, 5]);
    expect(history.current[1].cost).toBeCloseTo(2.854553, 6);
    expect(history.current[2].cost).toBeCloseTo(2.854553, 6);
    expect(history.current[4].cost).toBeCloseTo(2.854553, 6);
    expect(history.current[5].cost).toBeCloseTo(0.085499, 6);
    expect(history.rejected.map((p) => p.n)).toEqual([2, 3, 4]);
    expect(history.rejected.map((p) => Number(p.cost.toFixed(4)))).toEqual([27.1935, 25.2307, 12.3648]);
    const gn = costHistory(runTrials("gn", FAR, 0), FAR, 3);
    expect(gn.rejected).toHaveLength(0);
    expect(gn.current[2].cost).toBeCloseTo(29.3211, 4);
  });
});

describe("per-observation reading of a trial", () => {
  it("shows the linearization opening up at trial 1 of Gauss–Newton from the far start", () => {
    const [one] = runTrials("gn", FAR, 0).trials;
    const readings = observationReadings(one);
    // y + r + Jp and y + r(x+p), from scipy (scratchpad fix2_numbers.py).
    const linear = [4.74592, 3.34220, 2.16266, 1.17736, 0.35999];
    const actual = [4.74592, 1.49940, 0.47371, 0.14966, 0.04728];
    readings.forEach((reading, index) => {
      expect(reading.linearized).toBeCloseTo(linear[index], 4);
      expect(reading.actual).toBeCloseTo(actual[index], 4);
    });
    // At t = 0 the amplitude is linear, so the two agree exactly.
    expect(readings[0].linearized).toBeCloseTo(readings[0].actual, 9);
  });
});
