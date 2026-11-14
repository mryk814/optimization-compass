/**
 * Reader-facing framing of each figure, read from `figures/<id>/meta.json`. Those files are also
 * the Python authority: `src/optimization_compass/explorables.py` validates them (fields, beats,
 * id = folder name) whenever content is built. This module only reshapes them for the site.
 *
 * It stays apart from `registry.tsx`: only the figures import it, so an article without a figure
 * does not download every figure's text.
 */
import { figureIdOf } from "./registry";
import type { SceneBeat } from "./scene";

export interface ExplorableMeta {
  question: string;
  fixedConditions: string;
  notImplied: string;
  /** Guided scene (ADR 0018). Empty when the figure has none. */
  beats: readonly SceneBeat[];
}

/** One `meta.json` as authored; the Python model `Explorable` is its schema. */
export interface MetaFile {
  id: string;
  title_ja: string;
  question: string;
  fixed_conditions: string;
  not_implied: string;
  beats?: ReadonlyArray<{
    settings: Record<string, number | string>;
    duration_s: number;
    caption_ja: string;
    narration_ja: string;
  }>;
}

export function toExplorableMeta(file: MetaFile): ExplorableMeta {
  return {
    question: file.question,
    fixedConditions: file.fixed_conditions,
    notImplied: file.not_implied,
    beats: (file.beats ?? []).map((beat) => ({
      settings: beat.settings,
      durationS: beat.duration_s,
      captionJa: beat.caption_ja,
      narrationJa: beat.narration_ja,
    })),
  };
}

const files = import.meta.glob<MetaFile>("./figures/*/meta.json", { eager: true, import: "default" });

export const EXPLORABLE_META: Readonly<Record<string, ExplorableMeta>> = Object.fromEntries(
  Object.entries(files).map(([path, file]) => [figureIdOf(path), toExplorableMeta(file)]),
);
