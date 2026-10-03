import { useMemo } from "react";

import {
  fitToBox,
  normalizedHeight,
  projectPoint,
  surfaceQuads,
  type Camera,
  type SurfaceSpec,
} from "./math/surface3d";

/** A point to draw on the surface, in domain coordinates; its height is read from the surface. */
export interface SurfaceMark {
  x: number;
  y: number;
}

interface Surface3DProps {
  spec: SurfaceSpec;
  camera: Camera;
  width: number;
  height: number;
  /** A path walked on the surface (e.g. iterates). Points outside the bounds end the path. */
  path?: readonly SurfaceMark[];
  current?: SurfaceMark;
  /** Points to label, e.g. the minimum. */
  marks?: ReadonlyArray<SurfaceMark & { label: string }>;
  /** Names of the two floor axes, written beside the floor edges so the reader keeps orientation. */
  axes?: { x: string; y: string };
}

// Low ground is teal (where the objective is small), high ground fades to the page colour.
const LOW: readonly [number, number, number] = [26, 120, 112];
const HIGH: readonly [number, number, number] = [244, 238, 222];

function shade(height: number, light: number): string {
  const tone = 0.62 + 0.38 * light;
  const mix = LOW.map((low, index) => (low + (HIGH[index] - low) * Math.sqrt(height)) * tone);
  return `rgb(${mix.map((value) => Math.round(value)).join(",")})`;
}

function inside(mark: SurfaceMark, spec: SurfaceSpec): boolean {
  const { bounds } = spec;
  return mark.x >= bounds.xMin && mark.x <= bounds.xMax && mark.y >= bounds.yMin && mark.y <= bounds.yMax;
}

/**
 * Shaded surface under an orthographic camera. Heights are clipped and log1p-compressed
 * (see `math/surface3d.ts`); the caller states this in the panel caption.
 */
export function Surface3D({ spec, camera, width, height, path = [], current, marks = [], axes }: Surface3DProps) {
  const quads = useMemo(() => surfaceQuads(spec, camera), [spec, camera]);
  const toPixel = useMemo(() => fitToBox(camera, width, height), [camera, width, height]);
  const place = (mark: SurfaceMark, lift = 0.012) => toPixel(
    projectPoint(mark.x, mark.y, normalizedHeight(spec.fn(mark.x, mark.y), spec) + lift, spec.bounds, camera),
  );
  const shownPath: SurfaceMark[] = [];
  for (const mark of path) {
    if (!inside(mark, spec)) break;
    shownPath.push(mark);
  }
  const pathPoints = shownPath.map((mark) => place(mark).map((value) => value.toFixed(1)).join(",")).join(" ");
  return (
    <svg className="ex-svg ex-surface" viewBox={`0 0 ${width} ${height}`}>
      <rect className="ex-ground" height={height} width={width} />
      <g>
        {quads.map((quad, index) => (
          <polygon
            fill={shade(quad.height, quad.light)}
            key={index}
            points={quad.corners.map((corner) => toPixel(corner).map((value) => value.toFixed(1)).join(",")).join(" ")}
            stroke={shade(quad.height, quad.light)}
            strokeWidth={0.6}
          />
        ))}
      </g>
      {shownPath.length > 1 && <polyline className="ex-surface-path" points={pathPoints} />}
      {shownPath.map((mark, index) => {
        const [x, y] = place(mark);
        return <circle className="ex-surface-dot" cx={x} cy={y} key={index} r={3} />;
      })}
      {marks.filter((mark) => inside(mark, spec)).map((mark) => {
        const [x, y] = place(mark);
        return (
          <g className="ex-minimum" key={mark.label}>
            <circle cx={x} cy={y} r={5} />
            <text x={x + 8} y={y - 8}>{mark.label}</text>
          </g>
        );
      })}
      {axes && <FloorAxes axes={axes} camera={camera} spec={spec} toPixel={toPixel} />}
      {current && inside(current, spec) && (() => {
        const [x, y] = place(current, 0.02);
        return <circle className="ex-head" cx={x} cy={y} r={7} />;
      })()}
    </svg>
  );
}

/** Labels the floor edge nearest to the viewer along x and along y. */
function FloorAxes({ axes, camera, spec, toPixel }: {
  axes: { x: string; y: string };
  camera: Camera;
  spec: SurfaceSpec;
  toPixel: (point: ReturnType<typeof projectPoint>) => readonly [number, number];
}) {
  const { bounds } = spec;
  const midX = (bounds.xMin + bounds.xMax) / 2;
  const midY = (bounds.yMin + bounds.yMax) / 2;
  const nearer = (a: [number, number], b: [number, number]) => (
    projectPoint(a[0], a[1], 0, bounds, camera).depth > projectPoint(b[0], b[1], 0, bounds, camera).depth ? a : b
  );
  const xEdge = nearer([midX, bounds.yMin], [midX, bounds.yMax]);
  const yEdge = nearer([bounds.xMin, midY], [bounds.xMax, midY]);
  const at = ([x, y]: [number, number]) => toPixel(projectPoint(x, y, 0, bounds, camera));
  const [xx, xy] = at(xEdge);
  const [yx, yy] = at(yEdge);
  return (
    <g className="ex-surface-axes">
      <text textAnchor="middle" x={xx} y={xy + 18}>{axes.x} →</text>
      <text textAnchor="middle" x={yx} y={yy + 18}>{axes.y} →</text>
    </g>
  );
}
