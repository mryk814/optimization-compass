import type { JsonValue } from "../../contracts/trace";

export interface PlotBounds {
  xMin: number;
  xMax: number;
  yMin: number;
  yMax: number;
  zMin: number;
  zMax: number;
}

export interface PlotPoint {
  x: number;
  y: number;
}

export interface ContourSegment {
  level: number;
  start: PlotPoint;
  end: PlotPoint;
}

export interface ObjectivePlotSpec {
  family: "quadratic" | "rosenbrock";
  expression: string;
  bounds: PlotBounds;
}

export function objectivePlotSpec(objective: Record<string, JsonValue>): ObjectivePlotSpec {
  const family = objective.family;
  if (family !== "quadratic" && family !== "rosenbrock") {
    throw new Error(`Unsupported objective family for explanatory plot: ${String(family)}.`);
  }
  const displayRange = record(objective.display_range, "objective.display_range");
  const x = finitePair(displayRange.x, "objective.display_range.x");
  const y = finitePair(displayRange.y, "objective.display_range.y");
  const z = finitePair(displayRange.z, "objective.display_range.z");
  if (x[0] >= x[1] || y[0] >= y[1] || z[0] >= z[1]) {
    throw new Error("Objective display ranges must increase.");
  }
  if (typeof objective.display_expression !== "string" || !objective.display_expression.trim()) {
    throw new Error("Objective display expression is required.");
  }
  return {
    family,
    expression: objective.display_expression,
    bounds: {
      xMin: x[0],
      xMax: x[1],
      yMin: y[0],
      yMax: y[1],
      zMin: z[0],
      zMax: z[1],
    },
  };
}

export function objectiveValue(spec: ObjectivePlotSpec, x: number, y: number): number {
  if (spec.family === "quadratic") return 100 * x * x + y * y;
  return 100 * (y - x * x) ** 2 + (1 - x) ** 2;
}

export function contourSegments(
  spec: ObjectivePlotSpec,
  columns = 28,
  rows = 22,
): ContourSegment[] {
  const levels = [0.001, 0.004, 0.016, 0.064, 0.256, 0.72].map(
    (fraction) => spec.bounds.zMin + (spec.bounds.zMax - spec.bounds.zMin) * fraction,
  );
  const xStep = (spec.bounds.xMax - spec.bounds.xMin) / columns;
  const yStep = (spec.bounds.yMax - spec.bounds.yMin) / rows;
  const segments: ContourSegment[] = [];
  for (const level of levels) {
    for (let row = 0; row < rows; row += 1) {
      for (let column = 0; column < columns; column += 1) {
        const x0 = spec.bounds.xMin + column * xStep;
        const x1 = x0 + xStep;
        const y0 = spec.bounds.yMin + row * yStep;
        const y1 = y0 + yStep;
        const corners = [
          { x: x0, y: y0, value: objectiveValue(spec, x0, y0) },
          { x: x1, y: y0, value: objectiveValue(spec, x1, y0) },
          { x: x1, y: y1, value: objectiveValue(spec, x1, y1) },
          { x: x0, y: y1, value: objectiveValue(spec, x0, y1) },
        ];
        const crossings = [
          interpolate(corners[0], corners[1], level),
          interpolate(corners[1], corners[2], level),
          interpolate(corners[2], corners[3], level),
          interpolate(corners[3], corners[0], level),
        ].filter((point): point is PlotPoint => point !== undefined);
        if (crossings.length === 2) {
          segments.push({ level, start: crossings[0], end: crossings[1] });
        } else if (crossings.length === 4) {
          segments.push(
            { level, start: crossings[0], end: crossings[1] },
            { level, start: crossings[2], end: crossings[3] },
          );
        }
      }
    }
  }
  return segments;
}

export function mapX(value: number, bounds: PlotBounds, start: number, end: number): number {
  return start + ((value - bounds.xMin) / (bounds.xMax - bounds.xMin)) * (end - start);
}

export function mapY(value: number, bounds: PlotBounds, start: number, end: number): number {
  return end - ((value - bounds.yMin) / (bounds.yMax - bounds.yMin)) * (end - start);
}

export function normalizedVectorEnd(
  origin: readonly number[],
  components: readonly number[],
  bounds: PlotBounds,
  fraction = 0.16,
): [number, number] {
  const norm = Math.hypot(components[0] ?? 0, components[1] ?? 0);
  if (norm === 0) return [origin[0], origin[1]];
  const scale = Math.min(bounds.xMax - bounds.xMin, bounds.yMax - bounds.yMin) * fraction / norm;
  return [origin[0] + components[0] * scale, origin[1] + components[1] * scale];
}

function interpolate(
  start: PlotPoint & { value: number },
  end: PlotPoint & { value: number },
  level: number,
): PlotPoint | undefined {
  const startDelta = start.value - level;
  const endDelta = end.value - level;
  if ((startDelta > 0 && endDelta > 0) || (startDelta < 0 && endDelta < 0)) return undefined;
  if (start.value === end.value) return undefined;
  const ratio = (level - start.value) / (end.value - start.value);
  if (ratio < 0 || ratio > 1) return undefined;
  return {
    x: start.x + (end.x - start.x) * ratio,
    y: start.y + (end.y - start.y) * ratio,
  };
}

function record(value: JsonValue | undefined, field: string): Record<string, JsonValue> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error(`${field} must be an object.`);
  }
  return value;
}

function finitePair(value: JsonValue | undefined, field: string): [number, number] {
  if (
    !Array.isArray(value)
    || value.length !== 2
    || value.some((item) => typeof item !== "number" || !Number.isFinite(item))
  ) {
    throw new Error(`${field} must be a finite pair.`);
  }
  return [value[0] as number, value[1] as number];
}
