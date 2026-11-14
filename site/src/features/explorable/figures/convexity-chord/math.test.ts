import { describe, expect, it } from "vitest";

import {
  CURVE_FUNCTIONS,
  FEASIBLE_BANDS,
  inBands,
  nearestInBands,
  snapPoint,
  chordReading,
  descendFrom,
  globalMinimum,
  quadraticHump,
  slackTrace,
  SWEEP_HALF,
  SWEEP_STEPS,
  sweepReach,
  sweepTheta,
  violationIntervals,
} from "./math";

const quadraticMix = (a: number, b: number) => 0.5 * a + 0.5 * b;

describe("convexity chord", () => {
  const [quadratic, doubleWell, absolute] = CURVE_FUNCTIONS;

  it("never dips below the graph for the convex presets", () => {
    for (const fn of [quadratic, absolute]) {
      for (let a = -2.4; a <= 2.4; a += 0.4) {
        for (let b = -2.4; b <= 2.4; b += 0.4) {
          expect(violationIntervals(fn.f, a, b)).toEqual([]);
        }
      }
    }
  });

  it("finds a violating stretch for the double well across its hump", () => {
    const intervals = violationIntervals(doubleWell.f, -1.5, 1.5);
    expect(intervals.length).toBeGreaterThan(0);
    const [start, end] = intervals[0];
    const reading = chordReading(doubleWell.f, -1.5, 1.5, (start + end) / 2);
    expect(reading.slack).toBeLessThan(0);
  });

  it("mixes inputs and outputs by the same ratio, as in the definition", () => {
    const reading = chordReading(quadratic.f, -2, 2, 0.25);
    expect(reading.mix).toBeCloseTo(0.25 * -2 + 0.75 * 2);
    expect(reading.chord).toBeCloseTo(quadratic.f(-2));
  });

  it("sweeps theta from 0 to 1 and back, one step at a time", () => {
    expect(sweepTheta(0)).toBe(0);
    expect(sweepTheta(SWEEP_HALF)).toBe(1);
    expect(sweepTheta(SWEEP_STEPS)).toBe(0);
    expect(sweepTheta(SWEEP_HALF / 2)).toBeCloseTo(0.5);
    expect(sweepTheta(SWEEP_HALF + SWEEP_HALF / 2)).toBeCloseTo(0.5);
    expect(sweepReach(SWEEP_STEPS)).toBe(1);
    expect(sweepReach(SWEEP_HALF / 2)).toBeCloseTo(0.5);
  });

  it("traces the quadratic gap as the hump 0.35 theta (1 - theta) (a - b)^2", () => {
    const trace = slackTrace(quadratic.f, -1.8, 1.6);
    for (const sample of trace) {
      expect(sample.slack).toBeCloseTo(quadraticHump(0.35, -1.8, 1.6, sample.theta), 12);
    }
    const peak = trace.reduce((best, sample) => (sample.slack > best.slack ? sample : best));
    expect(peak.theta).toBeCloseTo(0.5);
    expect(peak.slack).toBeCloseTo(0.35 * 0.25 * 3.4 ** 2, 12);
    expect(trace[0].slack).toBeCloseTo(0, 12);
    expect(trace.at(-1)!.slack).toBeCloseTo(0, 12);
  });

  it("makes the double-well gap dip below zero between the ends, where the sweep must flash", () => {
    const trace = slackTrace(doubleWell.f, -1.5, 1.5);
    expect(Math.min(...trace.map((sample) => sample.slack))).toBeLessThan(-1);
    expect(trace[0].slack).toBeCloseTo(0, 12);
    expect(trace.at(-1)!.slack).toBeCloseTo(0, 12);
    expect(trace.some((sample) => sample.theta === 0.5 && sample.slack < 0)).toBe(true);
  });

  it("uses the article's pair a = -2, b = 2 with a hump of 1.4 and a = -1 with 0.7875", () => {
    expect([quadratic.defaultA, quadratic.defaultB]).toEqual([-2, 2]);
    expect(quadraticHump(0.35, -2, 2, 0.5)).toBeCloseTo(1.4, 12);
    expect(quadraticHump(0.35, -1, 2, 0.5)).toBeCloseTo(0.7875, 12);
    expect(snapPoint(-1.0400000001)).toBeCloseTo(-1, 12);
    expect(snapPoint(0.349)).toBeCloseTo(0.3, 12);
  });

  it("projects onto C = [-2, -1] ∪ [2, 3] and stops gradient descent at the band's edge", () => {
    expect(inBands(-1.5)).toBe(true);
    expect(inBands(0.5)).toBe(false);
    expect(nearestInBands(0.4)).toBe(-1);
    expect(nearestInBands(0.6)).toBe(2);
    expect(inBands(quadraticMix(-1, 2))).toBe(false);
    const left = descendFrom(quadratic, -2, 0.12, 60, FEASIBLE_BANDS).at(-1)!;
    expect(left).toBeCloseTo(-1, 12);
    const right = descendFrom(quadratic, 3, 0.12, 60, FEASIBLE_BANDS).at(-1)!;
    expect(right).toBeCloseTo(2, 12);
    const best = globalMinimum(quadratic, 2600, FEASIBLE_BANDS);
    expect(best.x).toBeCloseTo(-1, 12);
    expect(best.value).toBeCloseTo(0.55, 12);
    expect(quadratic.f(2)).toBeCloseTo(1.6, 12);
  });

  it("stops in different valleys depending on the start, and only one is global", () => {
    const global = globalMinimum(doubleWell);
    const fromLeft = descendFrom(doubleWell, -2).at(-1)!;
    const fromRight = descendFrom(doubleWell, 2).at(-1)!;

    expect(Math.abs(fromLeft - global.x)).toBeLessThan(0.05);
    expect(Math.abs(fromRight - global.x)).toBeGreaterThan(1);
    expect(doubleWell.f(fromRight)).toBeGreaterThan(global.value + 0.3);
  });
});
