import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { AlgorithmTrace, JsonValue, TraceFrame } from "../../contracts/trace";
import { LinkedSurfaceView, projectSurfacePoint, surfaceMesh, traceTrajectory } from "./LinkedSurfaceView";
import { objectivePlotSpec } from "./objectivePlot";

const objective: Record<string, JsonValue> = {
  family: "quadratic",
  display_expression: "100x^2 + y^2",
  display_range: { x: [-2, 2], y: [-2, 2], z: [0, 500] },
};

const frames = [
  frame(0, [point("simplex-vertex", [1, 1], 101), point("simplex-vertex", [0.5, 1], 26)]),
  frame(1, [point("iterate", [0.25, 0.5], 6.5)]),
];

describe("LinkedSurfaceView", () => {
  it("uses the best simplex vertex and then the iterate as the linked trajectory", () => {
    expect(traceTrajectory(frames)).toEqual([
      expect.objectContaining({ frameIndex: 0, x: 0.5, y: 1, z: 26 }),
      expect.objectContaining({ frameIndex: 1, x: 0.25, y: 0.5, z: 6.5 }),
    ]);
  });

  it("builds a finite mesh whose projection changes with the camera", () => {
    const spec = objectivePlotSpec(objective);
    expect(surfaceMesh(spec, 315, 4)).toHaveLength(10);
    const first = projectSurfacePoint({ x: 1, y: 0, z: 100 }, spec, 315);
    const rotated = projectSurfacePoint({ x: 1, y: 0, z: 100 }, spec, 405);
    expect(Number.isFinite(first.x)).toBe(true);
    expect(first.x).not.toBe(rotated.x);
  });

  it("moves the shared trace frame from a trajectory point", () => {
    const onFrameSelect = vi.fn();
    render(<LinkedSurfaceView currentFrameIndex={0} onFrameSelect={onFrameSelect} trace={{ objective, frames } as unknown as AlgorithmTrace} />);
    fireEvent.click(screen.getByRole("button", { name: "frame 2へ移動" }));
    expect(onFrameSelect).toHaveBeenCalledWith(1);
    expect(screen.getByRole("group", { name: "3D探索軌跡" })).toHaveAttribute("data-current-frame", "0");
  });
});

function point(role: string, coordinates: number[], value: number) {
  return { point_id: `${role}-${coordinates.join("-")}`, role, coordinates, value, label_ja: role, label_en: role };
}

function frame(frameIndex: number, points: ReturnType<typeof point>[]): TraceFrame {
  return {
    frame_index: frameIndex,
    iteration: frameIndex,
    oracle_evaluations: frameIndex + 1,
    elapsed_steps: frameIndex,
    elapsed_time_ms: frameIndex,
    event_type: "step",
    decision: "accepted",
    explanation_key: "trace.test.step",
    event_label_ja: "step",
    event_label_en: "step",
    keyframe: true,
    points,
    vectors: [],
    metrics: [],
    payload: {},
  };
}
