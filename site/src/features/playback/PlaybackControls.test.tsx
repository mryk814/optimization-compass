import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, describe, expect, test, vi } from "vitest";

import { parseAlgorithmTrace } from "../../contracts/trace";
import {
  algorithmTraceFixture,
  traceFrameFixture,
} from "../../contracts/trace.fixtures";
import { PlaybackControls } from "./PlaybackControls";
import { usePlayback } from "./usePlayback";

const parsed = parseAlgorithmTrace({
  ...algorithmTraceFixture,
  frames: [
    traceFrameFixture,
    { ...traceFrameFixture, frame_index: 1, iteration: 1, oracle_evaluations: 2 },
    { ...traceFrameFixture, frame_index: 2, iteration: 2, oracle_evaluations: 5 },
  ],
});

function Harness() {
  const playback = usePlayback(parsed.trace_id, parsed.frames);
  const location = useLocation();
  return (
    <>
      <PlaybackControls playback={playback} />
      <output aria-label="current frame">{playback.currentFrameIndex}</output>
      <output aria-label="playing">{String(playback.isPlaying)}</output>
      <output aria-label="url">{location.search}</output>
    </>
  );
}

function renderHarness(initialEntry = "/traces/dummy?foo=bar") {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Harness />
    </MemoryRouter>,
  );
}

describe("PlaybackControls", () => {
  afterEach(() => {
    cleanup();
    vi.useRealTimers();
  });

  test("steps, seeks, changes speed, reverses, and stays within bounds", () => {
    renderHarness();
    fireEvent.click(screen.getByRole("button", { name: "1フレーム進む" }));
    expect(screen.getByLabelText("current frame")).toHaveTextContent("1");
    fireEvent.change(screen.getByLabelText("フレーム位置"), { target: { value: "2" } });
    expect(screen.getByLabelText("current frame")).toHaveTextContent("2");
    fireEvent.change(screen.getByLabelText("評価回数位置"), { target: { value: "1" } });
    expect(screen.getByLabelText("current frame")).toHaveTextContent("0");
    fireEvent.change(screen.getByLabelText("フレーム位置"), { target: { value: "2" } });
    fireEvent.click(screen.getByRole("button", { name: "1フレーム進む" }));
    expect(screen.getByLabelText("current frame")).toHaveTextContent("2");
    fireEvent.change(screen.getByLabelText("再生速度"), { target: { value: "4" } });
    fireEvent.click(screen.getByRole("button", { name: "逆再生にする" }));
    expect(screen.getByRole("button", { name: "順再生にする" })).toBeVisible();
    expect(screen.getByLabelText("url")).toHaveTextContent("foo=bar");
    expect(screen.getByLabelText("url")).toHaveTextContent("speed=4");
    expect(screen.getByLabelText("url")).toHaveTextContent("direction=reverse");
  });

  test("reload state decodes position/speed/direction but always starts paused", () => {
    renderHarness(
      "/traces/dummy?trace=dummy-educational&evaluation=4&speed=2&direction=reverse&foo=bar",
    );
    expect(screen.getByLabelText("current frame")).toHaveTextContent("1");
    expect(screen.getByLabelText("playing")).toHaveTextContent("false");
    expect(screen.getByRole("combobox", { name: "再生速度" })).toHaveValue("2");
    expect(screen.getByRole("button", { name: "順再生にする" })).toBeVisible();
  });

  test("play advances at the selected speed and pauses safely at the terminal frame", () => {
    vi.useFakeTimers();
    renderHarness("/traces/dummy?speed=4");
    fireEvent.click(screen.getByRole("button", { name: "再生" }));
    act(() => vi.advanceTimersByTime(600));
    expect(screen.getByLabelText("current frame")).toHaveTextContent("2");
    expect(screen.getByLabelText("playing")).toHaveTextContent("false");
  });

  test("reverse playback reaches the first frame and pauses", () => {
    vi.useFakeTimers();
    renderHarness("/traces/dummy?frame=2&speed=4&direction=reverse");
    fireEvent.click(screen.getByRole("button", { name: "再生" }));
    act(() => vi.advanceTimersByTime(600));
    expect(screen.getByLabelText("current frame")).toHaveTextContent("0");
    expect(screen.getByLabelText("playing")).toHaveTextContent("false");
  });
});
