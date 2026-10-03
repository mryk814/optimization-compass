export type Vec3 = readonly [number, number, number];
export interface Obstacle { center: Vec3; radius: number }
export interface Source { title: string; url: string }
export type Metrics = Record<string, number | boolean | string>;
export interface Variant<F> { id: string; label: string; frames: F[]; metrics: Metrics }
export interface SceneData<F> { model: string; sources: Source[]; limitations: string[]; variants: Variant<F>[] }
export interface TopologyFrame {
  iteration: number; density: number[]; compliance: number; volume: number;
  residual: number; maxDisplacement: number;
  nodeDisplacements?: number[][];
}
export interface TopologyData extends SceneData<TopologyFrame> {
  grid: Vec3; spacing: Vec3;
  supports: { axis: string; value: number }[];
  loads: { position: Vec3; force: Vec3 }[];
}
export interface ArmFrame { time: number; joints: number[]; points: Vec3[]; clearance: number }
export interface ArmData extends SceneData<ArmFrame> { obstacles: Obstacle[]; linkLengths: number[]; base: Vec3 }
export interface DroneFrame {
  time: number; position: Vec3; velocity: Vec3; acceleration: Vec3;
  prediction: Vec3[]; trackingError: number; clearance: number;
}
export interface DroneData extends SceneData<DroneFrame> {
  reference: Vec3[]; obstacles: Obstacle[]; target: Vec3; dt: number;
}
export interface SceneDrawing {
  center: Vec3; radius: number;
  boxes?: { center: Vec3; size: Vec3; color: string; opacity?: number }[];
  spheres?: { center: Vec3; radius: number; color: string; opacity?: number }[];
  rods?: { from: Vec3; to: Vec3; radius: number; color: string }[];
  lines?: { points: Vec3[]; color: string; dashed?: boolean }[];
  arrows?: { from: Vec3; direction: Vec3; length: number; color: string }[];
  voxels?: { centers: Vec3[]; colors: string[]; size: Vec3 };
  surface?: { positions: number[]; color: string };
}
