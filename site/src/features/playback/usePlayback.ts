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
  reducedMotion: boolean;
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
  const search = searchParams.toString();
  const position = useMemo(
    () => decodePosition(searchParams, traceId, frames),
    // URL search is a stable serialization of the current navigation entry.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [search, traceId, frames],
  );
  const [isPlaying, setIsPlaying] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(() =>
    typeof window.matchMedia === "function"
      && window.matchMedia("(prefers-reduced-motion: reduce)").matches,
  );
  const frameIndexRef = useRef(position.frameIndex);
  frameIndexRef.current = position.frameIndex;
  const internalSearchRef = useRef<string | null>(null);

  const writePosition = useCallback(
    (nextPosition: DecodedPosition) => {
      const next = new URLSearchParams(searchParams);
      next.set("trace", traceId);
      next.set("frame", String(nextPosition.frameIndex));
      next.delete("evaluation");
      if (nextPosition.speed === 1) next.delete("speed");
      else next.set("speed", String(nextPosition.speed));
      if (nextPosition.direction === "forward") next.delete("direction");
      else next.set("direction", nextPosition.direction);
      const nextSearch = next.toString();
      if (nextSearch !== search) {
        internalSearchRef.current = nextSearch;
        setSearchParams(next, { replace: true });
      }
    },
    [search, searchParams, setSearchParams, traceId],
  );

  const seekToFrame = useCallback(
    (requestedIndex: number) => {
      const nextIndex = clamp(Math.trunc(requestedIndex), 0, frames.length - 1);
      frameIndexRef.current = nextIndex;
      writePosition({ ...position, frameIndex: nextIndex });
    },
    [frames.length, position, writePosition],
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
    writePosition({ ...position, speed: nextSpeed });
  }, [position, writePosition]);

  useEffect(() => {
    if (internalSearchRef.current === search) {
      internalSearchRef.current = null;
    } else {
      setIsPlaying(false);
    }
  }, [search]);

  useEffect(() => {
    if (typeof window.matchMedia !== "function") return undefined;
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReducedMotion(query.matches);
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    if (reducedMotion) setIsPlaying(false);
  }, [reducedMotion]);

  useEffect(() => {
    if (!isPlaying) return undefined;
    const delta = position.direction === "forward" ? 1 : -1;
    const timer = window.setInterval(() => {
      const nextIndex = frameIndexRef.current + delta;
      if (nextIndex < 0 || nextIndex >= frames.length) {
        setIsPlaying(false);
        return;
      }
      frameIndexRef.current = nextIndex;
      writePosition({ ...position, frameIndex: nextIndex });
      if (nextIndex === 0 || nextIndex === frames.length - 1) setIsPlaying(false);
    }, BASE_FRAME_INTERVAL_MS / position.speed);
    return () => window.clearInterval(timer);
  }, [frames.length, isPlaying, position, writePosition]);

  return {
    traceId,
    frames,
    currentFrameIndex: position.frameIndex,
    currentFrame: frames[position.frameIndex],
    isPlaying,
    speed: position.speed,
    direction: position.direction,
    reducedMotion,
    play: () => {
      if (!reducedMotion) setIsPlaying(true);
    },
    pause: () => setIsPlaying(false),
    togglePlayback: () => {
      if (!reducedMotion) setIsPlaying((playing) => !playing);
    },
    stepBackward,
    stepForward,
    seekToFrame,
    seekToEvaluation,
    reverse: () => writePosition({
      ...position,
      direction: position.direction === "forward" ? "reverse" : "forward",
    }),
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
