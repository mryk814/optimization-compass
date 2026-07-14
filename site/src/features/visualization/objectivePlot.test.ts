import { describe, expect, test } from "vitest";

import {
  contourSegments,
  normalizedVectorEnd,
  objectivePlotSpec,
  objectiveValue,
} from "./objectivePlot";

describe("objective plot metadata", () => {
  test("uses objective-owned bounds and creates finite quadratic contours", () => {
    const spec = objectivePlotSpec({
      family: "quadratic",
      display_expression: "f(x, y) = 100x² + y²",
      display_range: { x: [-4, 4], y: [-3, 5], z: [0, 1600] },
    });

    expect(spec.bounds).toEqual({ xMin: -4, xMax: 4, yMin: -3, yMax: 5, zMin: 0, zMax: 1600 });
    expect(objectiveValue(spec, 2, 3)).toBe(409);
    const contours = contourSegments(spec, 12, 10);
    expect(contours.length).toBeGreaterThan(20);
    expect(contours.every((segment) => Number.isFinite(segment.start.x + segment.end.y))).toBe(true);
  });

  test("rejects invalid metadata instead of falling back to component bounds", () => {
    expect(() => objectivePlotSpec({
      family: "quadratic",
      display_expression: "f",
      display_range: { x: [1, -1], y: [-1, 1], z: [0, 2] },
    })).toThrow("must increase");
  });

  test("normalizes a vector for legible direction without mutating objective coordinates", () => {
    const end = normalizedVectorEnd([0, 0], [200, 2], {
      xMin: -4,
      xMax: 4,
      yMin: -4,
      yMax: 4,
      zMin: 0,
      zMax: 1600,
    });

    expect(end[0]).toBeCloseTo(1.2799, 3);
    expect(end[1]).toBeCloseTo(0.0128, 3);
  });
});
