import { describe, expect, test } from "vitest";

import generated from "../../public/data/media/manifest.json";
import { parseDerivedMediaManifest } from "./derived-media";

describe("DerivedMediaManifest", () => {
  test("parses the generated static, animated, caption, and transcript assets", () => {
    const manifest = parseDerivedMediaManifest(generated);
    const entry = manifest.entries[0];

    expect(entry.scenario_id).toBe("SCENARIO_NM_QUADRATIC");
    expect(entry.files.map((file) => file.media_kind)).toEqual([
      "static_svg",
      "static_png",
      "thumbnail",
      "animated_gif",
      "webm",
    ]);
    expect(entry.files.every((file) => file.sha256.length === 64)).toBe(true);
    expect(entry.captions.path).toMatch(/captions\.vtt$/u);
    expect(entry.transcript.path).toMatch(/transcript\.txt$/u);
    expect(entry.animation_frame_indices.length).toBeGreaterThan(2);
  });

  test("rejects unknown fields and unsafe paths", () => {
    expect(() => parseDerivedMediaManifest({ ...generated, legacy: true })).toThrow(/unknown/u);
    const copy = structuredClone(generated) as unknown as {
      entries: { files: { path: string }[] }[];
    };
    copy.entries[0].files[0].path = "../static.svg";
    expect(() => parseDerivedMediaManifest(copy)).toThrow(/unsafe/u);
  });
});
