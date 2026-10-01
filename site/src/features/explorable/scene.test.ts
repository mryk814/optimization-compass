import { describe, expect, it } from "vitest";

import { beatStart, sceneAt, sceneDuration, sceneWebVtt, type SceneBeat } from "./scene";

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
