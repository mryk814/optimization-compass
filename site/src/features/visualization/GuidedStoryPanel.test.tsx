import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

import fixture from "../../contracts/visualization-scenarios.fixture.json";
import { parseVisualizationScenarioIndex } from "../../contracts/visualization-scenarios";
import type { PlaybackController } from "../playback/usePlayback";
import { GuidedStoryPanel } from "./GuidedStoryPanel";

const scenario = parseVisualizationScenarioIndex(fixture).scenarios[0];

describe("GuidedStoryPanel", () => {
  test("activates an authored cue and applies its playback contract", () => {
    const pause = vi.fn();
    const seekToFrameAtSpeed = vi.fn();
    const onStepChange = vi.fn();
    const playback = {
      currentFrameIndex: 0,
      isPlaying: false,
      pause,
      seekToFrameAtSpeed,
    } as unknown as PlaybackController;

    render(
      <GuidedStoryPanel
        activeStep={null}
        onStepChange={onStepChange}
        playback={playback}
        scenario={scenario}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /最初の受理判断/u }));

    const step = scenario.guided_story?.steps[1];
    expect(step).toBeDefined();
    expect(pause).toHaveBeenCalledOnce();
    expect(seekToFrameAtSpeed).toHaveBeenCalledWith(step?.frame_index, step?.playback_speed);
    expect(onStepChange).toHaveBeenCalledWith(step);
  });
});
