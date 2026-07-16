import { useMemo, useState, type KeyboardEvent } from "react";

import type { AlgorithmTrace, TraceFrame, TracePoint } from "../../contracts/trace";
import { objectivePlotSpec, objectiveValue, type ObjectivePlotSpec } from "./objectivePlot";

export interface SurfacePoint {
  x: number;
  y: number;
  z: number;
}

export interface TrajectoryPoint extends SurfacePoint {
  frameIndex: number;
  label: string;
}

interface LinkedSurfaceViewProps {
  trace: AlgorithmTrace;
  currentFrameIndex: number;
  onFrameSelect(frameIndex: number): void;
}

const DEFAULT_AZIMUTH = 315;
const SURFACE_DIVISIONS = 12;

export function LinkedSurfaceView({ trace, currentFrameIndex, onFrameSelect }: LinkedSurfaceViewProps) {
  const [azimuth, setAzimuth] = useState(DEFAULT_AZIMUTH);
  const spec = useMemo(() => objectivePlotSpec(trace.objective), [trace.objective]);
  const mesh = useMemo(() => surfaceMesh(spec, azimuth), [azimuth, spec]);
  const trajectory = useMemo(() => traceTrajectory(trace.frames), [trace.frames]);
  const projectedTrajectory = trajectory.map((point) => ({
    ...point,
    projected: projectSurfacePoint(point, spec, azimuth),
  }));
  const history = projectedTrajectory.filter((point) => point.frameIndex <= currentFrameIndex);
  const current = [...history].reverse().find((point) => point.frameIndex <= currentFrameIndex);
  const path = history.map(({ projected }) => `${projected.x.toFixed(2)},${projected.y.toFixed(2)}`).join(" ");
  const pointLabel = current
    ? `frame ${current.frameIndex + 1}: (${format(current.x)}, ${format(current.y)}), f=${format(current.z)}`
    : `frame ${currentFrameIndex + 1}: 表示できる2次元点なし`;

  const activateFrame = (event: KeyboardEvent<SVGGElement>, frameIndex: number) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    onFrameSelect(frameIndex);
  };

  return (
    <section className="linked-surface-card" aria-labelledby="linked-surface-heading">
      <header>
        <div>
          <p className="eyebrow">Linked 3D · same trace frame</p>
          <h2 id="linked-surface-heading">目的関数の地形と探索位置</h2>
          <p>上の再生frameと同じ点を、等高線の2D表示に加えて高さ f(x, y) でも確認できます。</p>
        </div>
        <label className="surface-camera-control">
          <span>Camera azimuth <output>{azimuth}°</output></span>
          <input
            aria-label="3D表示のカメラ方位"
            max="405"
            min="225"
            onChange={(event) => setAzimuth(Number(event.target.value))}
            step="5"
            type="range"
            value={azimuth}
          />
        </label>
      </header>

      <figure className="linked-surface-figure">
        <svg
          data-current-frame={currentFrameIndex}
          data-testid="linked-objective-surface"
          role="img"
          viewBox="0 0 600 330"
          aria-labelledby="linked-surface-title linked-surface-description"
        >
          <title id="linked-surface-title">{spec.expression}の3D surfaceと探索軌跡</title>
          <desc id="linked-surface-description">
            直交投影した目的関数surface。高さはlog1pで正規化。{pointLabel}。軌跡上の点を選ぶと同じTraceのframeへ移動します。
          </desc>
          <rect className="surface-background" height="330" rx="12" width="600" />
          <g className="surface-mesh" aria-hidden="true">
            {mesh.map((line, index) => (
              <polyline key={index} points={line.map((point) => `${point.x.toFixed(2)},${point.y.toFixed(2)}`).join(" ")} />
            ))}
          </g>
          {path && <polyline className="surface-trajectory" points={path} />}
          <g className="surface-trajectory-points">
            {projectedTrajectory.map((point) => {
              const isCurrent = point.frameIndex === current?.frameIndex;
              const isFuture = point.frameIndex > currentFrameIndex;
              return (
                <g
                  aria-label={`frame ${point.frameIndex + 1}へ移動`}
                  className={`${isCurrent ? "is-current" : ""} ${isFuture ? "is-future" : ""}`}
                  data-frame-index={point.frameIndex}
                  key={point.frameIndex}
                  onClick={() => onFrameSelect(point.frameIndex)}
                  onKeyDown={(event) => activateFrame(event, point.frameIndex)}
                  role="button"
                  tabIndex={0}
                >
                  <circle cx={point.projected.x} cy={point.projected.y} r={isCurrent ? 7 : 3.4} />
                </g>
              );
            })}
          </g>
          <g className="surface-axis-labels" aria-hidden="true">
            <text x="548" y="282">x</text>
            <text x="63" y="282">y</text>
            <text x="300" y="28">f(x, y)</text>
          </g>
        </svg>
        <figcaption>
          <strong>{pointLabel}</strong>
          <span>Projection: orthographic · height: log1p normalized · 2D contour remains the precise fallback.</span>
        </figcaption>
      </figure>
    </section>
  );
}

export function traceTrajectory(frames: readonly TraceFrame[]): TrajectoryPoint[] {
  return frames.flatMap((frame) => {
    const point = representativePoint(frame);
    if (!point || point.coordinates.length < 2 || point.value === null) return [];
    return [{
      frameIndex: frame.frame_index,
      x: point.coordinates[0],
      y: point.coordinates[1],
      z: point.value,
      label: point.label_ja,
    }];
  });
}

export function projectSurfacePoint(
  point: SurfacePoint,
  spec: ObjectivePlotSpec,
  azimuth: number,
): { x: number; y: number } {
  const { bounds } = spec;
  const normalizedX = normalize(point.x, bounds.xMin, bounds.xMax) * 2 - 1;
  const normalizedY = normalize(point.y, bounds.yMin, bounds.yMax) * 2 - 1;
  const clippedZ = Math.min(bounds.zMax, Math.max(bounds.zMin, point.z));
  const normalizedZ = Math.log1p(normalize(clippedZ, bounds.zMin, bounds.zMax) * 9) / Math.log(10);
  const radians = azimuth * Math.PI / 180;
  const horizontal = normalizedX * Math.cos(radians) - normalizedY * Math.sin(radians);
  const depth = normalizedX * Math.sin(radians) + normalizedY * Math.cos(radians);
  return {
    x: 300 + horizontal * 118,
    y: 250 + depth * 53 - normalizedZ * 178,
  };
}

export function surfaceMesh(
  spec: ObjectivePlotSpec,
  azimuth: number,
  divisions = SURFACE_DIVISIONS,
): { x: number; y: number }[][] {
  const lines: { x: number; y: number }[][] = [];
  const { bounds } = spec;
  for (let row = 0; row <= divisions; row += 1) {
    const y = interpolate(bounds.yMin, bounds.yMax, row / divisions);
    lines.push(Array.from({ length: divisions + 1 }, (_, column) => {
      const x = interpolate(bounds.xMin, bounds.xMax, column / divisions);
      return projectSurfacePoint({ x, y, z: objectiveValue(spec, x, y) }, spec, azimuth);
    }));
  }
  for (let column = 0; column <= divisions; column += 1) {
    const x = interpolate(bounds.xMin, bounds.xMax, column / divisions);
    lines.push(Array.from({ length: divisions + 1 }, (_, row) => {
      const y = interpolate(bounds.yMin, bounds.yMax, row / divisions);
      return projectSurfacePoint({ x, y, z: objectiveValue(spec, x, y) }, spec, azimuth);
    }));
  }
  return lines;
}

function representativePoint(frame: TraceFrame): TracePoint | undefined {
  const iterate = frame.points.find((point) => point.role === "iterate" && point.value !== null);
  if (iterate) return iterate;
  return frame.points
    .filter((point): point is TracePoint & { value: number } => point.role === "simplex-vertex" && point.value !== null)
    .sort((left, right) => left.value - right.value)[0];
}

function normalize(value: number, minimum: number, maximum: number): number {
  return (value - minimum) / (maximum - minimum);
}

function interpolate(start: number, end: number, fraction: number): number {
  return start + (end - start) * fraction;
}

function format(value: number): string {
  return Number(value.toPrecision(4)).toString();
}
