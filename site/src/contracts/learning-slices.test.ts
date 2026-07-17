import { describe, expect, test } from "vitest";

import paretoPayload from "../../public/data/visualizations/biobjective-quadratic-pareto-front.json";
import feasiblePayload from "../../public/data/visualizations/constrained-disk-feasible-region.json";
import { parseLearningSliceArtifact } from "./learning-slices";

describe("learning-slice artifact parser", () => {
  test("parses both generated renderer families with canonical identity", () => {
    const feasible = parseLearningSliceArtifact(feasiblePayload);
    const pareto = parseLearningSliceArtifact(paretoPayload);

    expect(feasible.renderer_family).toBe("feasible_region");
    expect(feasible.dataset_version).toBe("0.12.0");
    if (feasible.renderer_family !== "feasible_region") throw new Error("unexpected family");
    expect(feasible.paths.map((path) => path.role)).toEqual([
      "constraint_aware",
      "unconstrained_failure",
    ]);
    expect(pareto.renderer_family).toBe("pareto_front");
    expect(pareto.dataset_version).toBe("0.12.0");
    if (pareto.renderer_family !== "pareto_front") throw new Error("unexpected family");
    expect(pareto.pareto_front.every((point) => !point.dominated)).toBe(true);
  });

  test("fails closed on an unknown family and a dominated Pareto-front point", () => {
    expect(() => parseLearningSliceArtifact({
      ...feasiblePayload,
      renderer_family: "method_specific_renderer",
    })).toThrow(/Unsupported learning-slice renderer/u);

    expect(() => parseLearningSliceArtifact({
      ...paretoPayload,
      pareto_front: [{ ...paretoPayload.pareto_front[0], dominated: true }],
    })).toThrow(/dominated point/u);
  });
});
