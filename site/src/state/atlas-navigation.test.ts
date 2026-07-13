import { describe, expect, test } from "vitest";

import type { AtlasStateV1 } from "./atlas-state";
import { buildAtlasNavigation } from "./atlas-navigation";

const state: AtlasStateV1 = {
  stateVersion: 1,
  datasetVersion: "0.2.0",
  viewId: "problem-structure",
  viewVersion: "1.0.0",
  answers: {},
};

describe("Atlas cross-route navigation", () => {
  test("preserves every non-state query parameter and replaces only state", () => {
    const result = buildAtlasNavigation(
      "/map",
      "?keep=1&tag=a&state=stale&tag=b",
      state,
    );

    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const params = new URLSearchParams(result.to.search);
    expect(result.to.pathname).toBe("/map");
    expect(params.get("keep")).toBe("1");
    expect(params.getAll("tag")).toEqual(["a", "b"]);
    expect(params.get("state")).not.toBe("stale");
  });

  test("returns a recoverable error without a partial URL when encoding fails", () => {
    const result = buildAtlasNavigation("/map", "?keep=1", {
      ...state,
      selectedNodeId: "x".repeat(2000),
    });

    expect(result.ok).toBe(false);
    if (result.ok) return;
    expect(result.error.name).toBe("AtlasStateUrlTooLongError");
    expect(result).not.toHaveProperty("to");
  });
});
