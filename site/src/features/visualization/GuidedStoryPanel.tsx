import { useEffect, useRef } from "react";

import type {
  GuidedPlaybackSpeed,
  GuidedStoryStep,
  VisualizationScenario,
} from "../../contracts/visualization-scenarios";

export interface GuidedPlaybackController {
  currentFrameIndex: number;
  isPlaying: boolean;
  pause(): void;
  seekToFrameAtSpeed(frameIndex: number, speed: GuidedPlaybackSpeed): void;
}

interface GuidedStoryPanelProps {
  scenario: VisualizationScenario;
  playback: GuidedPlaybackController;
  activeStep: GuidedStoryStep | null;
  onStepChange(step: GuidedStoryStep): void;
}

export function GuidedStoryPanel({
  scenario,
  playback,
  activeStep,
  onStepChange,
}: GuidedStoryPanelProps) {
  const story = scenario.guided_story;
  const previousFrame = useRef(playback.currentFrameIndex);

  useEffect(() => {
    const frameChanged = previousFrame.current !== playback.currentFrameIndex;
    previousFrame.current = playback.currentFrameIndex;
    if (!story || !frameChanged || !playback.isPlaying) return;
    const cue = story.steps.find((step) => step.frame_index === playback.currentFrameIndex);
    if (cue?.auto_pause) {
      playback.pause();
      onStepChange(cue);
    }
  }, [onStepChange, playback, story]);

  if (!story) return null;

  const activate = (step: GuidedStoryStep) => {
    playback.pause();
    playback.seekToFrameAtSpeed(step.frame_index, step.playback_speed);
    onStepChange(step);
  };
  const activeIndex = activeStep
    ? story.steps.findIndex((step) => step.milestone_id === activeStep.milestone_id)
    : -1;
  const nextStep = activeIndex === story.steps.length - 1
    ? story.steps[0]
    : story.steps[Math.max(0, activeIndex + 1)];

  return (
    <section className="guided-story-panel" aria-labelledby={`guided-${scenario.scenario_id}`}>
      <header>
        <div>
          <p className="eyebrow">Guided story · 順に見る</p>
          <h2 id={`guided-${scenario.scenario_id}`}>順に見る</h2>
          <p>{story.introduction.ja}</p>
        </div>
        <button onClick={() => activate(activeIndex < 0 ? story.steps[0] : nextStep)} type="button">
          {activeIndex < 0 ? "案内を始める" : activeIndex === story.steps.length - 1 ? "最初から" : "次のポイント"}
        </button>
      </header>
      <ol className="guided-story-steps">
        {story.steps.map((step, index) => {
          const selected = activeStep?.milestone_id === step.milestone_id;
          return (
            <li key={step.milestone_id}>
              <button
                aria-current={selected ? "step" : undefined}
                onClick={() => activate(step)}
                type="button"
              >
                <span>{index + 1}</span>
                <strong>{scenario.lesson.narration_steps.find((item) => item.milestone_id === step.milestone_id)?.title_ja}</strong>
                <small>フレーム {step.frame_index + 1} · {step.playback_speed}倍{step.auto_pause ? " · 自動停止" : ""}</small>
              </button>
            </li>
          );
        })}
      </ol>
      {activeStep && (
        <div className="guided-story-callout" role="status" aria-live="polite">
          <strong>{activeStep.annotation.ja}</strong>
          <span>
            注目: {activeStep.focus_target} · 表示: {activeStep.viewport_preset}
            {activeStep.camera_preset ? ` · カメラ: ${activeStep.camera_preset}` : ""}
          </span>
        </div>
      )}
      {activeIndex === story.steps.length - 1 && <p className="guided-story-summary">{story.summary.ja}</p>}
    </section>
  );
}
