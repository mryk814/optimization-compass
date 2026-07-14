import { act, renderHook } from "@testing-library/react";
import type { PropsWithChildren } from "react";
import { MemoryRouter, useLocation, useNavigate } from "react-router-dom";
import { describe, expect, test } from "vitest";

import {
  AtlasStateUrlTooLongError,
  encodeAtlasState,
  type AtlasCompatibilityCatalog,
  type AtlasStateV1,
} from "./atlas-state";
import { useAtlasState } from "./useAtlasState";

const catalog: AtlasCompatibilityCatalog = {
  datasetVersion: "0.2.0",
  viewId: "problem-structure",
  viewVersion: "1.0.0",
  nodeIds: new Set(["A", "B"]),
  questions: {},
};

function wrapper(initialEntry: string) {
  return function Wrapper({ children }: PropsWithChildren) {
    return <MemoryRouter initialEntries={[initialEntry]}>{children}</MemoryRouter>;
  };
}

function useHarness() {
  return { atlas: useAtlasState(catalog), location: useLocation(), navigate: useNavigate() };
}

describe("useAtlasState", () => {
  test("creates initial state without adding a token", () => {
    const { result } = renderHook(useHarness, { wrapper: wrapper("/map?keep=1") });
    expect(result.current.atlas.state).toEqual({
      stateVersion: 1,
      datasetVersion: "0.2.0",
      viewId: "problem-structure",
      viewVersion: "1.0.0",
      answers: {},
    });
    expect(result.current.location.search).toBe("?keep=1");
  });

  test("reports malformed and incompatible tokens and reset preserves unrelated params", () => {
    const { result } = renderHook(useHarness, { wrapper: wrapper("/map?keep=1&state=bad") });
    expect(result.current.atlas.error).toBeInstanceOf(Error);
    act(() => result.current.atlas.reset());
    expect(result.current.atlas.error).toBeUndefined();
    expect(result.current.location.search).toBe("?keep=1");
  });

  test("migrates stale compatible tokens with warnings and replacement", async () => {
    const stale: AtlasStateV1 = {
      stateVersion: 1,
      datasetVersion: "old",
      viewId: "problem-structure",
      viewVersion: "old",
      selectedNodeId: "A",
      answers: {},
    };
    const { result } = renderHook(useHarness, {
      wrapper: wrapper(`/map?state=${encodeAtlasState(stale)}&keep=1`),
    });
    expect(result.current.atlas.warnings).toHaveLength(2);
    await act(async () => undefined);
    expect(new URLSearchParams(result.current.location.search).get("state")).toBe(
      encodeAtlasState(result.current.atlas.state),
    );
    expect(new URLSearchParams(result.current.location.search).get("keep")).toBe("1");
  });

  test("pushes intentional A to B selection and browser back restores A", async () => {
    const { result } = renderHook(useHarness, { wrapper: wrapper("/map?keep=1") });
    act(() =>
      result.current.atlas.setState((state) => ({ ...state, selectedNodeId: "A" })),
    );
    const tokenA = new URLSearchParams(result.current.location.search).get("state");
    act(() =>
      result.current.atlas.setState((state) => ({ ...state, selectedNodeId: "B" })),
    );
    expect(new URLSearchParams(result.current.location.search).get("state")).not.toBe(tokenA);
    act(() => result.current.navigate(-1));
    await act(async () => undefined);
    expect(result.current.atlas.state.selectedNodeId).toBe("A");
  });

  test("reports URL-too-long visibly without truncating or changing location", () => {
    const { result } = renderHook(useHarness, { wrapper: wrapper("/diagnose?keep=1") });
    const before = result.current.location.search;

    act(() =>
      result.current.atlas.setState((state) => ({
        ...state,
        answers: Object.fromEntries(
          Array.from({ length: 80 }, (_, index) => [
            `Q-${index}`,
            { status: "answered" as const, values: [`${"value".repeat(8)}-${index}`] },
          ]),
        ),
      })),
    );

    expect(result.current.atlas.error).toBeInstanceOf(AtlasStateUrlTooLongError);
    expect(result.current.location.search).toBe(before);
  });
});
