import { describe, expect, test } from "vitest";

import paretoPayload from "../../public/data/visualizations/biobjective-quadratic-pareto-front.json";
import feasiblePayload from "../../public/data/visualizations/constrained-disk-feasible-region.json";
import topologyPayload from "../../public/data/visualizations/topology-optimization-field-evolution.json";
import releasePayload from "../../public/data/release.json";
import { parseLearningSliceArtifact } from "./learning-slices";
import { buildFieldEvolutionPayload } from "./field-evolution";

describe("learning-slice artifact parser", () => {
  test("parses both generated renderer families with canonical identity", () => {
    const feasible = parseLearningSliceArtifact(feasiblePayload);
    const pareto = parseLearningSliceArtifact(paretoPayload);

    expect(feasible.renderer_family).toBe("feasible_region");
    expect(feasible.dataset_version).toBe(releasePayload.dataset_version);
    if (feasible.renderer_family !== "feasible_region") throw new Error("unexpected family");
    expect(feasible.paths.map((path) => path.role)).toEqual([
      "constraint_aware",
      "unconstrained_failure",
    ]);
    expect(pareto.renderer_family).toBe("pareto_front");
    expect(pareto.dataset_version).toBe(releasePayload.dataset_version);
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

  test("adapts the field artifact to a deterministic shared payload", () => {
    const artifact = parseLearningSliceArtifact(topologyPayload);
    if (artifact.renderer_family !== "field_evolution") throw new Error("Topology fixture is invalid");

    const first = buildFieldEvolutionPayload(artifact);
    const second = buildFieldEvolutionPayload(artifact);

    expect(first).toEqual(second);
    expect(first.progress_axis).toEqual({ id: "optimizer_iterations", unit: "iterations" });
    expect(first.observables.map((observable) => observable.observable_id)).toEqual([
      "design_field", "state_field", "sensitivity_field", "objective_value", "mesh_quality",
    ]);
    expect(first.event_markers.some((marker) => marker.event_type === "checkerboard_risk" && marker.severity === "warning")).toBe(true);
    expect(first.static_fallback.facts.length).toBeGreaterThanOrEqual(2);
    expect(first.static_fallback.artifact_kind).toBe("executable_trace");
    expect(first.static_fallback.execution_status).toBe("executable_teaching_trace");
    expect(first.static_fallback.event_marker_ids.every((id) => first.event_markers.some((marker) => marker.marker_id === id))).toBe(true);
  });
});
