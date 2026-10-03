import type { ArmData, DroneData, SceneDrawing, TopologyData, Vec3 } from "./types";
import { densitySurface } from "./isosurface";

export const COLORS = { structure: "#233d55", accepted: "#177e82", update: "#cc7728", ghost: "#b8c7d3", obstacle: "#7c7994" };
// The FE model uses y as the load's vertical direction; the view uses z-up.
const feView = ([x, y, z]: Vec3): Vec3 => [x, z, y];

export function topologyDrawing(data: TopologyData, variant: number, frameIndex: number, threshold: number, deformation: boolean): SceneDrawing {
  const frame = data.variants[variant].frames[frameIndex];
  const [nx, ny, nz] = data.grid; const [sx, sy, sz] = data.spacing;
  const centers: Vec3[] = []; const colors: string[] = [];
  const scale = deformation && frame.nodeDisplacements ? ny * sy * 0.12 / Math.max(frame.maxDisplacement, 1e-12) : 0;
  frame.density.forEach((density, index) => {
    if (density < threshold) return;
    const x = index % nx; const y = Math.floor(index / nx) % ny; const z = Math.floor(index / (nx * ny));
    let dx = 0; let dy = 0; let dz = 0;
    if (scale && frame.nodeDisplacements) {
      for (let a = 0; a <= 1; a++) for (let b = 0; b <= 1; b++) for (let c = 0; c <= 1; c++) {
        const displacement = frame.nodeDisplacements[x + a + (nx + 1) * (y + b + (ny + 1) * (z + c))];
        dx += displacement[0] / 8; dy += displacement[1] / 8; dz += displacement[2] / 8;
      }
    }
    centers.push(feView([(x + 0.5) * sx + dx * scale, (y + 0.5) * sy + dy * scale, (z + 0.5) * sz + dz * scale]));
    colors.push(`hsl(183, ${32 + density * 32}%, ${78 - density * 48}%)`);
  });
  const corners: Vec3[] = [
    [0, 0, 0], [nx * sx, 0, 0], [nx * sx, ny * sy, 0], [0, ny * sy, 0], [0, 0, 0],
    [0, 0, nz * sz], [nx * sx, 0, nz * sz], [nx * sx, ny * sy, nz * sz], [0, ny * sy, nz * sz], [0, 0, nz * sz],
  ];
  const mesh = densitySurface(frame.density, data.grid, data.spacing, threshold);
  const transformed: number[] = [];
  const transformVertex = (i: number): Vec3 => {
    const point: number[] = [mesh.positions[i], mesh.positions[i + 1], mesh.positions[i + 2]];
    if (scale && frame.nodeDisplacements) {
      const unit = point.map((v, axis) => Math.max(0, Math.min(data.grid[axis] - 1e-8, v / data.spacing[axis])));
      const lower = unit.map(Math.floor); const fraction = unit.map((v, axis) => v - lower[axis]);
      for (let a = 0; a <= 1; a++) for (let b = 0; b <= 1; b++) for (let c = 0; c <= 1; c++) {
        const weight = (a ? fraction[0] : 1 - fraction[0]) * (b ? fraction[1] : 1 - fraction[1]) * (c ? fraction[2] : 1 - fraction[2]);
        const displacement = frame.nodeDisplacements[lower[0] + a + (nx + 1) * (lower[1] + b + (ny + 1) * (lower[2] + c))];
        point.forEach((_, axis) => { point[axis] += scale * weight * displacement[axis]; });
      }
    }
    return feView(point as unknown as Vec3);
  };
  // Swapping y/z reflects the coordinates, so reverse each triangle's winding.
  for (let i = 0; i < mesh.positions.length; i += 9) {
    transformed.push(...transformVertex(i), ...transformVertex(i + 6), ...transformVertex(i + 3));
  }
  return {
    center: feView([nx * sx / 2, ny * sy / 2, nz * sz / 2]), radius: nx * sx * 0.62,
    boxes: [{ center: feView([-0.3, ny * sy / 2, nz * sz / 2]), size: [0.4, nz * sz + 0.6, ny * sy + 0.6], color: COLORS.structure, opacity: 0.35 }],
    lines: [{ points: corners.map(feView), color: COLORS.ghost }],
    arrows: data.loads.filter((_, i) => i % 2 === 0).map(load => ({ from: feView(load.position), direction: feView(load.force), length: sy * 2.2, color: COLORS.update })),
    voxels: { centers, colors, size: [sx * 0.94, sz * 0.94, sy * 0.94] },
    surface: { positions: transformed, color: COLORS.accepted },
  };
}

export function armDrawing(data: ArmData, variant: number, step: number, compare: boolean): SceneDrawing {
  const run = data.variants[variant]; const frame = run.frames[step];
  const tip = (points: Vec3[]) => points[points.length - 1];
  const lines: NonNullable<SceneDrawing["lines"]> = [
    { points: run.frames.map(f => tip(f.points)), color: COLORS.ghost, dashed: true },
    { points: run.frames.slice(0, step + 1).map(f => tip(f.points)), color: COLORS.accepted },
  ];
  if (compare) lines.push({ points: data.variants[1 - variant].frames.map(f => tip(f.points)), color: COLORS.update, dashed: true });
  // Keep one frame around both complete motions, including link thickness and obstacles.
  const allPoints = data.variants.flatMap(v => v.frames.flatMap(f => f.points));
  const expand = (point: Vec3, amount: number): Vec3 => [point[0] + amount, point[1] + amount, point[2] + amount];
  const extents: Vec3[] = [
    ...allPoints.flatMap(p => [-1, 1].map(sign => expand(p, sign * 0.065))),
    ...data.obstacles.flatMap(o => [-1, 1].map(sign => expand(o.center, sign * o.radius))),
    [data.base[0] - 0.12, data.base[1] - 0.12, 0],
    [data.base[0] + 0.12, data.base[1] + 0.12, data.base[2]],
  ];
  const mins = [0, 1, 2].map(axis => Math.min(...extents.map(p => p[axis])));
  const maxs = [0, 1, 2].map(axis => Math.max(...extents.map(p => p[axis])));
  const center: Vec3 = [(mins[0] + maxs[0]) / 2, (mins[1] + maxs[1]) / 2, (mins[2] + maxs[2]) / 2];
  const radius = Math.hypot(...maxs.map((value, axis) => (value - mins[axis]) / 2));
  return {
    center, radius,
    boxes: [{ center: [data.base[0], data.base[1], data.base[2] / 2], size: [0.24, 0.24, data.base[2]], color: COLORS.structure }],
    spheres: [
      ...data.obstacles.map(o => ({ ...o, color: COLORS.obstacle, opacity: 0.35 })),
      ...frame.points.map(p => ({ center: p, radius: 0.065, color: COLORS.structure })),
      { center: tip(run.frames[0].points), radius: 0.04, color: COLORS.ghost },
      { center: tip(run.frames[run.frames.length - 1].points), radius: 0.08, color: COLORS.update },
    ],
    rods: frame.points.slice(1).map((to, i) => ({ from: frame.points[i], to, radius: 0.045, color: COLORS.accepted })),
    lines,
  };
}

export function droneDrawing(data: DroneData, variant: number, step: number, compare: boolean): SceneDrawing {
  const run = data.variants[variant]; const frame = run.frames[step];
  const [x, y, z] = frame.position;
  const lines: NonNullable<SceneDrawing["lines"]> = [
    { points: data.reference, color: COLORS.ghost, dashed: true },
    { points: run.frames.slice(0, step + 1).map(f => f.position), color: COLORS.accepted },
    { points: frame.prediction, color: COLORS.update },
  ];
  if (compare) lines.push({ points: data.variants[1 - variant].frames.map(f => f.position), color: COLORS.structure, dashed: true });
  // Align the cross with the thrust direction implied by the translational acceleration.
  const thrust = [frame.acceleration[0], frame.acceleration[1], frame.acceleration[2] + 9.81];
  const normalLength = Math.hypot(...thrust);
  const normal = thrust.map(value => value / normalLength);
  const u: Vec3 = [normal[2], 0, -normal[0]];
  const uLength = Math.hypot(...u);
  const a = u.map(value => value / uLength);
  const b = [normal[1] * a[2] - normal[2] * a[1], normal[2] * a[0] - normal[0] * a[2], normal[0] * a[1] - normal[1] * a[0]];
  const end = (axis: number[], sign: number): Vec3 => [x + axis[0] * sign * 0.16, y + axis[1] * sign * 0.16, z + axis[2] * sign * 0.16];
  const rotorPositions = [end(a, 1), end(a, -1), end(b, 1), end(b, -1)];
  const all = data.reference;
  const mins = [0, 1, 2].map(axis => Math.min(...all.map(p => p[axis])));
  const maxs = [0, 1, 2].map(axis => Math.max(...all.map(p => p[axis])));
  return {
    center: mins.map((v, i) => (v + maxs[i]) / 2) as unknown as Vec3,
    radius: Math.max(...maxs.map((v, i) => v - mins[i])) * 0.7,
    spheres: [
      ...data.obstacles.map(o => ({ ...o, color: COLORS.obstacle, opacity: 0.35 })),
      { center: frame.position, radius: 0.085, color: COLORS.accepted },
      ...rotorPositions.map(center => ({ center, radius: 0.055, color: COLORS.structure })),
      { center: data.target, radius: 0.08, color: COLORS.update },
    ],
    rods: [a, b].map(axis => ({ from: end(axis, -1), to: end(axis, 1), radius: 0.018, color: COLORS.structure })),
    lines,
  };
}
