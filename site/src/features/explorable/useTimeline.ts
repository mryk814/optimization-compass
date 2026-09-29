import { useCallback, useEffect, useRef, useState } from "react";

export const TIMELINE_SPEEDS = [0.5, 1, 2, 4] as const;
export type TimelineSpeed = (typeof TIMELINE_SPEEDS)[number];

export interface Timeline {
  /** Fractional position in [0, length]. The figure interpolates between whole steps. */
  position: number;
  /** Whole steps already taken. */
  step: number;
  length: number;
  playing: boolean;
  speed: TimelineSpeed;
  /** True when the reader asked the OS to reduce motion; playback is then step-by-step only. */
  reducedMotion: boolean;
  atStart: boolean;
  atEnd: boolean;
  play(): void;
  pause(): void;
  toggle(): void;
  /** Jump to a position and stop. */
  seek(position: number): void;
  /** Go back to the start and, unless motion is reduced, play. */
  restart(): void;
  /** Show the finished state immediately. */
  finish(): void;
  stepForward(): void;
  stepBackward(): void;
  setSpeed(speed: TimelineSpeed): void;
}

export function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(
    () => typeof window.matchMedia === "function"
      && window.matchMedia("(prefers-reduced-motion: reduce)").matches,
  );
  useEffect(() => {
    if (typeof window.matchMedia !== "function") return undefined;
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduced(query.matches);
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);
  return reduced;
}

/**
 * Replays the timeline whenever `key` changes (a slider moved, a point was dragged).
 * The first render shows the finished state so a figure below the fold is not already over
 * by the time it is scrolled into view; reduced motion always shows the finished state.
 */
export function useReplayOnChange(timeline: Timeline, key: string): void {
  const previous = useRef<string | undefined>(undefined);
  useEffect(() => {
    if (previous.current === key) return;
    const first = previous.current === undefined;
    previous.current = key;
    if (first || timeline.reducedMotion) timeline.finish();
    else timeline.restart();
  }, [key]);
}

/**
 * A requestAnimationFrame clock over `length` steps. The figure owns what a step means;
 * the clock only owns time, so every explorable shares the same play / scrub / reduced-motion behaviour.
 */
export function useTimeline(length: number, stepsPerSecond = 5): Timeline {
  const reducedMotion = usePrefersReducedMotion();
  const [position, setPosition] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState<TimelineSpeed>(1);
  const positionRef = useRef(0);
  positionRef.current = position;

  const seek = useCallback((next: number) => {
    const clamped = Math.min(Math.max(next, 0), length);
    positionRef.current = clamped;
    setPosition(clamped);
    setPlaying(false);
  }, [length]);

  useEffect(() => {
    if (positionRef.current > length) {
      positionRef.current = length;
      setPosition(length);
    }
  }, [length]);

  useEffect(() => {
    if (!playing) return undefined;
    let frame = 0;
    let last: number | undefined;
    const tick = (now: number) => {
      // The first frame only sets the clock: rAF timestamps are frame-start times and can
      // precede performance.now(), which would otherwise make the first delta negative.
      const elapsed = last === undefined ? 0 : Math.max(0, (now - last) / 1000);
      last = now;
      const next = Math.min(length, positionRef.current + elapsed * stepsPerSecond * speed);
      positionRef.current = next;
      setPosition(next);
      if (next >= length) {
        setPlaying(false);
        return;
      }
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [length, playing, speed, stepsPerSecond]);

  useEffect(() => {
    if (reducedMotion) setPlaying(false);
  }, [reducedMotion]);

  const play = useCallback(() => {
    if (reducedMotion) return;
    if (positionRef.current >= length) {
      positionRef.current = 0;
      setPosition(0);
    }
    setPlaying(true);
  }, [length, reducedMotion]);
  const pause = useCallback(() => setPlaying(false), []);
  const toggle = useCallback(() => (playing ? pause() : play()), [pause, play, playing]);
  const restart = useCallback(() => {
    positionRef.current = 0;
    setPosition(0);
    setPlaying(!reducedMotion);
  }, [reducedMotion]);
  const finish = useCallback(() => seek(length), [length, seek]);
  const stepForward = useCallback(
    () => seek(Math.floor(positionRef.current + 1e-9) + 1),
    [seek],
  );
  const stepBackward = useCallback(
    () => seek(Math.ceil(positionRef.current - 1e-9) - 1),
    [seek],
  );

  return {
    position,
    step: Math.max(0, Math.min(length, Math.floor(position + 1e-9))),
    length,
    playing,
    speed,
    reducedMotion,
    atStart: position <= 0,
    atEnd: position >= length,
    play,
    pause,
    toggle,
    seek,
    restart,
    finish,
    stepForward,
    stepBackward,
    setSpeed,
  };
}
