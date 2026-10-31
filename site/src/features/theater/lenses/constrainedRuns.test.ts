import { describe, expect, it } from "vitest";

import {
  CONSTRAINED_ITERATIONS,
  CONSTRAINED_OPTIMUM,
  CONSTRAINED_START,
  constrainedSnapshotAt,
  constraint2,
  isFeasible,
  objective2,
  projectOntoDisc,
  runConstrainedLenses,
} from "./constrainedRuns";

describe("constrained lens runs", () => {
  const runs = runConstrainedLenses();
  const last = (id: keyof typeof runs) => runs[id].snapshots.at(-1)!.steps.at(-1)!;

  it("starts every run at the same feasible point and runs the same iterations", () => {
    expect(isFeasible(CONSTRAINED_START)).toBe(true);
    for (const run of Object.values(runs)) {
      expect(run.snapshots).toHaveLength(CONSTRAINED_ITERATIONS + 1);
      expect(run.snapshots[0].steps[0].point).toEqual(CONSTRAINED_START);
      expect(constrainedSnapshotAt(run, CONSTRAINED_ITERATIONS).steps).toHaveLength(CONSTRAINED_ITERATIONS + 1);
    }
  });

  it("the objective-only run leaves the feasible region, because it never reads the constraint", () => {
    expect(isFeasible(last("objective-only").point)).toBe(false);
    expect(objective2(last("objective-only").point)).toBeLessThan(objective2(CONSTRAINED_OPTIMUM));
  });

  it("the projection run never leaves the disc and ends near the constrained optimum", () => {
    for (const s of runs.projection.snapshots.at(-1)!.steps) expect(isFeasible(s.point)).toBe(true);
    const end = last("projection").point;
    expect(Math.hypot(end[0] - CONSTRAINED_OPTIMUM[0], end[1] - CONSTRAINED_OPTIMUM[1])).toBeLessThan(0.02);
  });

  it("the penalty run ends with a smaller violation than the objective-only run", () => {
    expect(last("penalty").violation).toBeLessThan(last("objective-only").violation);
  });

  it("projects outside points onto the circle and leaves inside points alone", () => {
    expect(projectOntoDisc([1.2, 1.1])).toEqual([1.2, 1.1]);
    expect(constraint2(projectOntoDisc([-1, -1]))).toBeCloseTo(0, 12);
  });

});
