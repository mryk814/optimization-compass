import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
  type RefObject,
} from "react";

import type { Bounds } from "./math/contours";

/** Maps domain coordinates (y up) to SVG pixels (y down) and back. */
export interface Viewport {
  width: number;
  height: number;
  bounds: Bounds;
}

export interface Scale {
  px(x: number): number;
  py(y: number): number;
  ix(px: number): number;
  iy(py: number): number;
}

export function makeScale({ width, height, bounds }: Viewport): Scale {
  const sx = width / (bounds.xMax - bounds.xMin);
  const sy = height / (bounds.yMax - bounds.yMin);
  return {
    px: (x) => (x - bounds.xMin) * sx,
    py: (y) => height - (y - bounds.yMin) * sy,
    ix: (px) => bounds.xMin + px / sx,
    iy: (py) => bounds.yMin + (height - py) / sy,
  };
}

const FALLBACK_WIDTH = 660;
const MIN_WIDTH = 240;

/**
 * Sizes a figure to the width it is actually given, so one SVG unit is one CSS pixel.
 * A fixed viewBox would shrink axis labels and handles on a phone below the readable size;
 * here the geometry is recomputed instead and text keeps its typographic size.
 */
export interface CompactLayout {
  /** Width in CSS pixels below which the compact bounds replace the default ones. */
  below: number;
  bounds: Bounds;
  aspect: number;
}

export function useStageViewport(bounds: Bounds, aspect: number, compact?: CompactLayout) {
  const ref = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(FALLBACK_WIDTH);
  useEffect(() => {
    const element = ref.current;
    if (!element) return undefined;
    const measure = () => {
      const measured = Math.round(element.clientWidth);
      if (measured > 0) setWidth(Math.max(MIN_WIDTH, measured));
    };
    measure();
    if (typeof ResizeObserver === "undefined") return undefined;
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, []);
  const useCompact = compact !== undefined && width < compact.below;
  const chosenBounds = useCompact ? compact.bounds : bounds;
  const chosenAspect = useCompact ? compact.aspect : aspect;
  const viewport = useMemo<Viewport>(
    () => ({ width, height: Math.round(width * chosenAspect), bounds: chosenBounds }),
    [width, chosenAspect, chosenBounds],
  );
  return { ref, viewport };
}

export const clamp =(value: number, low: number, high: number) => Math.min(high, Math.max(low, value));

export function segmentsPath(
  segments: ReadonlyArray<readonly [number, number, number, number]>,
  scale: Scale,
): string {
  return segments
    .map(([x1, y1, x2, y2]) => (
      `M${scale.px(x1).toFixed(1)} ${scale.py(y1).toFixed(1)}L${scale.px(x2).toFixed(1)} ${scale.py(y2).toFixed(1)}`
    ))
    .join("");
}

export function polylinePath(points: ReadonlyArray<readonly [number, number]>, scale: Scale): string {
  return points
    .map(([x, y], index) => `${index === 0 ? "M" : "L"}${scale.px(x).toFixed(1)} ${scale.py(y).toFixed(1)}`)
    .join("");
}

interface DragOptions {
  svgRef: RefObject<SVGSVGElement | null>;
  viewport: Viewport;
  /** Receives the pointer position in domain coordinates while the handle is held. */
  onDrag(x: number, y: number): void;
}

/** Pointer handlers for a draggable SVG handle. Keyboard control stays with the component. */
export function useDomainDrag({ svgRef, viewport, onDrag }: DragOptions) {
  const dragging = useRef(false);
  const locate = useCallback((event: ReactPointerEvent) => {
    const svg = svgRef.current;
    if (!svg) return undefined;
    const rect = svg.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return undefined;
    const scale = makeScale(viewport);
    const px = ((event.clientX - rect.left) / rect.width) * viewport.width;
    const py = ((event.clientY - rect.top) / rect.height) * viewport.height;
    return { x: scale.ix(px), y: scale.iy(py) };
  }, [svgRef, viewport]);

  return {
    onPointerDown(event: ReactPointerEvent<SVGElement>) {
      dragging.current = true;
      event.currentTarget.setPointerCapture?.(event.pointerId);
      event.preventDefault();
    },
    onPointerMove(event: ReactPointerEvent<SVGElement>) {
      if (!dragging.current) return;
      const point = locate(event);
      if (point) onDrag(point.x, point.y);
    },
    onPointerUp(event: ReactPointerEvent<SVGElement>) {
      dragging.current = false;
      event.currentTarget.releasePointerCapture?.(event.pointerId);
    },
  };
}
