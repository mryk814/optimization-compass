import { describe, expect, test } from "vitest";

import generated from "../../public/data/media/manifest.json";
import { parseDerivedMediaManifest } from "./derived-media";

describe("DerivedMediaManifest", () => {
  test("parses the generated static and thumbnail assets", () => {
    const manifest = parseDerivedMediaManifest(generated);
    const entry = manifest.entries[0];

    expect(entry.scenario_id).toBe("SCENARIO_NM_QUADRATIC");
    expect(entry.files.map((file) => file.media_kind)).toEqual([
      "static_svg",
      "static_png",
      "thumbnail",
    ]);
    expect(entry.files.every((file) => file.sha256.length === 64)).toBe(true);
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
