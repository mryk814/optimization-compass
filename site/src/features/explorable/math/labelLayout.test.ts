import { describe, expect, it } from "vitest";

import { markerBox, overlapArea, placeLabel, placeLabels, type Box } from "./labelLayout";

const BOUNDS: Box = { x0: 0, y0: 0, x1: 300, y1: 300 };

describe("label layout", () => {
  it("takes the first free position and leaves a lone marker's label beside it", () => {
    const label = placeLabel({ cx: 100, cy: 100, radius: 5, width: 8, height: 18 }, [], BOUNDS);

    expect(label.overlap).toBe(0);
    expect(label.anchor).toBe("start");
    expect(label.box.x0).toBeGreaterThan(100);
  });

  it("keeps labels of three markers 11–16 px apart off each other and off every marker", () => {
    const requests = [
      { cx: 150, cy: 100, radius: 5, width: 8, height: 18 },
      { cx: 139, cy: 111, radius: 5, width: 8, height: 18 },
      { cx: 161, cy: 89, radius: 5, width: 8, height: 18 },
    ];

    const placed = placeLabels(requests, [], BOUNDS);

    placed.forEach((label, index) => {
      expect(label.overlap).toBe(0);
      requests.forEach((request, other) => {
        expect(overlapArea(label.box, markerBox(request.cx, request.cy, request.radius))).toBe(0);
        if (other > index) expect(overlapArea(label.box, placed[other].box)).toBe(0);
      });
    });
  });

  it("avoids a fixed text box and stays inside the bounds", () => {
    const fixed: Box = { x0: 105, y0: 80, x1: 140, y1: 120 };
    const label = placeLabel({ cx: 100, cy: 100, radius: 5, width: 8, height: 18 }, [fixed], BOUNDS);

    expect(overlapArea(label.box, fixed)).toBe(0);
    const edge = placeLabel({ cx: 297, cy: 4, radius: 5, width: 40, height: 18 }, [], BOUNDS);
    expect(edge.box.x1).toBeLessThanOrEqual(BOUNDS.x1);
    expect(edge.box.y0).toBeGreaterThanOrEqual(BOUNDS.y0);
  });
});
