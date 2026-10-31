/**
 * Greedy placement of small text labels beside markers so that, at any figure width, a label
 * touches neither another marker, nor an axis label, nor a label placed before it.
 *
 * Boxes are in SVG pixels. A label is tried at eight positions around its marker; the position
 * with the least overlap wins, and the first position with no overlap is taken immediately.
 */

export interface Box {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

export type Anchor = "start" | "middle" | "end";

export interface LabelRequest {
  /** Marker centre. */
  cx: number;
  cy: number;
  /** Half-size of the marker. */
  radius: number;
  /** Text box size in px. */
  width: number;
  height: number;
}

export interface PlacedLabel {
  x: number;
  y: number;
  anchor: Anchor;
  box: Box;
  /** Total overlap area with obstacles and earlier labels; 0 means a clean placement. */
  overlap: number;
}

const GAP = 3;

export function overlapArea(a: Box, b: Box): number {
  const w = Math.min(a.x1, b.x1) - Math.max(a.x0, b.x0);
  const h = Math.min(a.y1, b.y1) - Math.max(a.y0, b.y0);
  return w > 0 && h > 0 ? w * h : 0;
}

/** Extra distance of the second ring of candidate positions. */
const OUTER = 14;

function candidates(request: LabelRequest): ReadonlyArray<Omit<PlacedLabel, "overlap">> {
  const { cx, cy, radius, width, height } = request;
  const make = (x0: number, y0: number, anchor: Anchor): Omit<PlacedLabel, "overlap"> => ({
    x: anchor === "start" ? x0 : anchor === "end" ? x0 + width : x0 + width / 2,
    y: y0 + height - 3,
    anchor,
    box: { x0, y0, x1: x0 + width, y1: y0 + height },
  });
  return [0, OUTER].flatMap((extra) => {
    const g = radius + GAP + extra;
    return [
      make(cx + g, cy - g - height + 4, "start"), // NE
      make(cx + g, cy - height / 2, "start"), // E
      make(cx + g, cy + g - 4, "start"), // SE
      make(cx - width / 2, cy - g - height, "middle"), // N
      make(cx - width / 2, cy + g, "middle"), // S
      make(cx - g - width, cy - g - height + 4, "end"), // NW
      make(cx - g - width, cy - height / 2, "end"), // W
      make(cx - g - width, cy + g - 4, "end"), // SW
    ];
  });
}

export function placeLabel(
  request: LabelRequest,
  obstacles: readonly Box[],
  bounds: Box,
): PlacedLabel {
  let best: PlacedLabel | null = null;
  for (const candidate of candidates(request)) {
    const outside =
      Math.max(0, bounds.x0 - candidate.box.x0) * 50 +
      Math.max(0, candidate.box.x1 - bounds.x1) * 50 +
      Math.max(0, bounds.y0 - candidate.box.y0) * 50 +
      Math.max(0, candidate.box.y1 - bounds.y1) * 50;
    const overlap = obstacles.reduce((sum, box) => sum + overlapArea(candidate.box, box), 0) + outside;
    if (best === null || overlap < best.overlap) best = { ...candidate, overlap };
    if (overlap === 0) break;
  }
  return best as PlacedLabel;
}

/** Marker box used as an obstacle for other labels. */
export function markerBox(cx: number, cy: number, radius: number): Box {
  return { x0: cx - radius, y0: cy - radius, x1: cx + radius, y1: cy + radius };
}

/** Places labels one after another; each placed label becomes an obstacle for the next. */
export function placeLabels(
  requests: readonly LabelRequest[],
  fixedObstacles: readonly Box[],
  bounds: Box,
): PlacedLabel[] {
  const markers = requests.map((request) => markerBox(request.cx, request.cy, request.radius + 1));
  const placed: PlacedLabel[] = [];
  requests.forEach((request, index) => {
    const own = markers.filter((_, other) => other !== index);
    const earlier = placed.map((label) => label.box);
    placed.push(placeLabel(request, [...fixedObstacles, ...own, ...earlier], bounds));
  });
  return placed;
}
