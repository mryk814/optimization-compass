import { createContext, useCallback, useContext, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

import { LessonContext } from "./lessonContext";
import {
  beatStart,
  resolveSettings,
  sceneAt,
  sceneDuration,
  sceneWebVtt,
  type BeatSettings,
  type ResolvedSettings,
  type SceneBeat,
} from "./scene";
import { usePrefersReducedMotion } from "./useTimeline";

/**
 * Set by the record page. A recorded scene is always on, has no wall clock, and is driven
 * frame by frame through `window.__ocScene.seek(t)` (see `site/scripts/record-scene.mjs`).
 */
export const SceneRecordingContext = createContext(false);

const NO_VALUES: ResolvedSettings = Object.freeze({});
const noop = () => {};

export interface SceneRecorderHandle {
  id: string;
  durationS: number;
  beats: readonly SceneBeat[];
  webVtt: string;
  /** Shows scene time `t` and resolves once that frame has been painted. */
  seek(t: number): Promise<void>;
}

declare global {
  interface Window {
    __ocScene?: SceneRecorderHandle;
  }
}

export interface SceneTour {
  beats: readonly SceneBeat[];
  /** True while the guided scene drives the figure instead of the reader's controls. */
  active: boolean;
  playing: boolean;
  recording: boolean;
  reducedMotion: boolean;
  t: number;
  durationS: number;
  index: number;
  /** Seconds since the current beat started. */
  local: number;
  beat: SceneBeat | undefined;
  /**
   * The current beat's settings at this instant, with sweeps and rates resolved to plain values.
   * Empty while the scene is off. A figure that draws from `values` works in a lesson unchanged.
   */
  values: ResolvedSettings;
  /** True when an article's lesson drives this figure; the frame then leaves the chrome to it. */
  lesson: boolean;
  start(): void;
  stop(): void;
  toggle(): void;
  goTo(index: number): void;
}

/**
 * The guided-scene clock. It owns only time; the figure maps the current beat's settings and
 * `local` onto its own state. Leaving the scene hands the last beat's settings to `onExit`, so
 * the reader continues from what they were just shown.
 *
 * Inside an article's lesson (`LessonContext`) the lesson owns the clock instead: its steps are the
 * beats, the active step is `index`, and `local` restarts when a step is entered. `beats` passed
 * here are then ignored, and `onExit` receives the values on screen when the reader takes over.
 */
export function useSceneTour(
  id: string,
  beats: readonly SceneBeat[],
  onExit: (settings: BeatSettings) => void,
): SceneTour {
  const recording = useContext(SceneRecordingContext);
  const lesson = useContext(LessonContext);
  const reducedMotion = usePrefersReducedMotion();
  const durationS = sceneDuration(beats);
  const [active, setActive] = useState(recording);
  const [playing, setPlaying] = useState(false);
  const [t, setT] = useState(0);
  const tRef = useRef(0);
  tRef.current = t;
  const paintedRef = useRef<Array<() => void>>([]);

  useEffect(() => {
    if (!playing || recording) return undefined;
    let frame = 0;
    let last: number | undefined;
    const tick = (now: number) => {
      const elapsed = last === undefined ? 0 : Math.max(0, (now - last) / 1000);
      last = now;
      const next = Math.min(durationS, tRef.current + elapsed);
      tRef.current = next;
      setT(next);
      if (next >= durationS) {
        setPlaying(false);
        return;
      }
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [durationS, playing, recording]);

  useEffect(() => {
    if (reducedMotion) setPlaying(false);
  }, [reducedMotion]);

  // Resolve pending recorder seeks after React commits the frame and the browser paints it.
  useEffect(() => {
    if (paintedRef.current.length === 0) return;
    const waiting = paintedRef.current;
    paintedRef.current = [];
    requestAnimationFrame(() => requestAnimationFrame(() => waiting.forEach((resolve) => resolve())));
  }, [t]);

  useEffect(() => {
    if (!recording) return undefined;
    window.__ocScene = {
      id,
      durationS,
      beats,
      webVtt: sceneWebVtt(beats),
      seek: (next) => new Promise<void>((resolve) => {
        const clamped = Math.min(Math.max(next, 0), durationS);
        if (clamped === tRef.current) {
          requestAnimationFrame(() => requestAnimationFrame(() => resolve()));
          return;
        }
        paintedRef.current.push(resolve);
        tRef.current = clamped;
        setT(clamped);
      }),
    };
    return () => {
      delete window.__ocScene;
    };
  }, [beats, durationS, id, recording]);

  const { index, local } = sceneAt(beats, t);
  const beat = active ? beats[index] : undefined;

  const lessonBeat = lesson?.beats[lesson.index];
  const lessonLocal = lesson?.local ?? 0;
  const lessonValues = useMemo(
    () => (lessonBeat ? resolveSettings(lessonBeat.settings, lessonLocal, lessonBeat.durationS) : NO_VALUES),
    [lessonBeat, lessonLocal],
  );
  const lessonFree = lesson?.free ?? false;
  const wasFree = useRef(lessonFree);
  const lessonValuesRef = useRef(lessonValues);
  lessonValuesRef.current = lessonValues;
  useLayoutEffect(() => {
    if (lessonFree && !wasFree.current) onExit(lessonValuesRef.current);
    wasFree.current = lessonFree;
  }, [lessonFree, onExit]);

  // With reduced motion each beat is shown in its finished state and advanced by hand.
  const showBeat = useCallback((target: number) => {
    const next = reducedMotion
      ? beatStart(beats, target) + beats[target].durationS - 1e-6
      : beatStart(beats, target);
    tRef.current = next;
    setT(next);
  }, [beats, reducedMotion]);

  const start = useCallback(() => {
    if (beats.length === 0) return;
    setActive(true);
    showBeat(0);
    setPlaying(!reducedMotion);
  }, [beats.length, reducedMotion, showBeat]);

  const stop = useCallback(() => {
    if (recording) return;
    const current = beats[sceneAt(beats, tRef.current).index];
    setActive(false);
    setPlaying(false);
    if (current) onExit(current.settings);
  }, [beats, onExit, recording]);

  const toggle = useCallback(() => {
    if (reducedMotion) return;
    if (tRef.current >= durationS) {
      showBeat(0);
      setPlaying(true);
      return;
    }
    setPlaying((value) => !value);
  }, [durationS, reducedMotion, showBeat]);

  const goTo = useCallback((target: number) => {
    if (target < 0 || target >= beats.length) return;
    showBeat(target);
    setPlaying(!reducedMotion);
  }, [beats.length, reducedMotion, showBeat]);

  if (lesson) {
    return {
      beats: lesson.beats,
      active: !lesson.free,
      playing: false,
      recording: false,
      reducedMotion,
      t: beatStart(lesson.beats, lesson.index) + lesson.local,
      durationS: sceneDuration(lesson.beats),
      index: lesson.index,
      local: lesson.local,
      beat: lesson.free ? undefined : lessonBeat,
      values: lesson.free ? NO_VALUES : lessonValues,
      lesson: true,
      start: noop,
      stop: noop,
      toggle: noop,
      goTo: noop,
    };
  }

  return {
    beats,
    active,
    playing,
    recording,
    reducedMotion,
    t,
    durationS,
    index,
    local,
    beat,
    values: beat ? resolveSettings(beat.settings, local, beat.durationS) : NO_VALUES,
    lesson: false,
    start,
    stop,
    toggle,
    goTo,
  };
}
