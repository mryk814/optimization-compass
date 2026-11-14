/**
 * A guided scene is a list of beats: settings to show, for how long, and what to say (ADR 0018).
 * Everything here is a pure function of scene time `t`, so the in-page guided playback, the
 * recorded video and its captions all point at the same frame for the same `t`.
 */
/** A value that moves during a beat: a sweep, or with `rate` a steady climb that stops at `to`. */
export interface MovingSetting {
  from: number;
  to: number;
  /** Units per second. Without it the value sweeps linearly over the beat. */
  rate?: number;
  /** Grid the moving value stays on (1 for an integer param). */
  step?: number;
}

export type SettingValue = number | string | Readonly<MovingSetting>;
export type BeatSettings = Readonly<Record<string, SettingValue>>;
/** Settings at one instant: what a figure draws. */
export type ResolvedSettings = Readonly<Record<string, number | string>>;

/** A sweep reaches its end this long before the beat ends, so the result can be read. */
export const SWEEP_HOLD_S = 1.5;

function movingValue({ from, to, rate, step }: Readonly<MovingSetting>, local: number, durationS: number): number {
  const span = Math.abs(to - from);
  let travelled = rate === undefined
    ? Math.min(1, local / Math.max(durationS - SWEEP_HOLD_S, 1)) * span
    : Math.min(span, rate * local);
  if (step !== undefined) travelled = Math.floor(travelled / step + 1e-9) * step;
  return to >= from ? from + travelled : from - travelled;
}

/**
 * The plain values of a beat's settings `local` seconds into it. Constants pass through; a sweep
 * `{from, to}` is linear over the beat and holds its end for the last `SWEEP_HOLD_S`; a rate
 * `{from, to, rate}` adds `rate` per second and stops at `to`. `content_markdown.py` computes the
 * same end values when it carries a param from one lesson step to the next.
 */
export function resolveSettings(settings: BeatSettings, local: number, durationS: number): ResolvedSettings {
  const time = Math.min(Math.max(local, 0), durationS);
  return Object.fromEntries(
    Object.entries(settings).map(([key, value]) => [
      key,
      typeof value === "object" ? movingValue(value, time, durationS) : value,
    ]),
  );
}

export interface SceneBeat {
  settings: BeatSettings;
  durationS: number;
  captionJa: string;
  narrationJa: string;
}

export interface ScenePoint {
  /** Index of the beat on screen at `t`. */
  index: number;
  /** Seconds since that beat started, in [0, its duration]. */
  local: number;
}

export function sceneDuration(beats: readonly SceneBeat[]): number {
  return beats.reduce((total, beat) => total + beat.durationS, 0);
}

export function beatStart(beats: readonly SceneBeat[], index: number): number {
  return sceneDuration(beats.slice(0, index));
}

/** The beat on screen at scene time `t`. A boundary belongs to the beat that starts there. */
export function sceneAt(beats: readonly SceneBeat[], t: number): ScenePoint {
  if (beats.length === 0) return { index: 0, local: 0 };
  let start = 0;
  for (let index = 0; index < beats.length; index += 1) {
    const end = start + beats[index].durationS;
    if (t < end || index === beats.length - 1) {
      return { index, local: Math.min(Math.max(t - start, 0), beats[index].durationS) };
    }
    start = end;
  }
  return { index: beats.length - 1, local: beats[beats.length - 1].durationS };
}

function timestamp(seconds: number): string {
  const ms = Math.round(seconds * 1000);
  const h = Math.floor(ms / 3_600_000);
  const m = Math.floor((ms % 3_600_000) / 60_000);
  const s = Math.floor((ms % 60_000) / 1000);
  const pad = (value: number, width = 2) => String(value).padStart(width, "0");
  return `${pad(h)}:${pad(m)}:${pad(s)}.${pad(ms % 1000, 3)}`;
}

/** WebVTT captions: one cue per beat, spoken text as the cue (ADR 0018 §5a). */
export function sceneWebVtt(beats: readonly SceneBeat[]): string {
  const cues = beats.map((beat, index) => {
    const start = beatStart(beats, index);
    return `${index + 1}\n${timestamp(start)} --> ${timestamp(start + beat.durationS)}\n${beat.narrationJa}\n`;
  });
  return ["WEBVTT", "", ...cues].join("\n");
}

export function numberSetting(settings: BeatSettings | ResolvedSettings, key: string, fallback: number): number {
  const value = settings[key];
  return typeof value === "number" ? value : fallback;
}

export function stringSetting<T extends string>(
  settings: BeatSettings | ResolvedSettings,
  key: string,
  allowed: readonly T[],
  fallback: T,
): T {
  const value = settings[key];
  return typeof value === "string" && (allowed as readonly string[]).includes(value) ? (value as T) : fallback;
}
