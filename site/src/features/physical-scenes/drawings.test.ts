import { describe, expect, it } from "vitest";
import arm from "./data/arm.json";
import drone from "./data/drone.json";
import topology from "./data/topology.json";
import { armDrawing, droneDrawing, topologyDrawing } from "./drawings";
import type { ArmData, DroneData, TopologyData } from "./types";

describe("computed 3D scenes", () => {
  it("preserves calculated arm link lengths at every exported pose", () => {
    const data = arm as unknown as ArmData;
    data.variants.forEach((run, variant) => run.frames.forEach((frame, step) => {
      const drawing = armDrawing(data, variant, step, false);
      drawing.rods!.forEach((rod, index) => {
        expect(Math.hypot(...rod.to.map((value, axis) => value - rod.from[axis]))).toBeCloseTo(data.linkLengths[index], 5);
      });
      expect(frame.clearance).toBeGreaterThan(0);
    }));
  });
  it("shows the actual MPC prediction instead of inventing a curve", () => {
    const data = drone as unknown as DroneData;
    data.variants.forEach((run, variant) => run.frames.forEach((frame, step) => {
      const drawing = droneDrawing(data, variant, step, false);
      expect(drawing.lines![2].points).toEqual(frame.prediction);
      expect(drawing.lines![1].points.at(-1)).toEqual(frame.position);
      expect(frame.prediction[0]).toEqual(frame.position);
      if (step < run.frames.length - 1) frame.prediction[1].forEach((value, axis) => {
        expect(value).toBeCloseTo(run.frames[step + 1].position[axis], 5);
      });
    }));
  });
  it("frames both complete arm motions, including the obstacle and link thickness", () => {
    const data = arm as unknown as ArmData;
    const drawing = armDrawing(data, 0, 0, false);
    const distance = (point: readonly number[]) => Math.hypot(...point.map((value, axis) => value - drawing.center[axis]));
    for (const run of data.variants) for (const frame of run.frames) for (const point of frame.points) {
      expect(distance(point) + 0.065).toBeLessThanOrEqual(drawing.radius);
    }
    for (const obstacle of data.obstacles) {
      expect(distance(obstacle.center) + obstacle.radius).toBeLessThanOrEqual(drawing.radius);
    }
    expect(armDrawing(data, 1, 60, true).center).toEqual(drawing.center);
    expect(armDrawing(data, 1, 60, true).radius).toEqual(drawing.radius);
  });
  it("keeps FE state and metrics fixed while changing the display threshold or deformation", () => {
    const data = topology as unknown as TopologyData;
    const before = JSON.stringify(data);
    const last = data.variants[1].frames.length - 1;
    const low = topologyDrawing(data, 1, last, 0.2, false);
    const high = topologyDrawing(data, 1, last, 0.6, false);
    const deformed = topologyDrawing(data, 1, last, 0.2, true);
    expect(low.voxels!.centers.length).toBeGreaterThan(high.voxels!.centers.length);
    expect(low.surface!.positions).not.toEqual(deformed.surface!.positions);
    expect(deformed.surface!.positions.every(Number.isFinite)).toBe(true);
    expect(JSON.stringify(data)).toEqual(before);
  });
  it("records successful solves and valid frame dimensions for every condition", () => {
    for (const data of [arm, drone]) for (const run of data.variants) {
      if (typeof run.metrics.solverSuccess === "boolean") expect(run.metrics.solverSuccess).toBe(true);
      else expect(run.metrics.solverSuccess).toBe(run.frames.length - 1);
      expect(run.frames.every(frame => Number.isFinite(frame.time) && frame.clearance >= 0)).toBe(true);
    }
    for (const run of topology.variants) for (const frame of run.frames) {
      expect(frame.density.length).toBe(topology.grid.reduce((a, b) => a * b, 1));
      expect(frame.residual).toBeLessThan(1e-8);
      expect(frame.volume).toBeCloseTo(run.metrics.volumeFraction, 6);
    }
  });
});
