import { describe, expect, it } from "vitest";

import {
  basinOf,
  gridArgmin,
  LENS_BUDGET,
  lensObjective,
  runAllLenses,
  snapshotAt,
} from "./lensRuns";

describe("lens runs", () => {
  const runs = runAllLenses();

  it("spends exactly the shared budget and includes the shared start x = 0", () => {
    for (const run of Object.values(runs)) {
      const last = run.snapshots[run.snapshots.length - 1];
      expect(last.evaluations).toHaveLength(LENS_BUDGET);
      expect(last.evaluations.some((item) => item.x === 0)).toBe(true);
      last.evaluations.forEach((item, index) => {
        expect(item.index).toBe(index + 1);
        expect(item.y).toBeCloseTo(lensObjective(item.x), 12);
      });
    }
  });

  it("records only what the method has seen at each count", () => {
    for (const run of Object.values(runs)) {
      for (let t = 0; t <= LENS_BUDGET; t += 1) {
        expect(snapshotAt(run, t).evaluations.length).toBeLessThanOrEqual(t);
      }
    }
  });

  it("gradient lens pays one probe evaluation per slope", () => {
    const evaluations = runs.gradient.snapshots.at(-1)!.evaluations;
    expect(evaluations.filter((item) => item.purpose === "probe")).toHaveLength(LENS_BUDGET / 2);
  });

  it("states a stuck-basin signal only when the final best is outside the global basin", () => {
    const best = runs.gradient.snapshots.at(-1)!.best!;
    const stuck = basinOf(best.x) !== basinOf(gridArgmin());
    expect(runs.gradient.events.some((event) => event.kind === "stuck_in_basin")).toBe(stuck);
  });

  it("is deterministic", () => {
    const again = runAllLenses();
    expect(again.population.snapshots.at(-1)!.evaluations).toEqual(runs.population.snapshots.at(-1)!.evaluations);
    expect(again.surrogate.snapshots.at(-1)!.evaluations).toEqual(runs.surrogate.snapshots.at(-1)!.evaluations);
  });
});
