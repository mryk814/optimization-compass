import { act, cleanup, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useReplayOnChange, useTimeline } from "./useTimeline";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function stubFrames() {
  const frames: FrameRequestCallback[] = [];
  vi.stubGlobal("requestAnimationFrame", (callback: FrameRequestCallback) => {
    frames.push(callback);
    return frames.length;
  });
  vi.stubGlobal("cancelAnimationFrame", () => undefined);
  return frames;
}

describe("useTimeline", () => {
  it("advances by elapsed time at the requested steps per second", () => {
    const frames = stubFrames();
    const { result } = renderHook(() => useTimeline(10, 5));

    act(() => result.current.play());
    act(() => frames.shift()!(1_000));
    act(() => frames.shift()!(2_000));

    expect(result.current.position).toBeCloseTo(5);
    expect(result.current.step).toBe(5);
  });

  it("stays at or after the start when the first frame timestamp precedes performance.now()", () => {
    const frames = stubFrames();
    const { result } = renderHook(() => useTimeline(10, 5));

    act(() => result.current.play());
    act(() => frames.shift()!(performance.now() - 5_000));
    act(() => frames.shift()!(performance.now() - 6_000));

    expect(result.current.position).toBeGreaterThanOrEqual(0);
    expect(result.current.step).toBeGreaterThanOrEqual(0);
  });

  it("stops at the end and replays from the start when played again", () => {
    const frames = stubFrames();
    const { result } = renderHook(() => useTimeline(2, 10));

    act(() => result.current.play());
    act(() => frames.shift()!(0));
    act(() => frames.shift()!(10_000));

    expect(result.current.atEnd).toBe(true);
    expect(result.current.playing).toBe(false);
    act(() => result.current.play());
    expect(result.current.position).toBe(0);
    expect(result.current.playing).toBe(true);
  });

  it("steps and seeks within bounds", () => {
    const { result } = renderHook(() => useTimeline(3));

    act(() => result.current.stepBackward());
    expect(result.current.position).toBe(0);
    act(() => result.current.stepForward());
    act(() => result.current.stepForward());
    expect(result.current.step).toBe(2);
    act(() => result.current.seek(99));
    expect(result.current.position).toBe(3);
    act(() => result.current.stepBackward());
    expect(result.current.position).toBe(2);
  });
});

describe("useReplayOnChange", () => {
  it("shows the finished state first, then replays when the key changes", () => {
    stubFrames();
    const { result, rerender } = renderHook(
      ({ key }) => {
        const timeline = useTimeline(8);
        useReplayOnChange(timeline, key);
        return timeline;
      },
      { initialProps: { key: "a" } },
    );

    expect(result.current.position).toBe(8);
    expect(result.current.playing).toBe(false);

    rerender({ key: "b" });

    expect(result.current.position).toBe(0);
    expect(result.current.playing).toBe(true);
  });
});
