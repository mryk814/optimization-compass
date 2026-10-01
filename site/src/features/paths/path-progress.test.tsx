import { act, renderHook } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";

import { usePathProgress } from "./path-progress";

afterEach(() => vi.restoreAllMocks());

test("progress stays usable and synchronized when browser storage is denied", () => {
  vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
    throw new DOMException("Blocked", "SecurityError");
  });
  vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
    throw new DOMException("Blocked", "SecurityError");
  });
  const first = renderHook(() => usePathProgress());
  const second = renderHook(() => usePathProgress());

  act(() => first.result.current.setDone("storage-denied-path", "formulation:PA017", true));
  expect(first.result.current.isDone("storage-denied-path", "formulation:PA017")).toBe(true);
  expect(second.result.current.doneCount("storage-denied-path")).toBe(1);

  act(() => second.result.current.setDone("storage-denied-path", "formulation:PA017", false));
  expect(first.result.current.doneCount("storage-denied-path")).toBe(0);
});
