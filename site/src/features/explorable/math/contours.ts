export interface Bounds {
  xMin: number;
  xMax: number;
  yMin: number;
  yMax: number;
}

/** One line segment in domain coordinates: x1, y1, x2, y2. */
export type Segment = readonly [number, number, number, number];

type Edge = "top" | "right" | "bottom" | "left";

// Corner bits: a (top-left) = 1, b (top-right) = 2, c (bottom-right) = 4, d (bottom-left) = 8.
// Each entry lists the edge pairs a level line connects inside a cell.
const CASES: ReadonlyArray<ReadonlyArray<readonly [Edge, Edge]>> = [
  [],
  [["left", "top"]],
  [["top", "right"]],
  [["left", "right"]],
  [["right", "bottom"]],
  [["left", "top"], ["right", "bottom"]],
  [["top", "bottom"]],
  [["left", "bottom"]],
  [["left", "bottom"]],
  [["top", "bottom"]],
  [["top", "right"], ["left", "bottom"]],
  [["right", "bottom"]],
  [["left", "right"]],
  [["top", "right"]],
  [["left", "top"]],
  [],
];

/**
 * Marching squares: the level set `fn(x, y) = level` as short segments.
 * Cells are sampled on a regular grid, so the outline is exact only up to the grid step.
 */
export function contourSegments(
  fn: (x: number, y: number) => number,
  bounds: Bounds,
  level: number,
  columns: number,
  rows: number,
): Segment[] {
  const dx = (bounds.xMax - bounds.xMin) / columns;
  const dy = (bounds.yMax - bounds.yMin) / rows;
  const samples = new Float64Array((columns + 1) * (rows + 1));
  for (let row = 0; row <= rows; row += 1) {
    for (let column = 0; column <= columns; column += 1) {
      samples[row * (columns + 1) + column] = fn(bounds.xMin + column * dx, bounds.yMin + row * dy);
    }
  }
  const at = (column: number, row: number) => samples[row * (columns + 1) + column];
  const segments: Segment[] = [];
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      const x0 = bounds.xMin + column * dx;
      const y0 = bounds.yMin + row * dy;
      const a = at(column, row);
      const b = at(column + 1, row);
      const c = at(column + 1, row + 1);
      const d = at(column, row + 1);
      const code = (a >= level ? 1 : 0) | (b >= level ? 2 : 0) | (c >= level ? 4 : 0) | (d >= level ? 8 : 0);
      if (code === 0 || code === 15) continue;
      const point = (edge: Edge): [number, number] => {
        switch (edge) {
          case "top": return [x0 + dx * fraction(level, a, b), y0];
          case "bottom": return [x0 + dx * fraction(level, d, c), y0 + dy];
          case "left": return [x0, y0 + dy * fraction(level, a, d)];
          case "right": return [x0 + dx, y0 + dy * fraction(level, b, c)];
        }
      };
      for (const [from, to] of CASES[code]) {
        const [x1, y1] = point(from);
        const [x2, y2] = point(to);
        segments.push([x1, y1, x2, y2]);
      }
    }
  }
  return segments;
}

function fraction(level: number, from: number, to: number): number {
  const span = to - from;
  return span === 0 ? 0.5 : Math.min(1, Math.max(0, (level - from) / span));
}
