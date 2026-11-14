import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

import { EXPLORABLE_META, type MetaFile } from "./figureMeta";
import { EXPLORABLE_COMPONENTS } from "./registry";

// Adding a figure means adding one folder. These checks hold the folder contract that
// replaces the old hand-kept lists (registry entries, the meta.ts copy of explorables.json).
const FIGURES = join(__dirname, "figures");
const folders = readdirSync(FIGURES, { withFileTypes: true })
  .filter((entry) => entry.isDirectory())
  .map((entry) => entry.name)
  .sort();
const metaOf = (folder: string) => JSON.parse(readFileSync(join(FIGURES, folder, "meta.json"), "utf8")) as MetaFile;

describe("figure folders", () => {
  it("each hold the component and its framing", () => {
    for (const folder of folders) {
      expect(existsSync(join(FIGURES, folder, "Figure.tsx")), `${folder}/Figure.tsx`).toBe(true);
      expect(existsSync(join(FIGURES, folder, "meta.json")), `${folder}/meta.json`).toBe(true);
    }
  });

  it("name each figure by the id in its meta.json", () => {
    expect(folders.length).toBeGreaterThan(0);
    for (const folder of folders) expect(metaOf(folder).id).toBe(folder);
  });

  it("give the component registry and the framing the same ids", () => {
    expect(Object.keys(EXPLORABLE_COMPONENTS).sort()).toEqual(folders);
    expect(Object.keys(EXPLORABLE_META).sort()).toEqual(folders);
  });

  it("hand each figure the framing and beats authored in its own meta.json", () => {
    for (const folder of folders) {
      const meta = metaOf(folder);
      expect(EXPLORABLE_META[folder]).toEqual({
        question: meta.question,
        fixedConditions: meta.fixed_conditions,
        notImplied: meta.not_implied,
        beats: (meta.beats ?? []).map((beat) => ({
          settings: beat.settings,
          durationS: beat.duration_s,
          captionJa: beat.caption_ja,
          narrationJa: beat.narration_ja,
        })),
      });
    }
  });
});
