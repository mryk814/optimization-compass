import { describe, expect, it } from "vitest";

import { beatStart, resolveSettings, sceneAt, sceneDuration, sceneWebVtt, type SceneBeat } from "./scene";

const beat = (durationS: number, narrationJa = "話す。"): SceneBeat => ({
  settings: {},
  durationS,
  captionJa: "見る。",
  narrationJa,
});

describe("scene time", () => {
  const beats = [beat(2), beat(3.5), beat(4)];

  it("adds beat durations and start times", () => {
    expect(sceneDuration(beats)).toBe(9.5);
    expect(beatStart(beats, 0)).toBe(0);
    expect(beatStart(beats, 2)).toBe(5.5);
  });

  it("gives a boundary to the beat that starts there and clamps both ends", () => {
    expect(sceneAt(beats, 0)).toEqual({ index: 0, local: 0 });
    expect(sceneAt(beats, 1.999)).toEqual({ index: 0, local: 1.999 });
    expect(sceneAt(beats, 2)).toEqual({ index: 1, local: 0 });
    expect(sceneAt(beats, 9.5)).toEqual({ index: 2, local: 4 });
    expect(sceneAt(beats, 20)).toEqual({ index: 2, local: 4 });
    expect(sceneAt(beats, -1)).toEqual({ index: 0, local: 0 });
  });

  it("writes one WebVTT cue per beat from the spoken text", () => {
    expect(sceneWebVtt([beat(2, "一つ目。"), beat(61.25, "二つ目。")])).toBe(
      "WEBVTT\n\n1\n00:00:00.000 --> 00:00:02.000\n一つ目。\n\n"
      + "2\n00:00:02.000 --> 00:01:03.250\n二つ目。\n",
    );
  });
});

describe("resolveSettings", () => {
  it("passes constants through", () => {
    expect(resolveSettings({ eta: 0.1, mode: "random" }, 3, 6)).toEqual({ eta: 0.1, mode: "random" });
  });

  it("sweeps linearly over the beat and holds the end for the last 1.5 s", () => {
    const at = (local: number) => resolveSettings({ k: { from: 0, to: 12 } }, local, 6).k;
    expect(at(0)).toBe(0);
    expect(at(1.5)).toBeCloseTo(4);
    expect(at(4.5)).toBe(12);
    expect(at(6)).toBe(12);
    // A short beat still takes a second to sweep.
    expect(resolveSettings({ k: { from: 0, to: 12 } }, 0.5, 2).k).toBeCloseTo(6);
  });

  it("sweeps downward as well", () => {
    expect(resolveSettings({ k: { from: 10, to: 4 } }, 2.25, 6).k).toBeCloseTo(7);
  });

  it("moves at a rate per second and stops at the far end", () => {
    const at = (local: number) => resolveSettings({ k: { from: 0, to: 30, rate: 4 } }, local, 15).k;
    expect(at(2.5)).toBeCloseTo(10);
    expect(at(7.5)).toBe(30);
    expect(at(15)).toBe(30);
    expect(resolveSettings({ k: { from: 30, to: 0, rate: 5 } }, 4, 4).k).toBeCloseTo(10);
  });

  it("keeps a stepped value on its grid, counting from the start", () => {
    const at = (local: number) => resolveSettings({ k: { from: 1, to: 40, rate: 2.5, step: 1 } }, local, 6).k;
    expect(at(0.39)).toBe(1);
    expect(at(0.4)).toBe(2);
    expect(at(6)).toBe(16); // the value content_markdown.py carries into the next lesson step
    expect(resolveSettings({ k: { from: 9, to: 1, step: 1 } }, 1.2, 6).k).toBe(7);
  });

  it("clamps time to the beat", () => {
    expect(resolveSettings({ k: { from: 2, to: 8 } }, -1, 6).k).toBe(2);
    expect(resolveSettings({ k: { from: 0, to: 30, rate: 1 } }, 99, 6).k).toBe(6);
  });
});
