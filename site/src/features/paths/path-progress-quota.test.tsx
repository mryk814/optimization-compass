import { act, renderHook } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";

import { usePathProgress } from "./path-progress";

afterEach(() => vi.restoreAllMocks());

test("progress retains saved steps and new steps when storage fills up", () => {
  vi.spyOn(Storage.prototype, "getItem").mockReturnValue('{"quota-path":["saved"]}');
  vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
    throw new DOMException("Full", "QuotaExceededError");
  });
  const first = renderHook(() => usePathProgress());
  const second = renderHook(() => usePathProgress());

  act(() => first.result.current.setDone("quota-path", "new", true));
  expect(first.result.current.isDone("quota-path", "saved")).toBe(true);
  expect(second.result.current.doneCount("quota-path")).toBe(2);
  act(() => second.result.current.setDone("quota-path", "new", false));
  expect(first.result.current.doneCount("quota-path")).toBe(1);
});
