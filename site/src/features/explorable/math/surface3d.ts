import type { Bounds } from "./contours";

/**
 * A height field drawn as shaded, filled quads under an orthographic camera.
 *
 * The domain is normalized to a square [-1, 1]², so a figure keeps its proportions whatever
 * the units of x and y. Heights are clipped to [zFloor, zCeil] and compressed with log1p so a
 * deep narrow valley and a high plateau fit in one picture; the figure must say so in its
 * caption, because heights are then not to scale.
 */
export interface SurfaceSpec {
  bounds: Bounds;
  fn(x: number, y: number): number;
  zFloor: number;
  zCeil: number;
  /** Cells per side. 32-40 keeps an SVG figure light and still reads as a smooth surface. */
  resolution: number;
  /**
   * How clipped heights map to the drawn height. "log" (the default) compresses high ground so
   * a deep, narrow valley stays visible; "linear" keeps differences between shallow valleys.
   */
  heightMode?: "log" | "linear";
}

export interface Camera {
  /** Rotation about the vertical axis, in degrees. 0 looks along +y. */
  azimuthDeg: number;
  /** Angle above the horizon, in degrees. */
  elevationDeg: number;
}

export interface Projected {
  /** Screen coordinates in the unit frame; `fitToBox` maps them to pixels. */
  sx: number;
  sy: number;
  /** Larger is closer to the viewer. */
  depth: number;
}

export interface SurfaceQuad {
  corners: readonly Projected[];
  depth: number;
  /** Mean normalized height in [0, 1]: 0 at zFloor, 1 at zCeil. */
  height: number;
  /** Lambert shading in [0, 1]. */
  light: number;
}

const HEIGHT_SCALE = 0.75;
const LIGHT = normalize([-0.45, -0.55, 0.7]);

/** Clipped height in [0, 1], compressed with log1p unless the spec asks for a linear scale. */
export function normalizedHeight(
  z: number,
  spec: Pick<SurfaceSpec, "zFloor" | "zCeil" | "heightMode">,
): number {
  const clipped = Math.min(Math.max(z, spec.zFloor), spec.zCeil);
  const unit = (clipped - spec.zFloor) / (spec.zCeil - spec.zFloor);
  return spec.heightMode === "linear" ? unit : Math.log1p(unit * 9) / Math.log(10);
}

/** Domain point to the normalized cube: x, y in [-1, 1], height in [0, HEIGHT_SCALE]. */
function toCube(x: number, y: number, h: number, bounds: Bounds): [number, number, number] {
  return [
    ((x - bounds.xMin) / (bounds.xMax - bounds.xMin)) * 2 - 1,
    ((y - bounds.yMin) / (bounds.yMax - bounds.yMin)) * 2 - 1,
    h * HEIGHT_SCALE,
  ];
}

function view([x, y, z]: readonly [number, number, number], camera: Camera): Projected {
  const az = (camera.azimuthDeg * Math.PI) / 180;
  const el = (camera.elevationDeg * Math.PI) / 180;
  const across = x * Math.cos(az) - y * Math.sin(az);
  const away = x * Math.sin(az) + y * Math.cos(az);
  return {
    sx: across,
    sy: -(z * Math.cos(el) + away * Math.sin(el)),
    depth: -away * Math.cos(el) + z * Math.sin(el),
  };
}

/** Projects a domain point with an already normalized height in [0, 1]. */
export function projectPoint(
  x: number,
  y: number,
  height: number,
  bounds: Bounds,
  camera: Camera,
): Projected {
  return view(toCube(x, y, height, bounds), camera);
}

export function surfaceQuads(spec: SurfaceSpec, camera: Camera): SurfaceQuad[] {
  const { bounds, resolution: n } = spec;
  const heights: number[][] = [];
  for (let i = 0; i <= n; i += 1) {
    heights.push([]);
    for (let j = 0; j <= n; j += 1) {
      const x = bounds.xMin + ((bounds.xMax - bounds.xMin) * i) / n;
      const y = bounds.yMin + ((bounds.yMax - bounds.yMin) * j) / n;
      heights[i].push(normalizedHeight(spec.fn(x, y), spec));
    }
  }
  const cube = (i: number, j: number) => toCube(
    bounds.xMin + ((bounds.xMax - bounds.xMin) * i) / n,
    bounds.yMin + ((bounds.yMax - bounds.yMin) * j) / n,
    heights[i][j],
    bounds,
  );
  const quads: SurfaceQuad[] = [];
  for (let i = 0; i < n; i += 1) {
    for (let j = 0; j < n; j += 1) {
      const points = [cube(i, j), cube(i + 1, j), cube(i + 1, j + 1), cube(i, j + 1)];
      const normal = normalize(cross(subtract(points[2], points[0]), subtract(points[3], points[1])));
      const corners = points.map((point) => view(point, camera));
      quads.push({
        corners,
        depth: corners.reduce((total, corner) => total + corner.depth, 0) / 4,
        height: (heights[i][j] + heights[i + 1][j] + heights[i + 1][j + 1] + heights[i][j + 1]) / 4,
        light: Math.max(0, dot(normal, LIGHT)),
      });
    }
  }
  // Painter's algorithm: far quads first, so nearer ones cover them.
  return quads.sort((left, right) => left.depth - right.depth);
}

/** Pixel transform that fits the whole box (floor to the top of the height range) in view. */
export function fitToBox(camera: Camera, width: number, height: number, padding = 12) {
  const corners: Projected[] = [];
  for (const x of [-1, 1]) {
    for (const y of [-1, 1]) {
      for (const z of [0, HEIGHT_SCALE]) corners.push(view([x, y, z], camera));
    }
  }
  const xs = corners.map((corner) => corner.sx);
  const ys = corners.map((corner) => corner.sy);
  const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  const scale = Math.min((width - 2 * padding) / (x1 - x0), (height - 2 * padding) / (y1 - y0));
  const offsetX = (width - (x1 - x0) * scale) / 2 - x0 * scale;
  const offsetY = (height - (y1 - y0) * scale) / 2 - y0 * scale;
  return (point: Projected) => [point.sx * scale + offsetX, point.sy * scale + offsetY] as const;
}

function subtract(a: readonly number[], b: readonly number[]): number[] {
  return a.map((value, index) => value - b[index]);
}

function cross(a: readonly number[], b: readonly number[]): number[] {
  return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
}

function dot(a: readonly number[], b: readonly number[]): number {
  return a.reduce((total, value, index) => total + value * b[index], 0);
}

function normalize(a: readonly number[]): number[] {
  const length = Math.hypot(...a) || 1;
  return a.map((value) => value / length);
}
