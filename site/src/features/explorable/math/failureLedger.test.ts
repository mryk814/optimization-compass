import { describe, expect, it } from "vitest";

import {
  BUDGET,
  halfSummaries,
  LEDGER,
  objectiveValue,
  PENALTY_CHOICES,
  probeVerdict,
  ranking,
  tally,
} from "./failureLedger";

// Reference values come from an exact-rational script (fractions.Fraction), not from this module:
// pa016_numbers.py in the article's working notes; its outputs are quoted in the article's code block.
describe("failure ledger values", () => {
  it("computes successful values from the lesson objective", () => {
    expect(objectiveValue(0.65, 0.35, 0)).toBeCloseTo(0, 12);
    expect(objectiveValue(0.45, 0.1, 0)).toBeCloseTo(0.1025, 12);
    expect(objectiveValue(0.6, 0.3, 0)).toBeCloseTo(0.005, 12);
    expect(objectiveValue(0.7, 0.42, 1)).toBeCloseTo(0.0874, 12);
    expect(objectiveValue(0.82, 0.62, 1)).toBeCloseTo(0.1818, 12);
  });

  it("keeps every failure value-free and every success inside the toy's success region", () => {
    expect(LEDGER.map((row) => row.status)).toEqual([
      "ok", "crash", "ok", "timeout", "ok", "ok", "nonphysical",
    ]);
    for (const row of LEDGER) {
      expect(row.value === null).toBe(row.status !== "ok");
      if (row.status === "ok") expect(row.u1 + row.u2).toBeGreaterThanOrEqual(0.25);
    }
  });
});

describe("tally: failed calls still use the budget", () => {
  it("7 calls = 4 successes + 3 failures, 13 of 20 left", () => {
    const t = tally(7);
    expect(t).toEqual({ spent: 7, ok: 4, crash: 1, timeout: 1, nonphysical: 1, failed: 3, remaining: 13 });
    expect(BUDGET - t.ok).toBe(16);
  });

  it("follows the prefix", () => {
    expect(tally(1)).toMatchObject({ spent: 1, ok: 1, failed: 0, remaining: 19 });
    expect(tally(2)).toMatchObject({ spent: 2, ok: 1, crash: 1, remaining: 18 });
  });
});

describe("halfSummaries", () => {
  it("status policy: only successes are averaged", () => {
    const [left, right] = halfSummaries(7, "status", 10);
    expect(left).toMatchObject({ evaluations: 3, used: 1 });
    expect(left.mean).toBeCloseTo(0.1025, 12);
    expect(right).toMatchObject({ evaluations: 4, used: 3 });
    expect(right.mean).toBeCloseTo(0.0308, 12);
  });

  it("penalty 10 turns the u1<0.5 half into 6.7008 and the u1≥0.5 half into 2.5231", () => {
    const [left, right] = halfSummaries(7, "penalty", 10);
    expect(left.mean).toBeCloseTo(6.700833333, 8);
    expect(right.mean).toBeCloseTo(2.5231, 12);
  });

  it("matches the reference table for the other penalties", () => {
    const expected: ReadonlyArray<readonly [number, number, number]> = [
      [0, 0.0341666667, 0.0231],
      [0.05, 0.0675, 0.0356],
      [0.1, 0.1008333333, 0.0481],
      [1, 0.7008333333, 0.2731],
      [100, 66.7008333333, 25.0231],
      [1_000_000, 666666.7008333333, 250000.0231],
    ];
    for (const [penalty, leftMean, rightMean] of expected) {
      expect(PENALTY_CHOICES).toContain(penalty);
      const [left, right] = halfSummaries(7, "penalty", penalty);
      expect(left.mean).toBeCloseTo(leftMean, 6);
      expect(right.mean).toBeCloseTo(rightMean, 6);
    }
  });
});

describe("ranking", () => {
  it("status policy: the best of the recorded successes is call 1 with value 0", () => {
    const r = ranking(7, "status", 10);
    expect(r.bestValue).toBeCloseTo(0, 12);
    expect(r.bestCalls).toEqual([1]);
    expect(r.topThree.map((item) => item.call)).toEqual([1, 5, 6]);
    expect(r.successSpread).toBeCloseTo(0.1025, 12);
    expect(r.spreadShare).toBeCloseTo(1, 12);
  });

  it("penalty 10 leaves the best at 0 but squeezes the successes into 1.025% of the recorded range", () => {
    const r = ranking(7, "penalty", 10);
    expect(r.bestCalls).toEqual([1]);
    expect(r.recordedMax - r.recordedMin).toBeCloseTo(10, 12);
    expect(r.spreadShare).toBeCloseTo(0.01025, 12);
  });

  it("penalty 1,000,000 squeezes them to 1.025e-7", () => {
    expect(ranking(7, "penalty", 1_000_000).spreadShare).toBeCloseTo(1.025e-7, 15);
  });

  it("penalty 0 ties a crashed, a timed-out and a nonphysical call with the real best", () => {
    expect(ranking(7, "penalty", 0).bestCalls).toEqual([1, 2, 4, 7]);
  });

  it("penalty 0.05 puts a crash ahead of a real result in the top three", () => {
    const r = ranking(7, "penalty", 0.05);
    expect(r.topThree.map((item) => item.call)).toEqual([1, 5, 2]);
    expect(r.topThree[2].status).toBe("crash");
  });

  it("has no spread with one success", () => {
    const r = ranking(1, "status", 10);
    expect(r.successSpread).toBeNull();
    expect(r.spreadShare).toBeNull();
  });
});

describe("probeVerdict", () => {
  it("a point outside [0, 1] is a known violation, decided without running anything", () => {
    const v = probeVerdict(1.1, 0.5, 7, "status", 10);
    expect(v).toEqual({ kind: "known_violation", reasons: ["u₁が範囲 [0, 1] の外"] });
    const both = probeVerdict(-0.1, 1.2, 7, "status", 10);
    expect(both.kind === "known_violation" && both.reasons.length).toBe(2);
  });

  it("(0.20, 0.04): the nearest record is the crash (0.051 away); the nearest success is call 3 (0.2571 away)", () => {
    const v = probeVerdict(0.2, 0.04, 7, "status", 10);
    if (v.kind !== "unknown") throw new Error("expected unknown");
    expect(v.nearest).toMatchObject({ call: 2, status: "crash", value: null });
    expect(v.nearest.distance).toBeCloseTo(0.051, 3);
    expect(v.nearestSuccess.call).toBe(3);
    expect(v.nearestSuccess.distance).toBeCloseTo(0.2571, 4);
    expect(v.guess).toEqual({ kind: "none" });
  });

  it("the penalty policy answers the same probe with the penalty value", () => {
    const v = probeVerdict(0.2, 0.04, 7, "penalty", 10);
    if (v.kind !== "unknown") throw new Error("expected unknown");
    expect(v.guess).toEqual({ kind: "value", value: 10, replaced: true });
  });

  it("(0.55, 0.25): nearest is the success of call 5 (value 0.005)", () => {
    const v = probeVerdict(0.55, 0.25, 7, "status", 10);
    if (v.kind !== "unknown") throw new Error("expected unknown");
    expect(v.nearest.call).toBe(5);
    expect(v.nearest.distance).toBeCloseTo(0.0707, 4);
    expect(v.guess).toMatchObject({ kind: "value", replaced: false });
  });

  it("only the calls made so far count", () => {
    const v = probeVerdict(0.2, 0.04, 1, "status", 10);
    if (v.kind !== "unknown") throw new Error("expected unknown");
    expect(v.nearest.call).toBe(1);
  });
});
