import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";

import type {
  PlaybackDirection,
  PlaybackSpeed,
  TraceFrame,
} from "../../contracts/trace";

export const PLAYBACK_SPEEDS = [0.25, 0.5, 1, 2, 4] as const;
const BASE_FRAME_INTERVAL_MS = 800;

export interface PlaybackController {
  traceId: string;
  frames: readonly TraceFrame[];
  currentFrameIndex: number;
  currentFrame: TraceFrame;
  isPlaying: boolean;
  speed: PlaybackSpeed;
  direction: PlaybackDirection;
  play(): void;
  pause(): void;
  togglePlayback(): void;
  stepBackward(): void;
  stepForward(): void;
  seekToFrame(frameIndex: number): void;
  seekToEvaluation(oracleEvaluations: number): void;
  reverse(): void;
  setSpeed(speed: PlaybackSpeed): void;
}

type DecodedPosition = {
  frameIndex: number;
  speed: PlaybackSpeed;
  direction: PlaybackDirection;
};

export function usePlayback(
  traceId: string,
  frames: readonly TraceFrame[],
): PlaybackController {
  if (frames.length === 0) throw new Error("Playback requires at least one frame.");
  const [searchParams, setSearchParams] = useSearchParams();
  const initial = useMemo(
    () => decodePosition(searchParams, traceId, frames),
    // Initial URL state is intentionally decoded once. Playback owns subsequent state.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [traceId, frames],
  );
  const [currentFrameIndex, setCurrentFrameIndex] = useState(initial.frameIndex);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeedState] = useState<PlaybackSpeed>(initial.speed);
  const [direction, setDirection] = useState<PlaybackDirection>(initial.direction);
  const frameIndexRef = useRef(currentFrameIndex);
  frameIndexRef.current = currentFrameIndex;

  const seekToFrame = useCallback(
    (requestedIndex: number) => {
      const nextIndex = clamp(Math.trunc(requestedIndex), 0, frames.length - 1);
      frameIndexRef.current = nextIndex;
      setCurrentFrameIndex(nextIndex);
    },
    [frames.length],
  );
  const stepBackward = useCallback(() => seekToFrame(frameIndexRef.current - 1), [seekToFrame]);
  const stepForward = useCallback(() => seekToFrame(frameIndexRef.current + 1), [seekToFrame]);
  const seekToEvaluation = useCallback(
    (oracleEvaluations: number) => {
      seekToFrame(frameIndexAtEvaluation(frames, Math.max(0, oracleEvaluations)));
    },
    [frames, seekToFrame],
  );
  const setSpeed = useCallback((nextSpeed: PlaybackSpeed) => {
    if (!PLAYBACK_SPEEDS.includes(nextSpeed)) throw new Error(`Unsupported playback speed: ${nextSpeed}.`);
    setSpeedState(nextSpeed);
  }, []);

  useEffect(() => {
    const next = new URLSearchParams(searchParams);
    next.set("trace", traceId);
    next.set("frame", String(currentFrameIndex));
    next.delete("evaluation");
    if (speed === 1) next.delete("speed");
    else next.set("speed", String(speed));
    if (direction === "forward") next.delete("direction");
    else next.set("direction", direction);
    if (next.toString() !== searchParams.toString()) {
      setSearchParams(next, { replace: true });
    }
  }, [currentFrameIndex, direction, searchParams, setSearchParams, speed, traceId]);

  useEffect(() => {
    if (!isPlaying) return undefined;
    const delta = direction === "forward" ? 1 : -1;
    const timer = window.setInterval(() => {
      const nextIndex = frameIndexRef.current + delta;
      if (nextIndex < 0 || nextIndex >= frames.length) {
        setIsPlaying(false);
        return;
      }
      frameIndexRef.current = nextIndex;
      setCurrentFrameIndex(nextIndex);
      if (nextIndex === 0 || nextIndex === frames.length - 1) setIsPlaying(false);
    }, BASE_FRAME_INTERVAL_MS / speed);
    return () => window.clearInterval(timer);
  }, [direction, frames.length, isPlaying, speed]);

  return {
    traceId,
    frames,
    currentFrameIndex,
    currentFrame: frames[currentFrameIndex],
    isPlaying,
    speed,
    direction,
    play: () => setIsPlaying(true),
    pause: () => setIsPlaying(false),
    togglePlayback: () => setIsPlaying((playing) => !playing),
    stepBackward,
    stepForward,
    seekToFrame,
    seekToEvaluation,
    reverse: () => setDirection((current) => (current === "forward" ? "reverse" : "forward")),
    setSpeed,
  };
}

function decodePosition(
  params: URLSearchParams,
  traceId: string,
  frames: readonly TraceFrame[],
): DecodedPosition {
  const requestedTrace = params.get("trace");
  const traceMatches = requestedTrace === null || requestedTrace === traceId;
  const requestedFrame = traceMatches ? parseNonNegativeInteger(params.get("frame")) : undefined;
  const requestedEvaluation = traceMatches
    ? parseNonNegativeInteger(params.get("evaluation"))
    : undefined;
  const frameIndex = requestedFrame === undefined
    ? requestedEvaluation === undefined
      ? 0
      : frameIndexAtEvaluation(frames, requestedEvaluation)
    : clamp(requestedFrame, 0, frames.length - 1);
  const requestedSpeed = Number(params.get("speed"));
  const speed = PLAYBACK_SPEEDS.includes(requestedSpeed as PlaybackSpeed)
    ? requestedSpeed as PlaybackSpeed
    : 1;
  return {
    frameIndex,
    speed,
    direction: params.get("direction") === "reverse" ? "reverse" : "forward",
  };
}

function frameIndexAtEvaluation(frames: readonly TraceFrame[], requested: number): number {
  let match = 0;
  for (let index = 0; index < frames.length; index += 1) {
    if (frames[index].oracle_evaluations > requested) break;
    match = index;
  }
  return match;
}

function parseNonNegativeInteger(value: string | null): number | undefined {
  if (value === null || !/^\d+$/u.test(value)) return undefined;
  const parsed = Number(value);
  return Number.isSafeInteger(parsed) ? parsed : undefined;
}

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.min(maximum, Math.max(minimum, value));
}
