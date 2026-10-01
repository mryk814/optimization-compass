/**
 * A guided scene is a list of beats: settings to show, for how long, and what to say (ADR 0018).
 * Everything here is a pure function of scene time `t`, so the in-page guided playback, the
 * recorded video and its captions all point at the same frame for the same `t`.
 */
export type BeatSettings = Readonly<Record<string, number | string>>;

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

export function numberSetting(settings: BeatSettings, key: string, fallback: number): number {
  const value = settings[key];
  return typeof value === "number" ? value : fallback;
}

export function stringSetting<T extends string>(
  settings: BeatSettings,
  key: string,
  allowed: readonly T[],
  fallback: T,
): T {
  const value = settings[key];
  return typeof value === "string" && (allowed as readonly string[]).includes(value) ? (value as T) : fallback;
}
