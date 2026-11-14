import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative, sep } from "node:path";

import { describe, expect, it } from "vitest";

import { EXPLORABLE_META, type MetaFile } from "./figureMeta";
import { EXPLORABLE_COMPONENTS } from "./registry";

// Adding a figure means adding one folder. These checks hold the folder contract that
// replaces the old hand-kept lists (registry entries, the meta.ts copy of explorables.json).
const SRC = join(__dirname, "..", "..");
const FIGURES = join(__dirname, "figures");
const folders = readdirSync(FIGURES, { withFileTypes: true })
  .filter((entry) => entry.isDirectory())
  .map((entry) => entry.name)
  .sort();
const metaOf = (folder: string) => JSON.parse(readFileSync(join(FIGURES, folder, "meta.json"), "utf8")) as MetaFile;

function sourceFiles(directory: string): string[] {
  return readdirSync(directory).flatMap((name) => {
    const path = join(directory, name);
    if (statSync(path).isDirectory()) return sourceFiles(path);
    return /\.(tsx?|css)$/u.test(name) && !/\.test\.tsx?$/u.test(name) ? [path] : [];
  });
}

/** Selectors of every style rule; @media blocks are entered, @keyframes blocks skipped. */
function selectorsOf(css: string): string[] {
  const text = css.replace(/\/\*[\s\S]*?\*\//gu, "");
  const selectors: string[] = [];
  let start = 0;
  for (let index = 0; index < text.length; index += 1) {
    if (text[index] === "{") {
      const prelude = text.slice(start, index).trim();
      if (prelude.startsWith("@keyframes")) {
        let depth = 1;
        while (depth > 0) {
          index += 1;
          if (text[index] === "{") depth += 1;
          if (text[index] === "}") depth -= 1;
        }
      } else if (prelude && !prelude.startsWith("@")) {
        selectors.push(...prelude.split(",").map((part) => part.trim()));
      }
      start = index + 1;
    } else if (text[index] === "}" || text[index] === ";") {
      start = index + 1;
    }
  }
  return selectors;
}

const classesIn = (selector: string) => [...selector.matchAll(/\.([A-Za-z_][\w-]*)/gu)].map((match) => match[1]);

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

describe("figure styles", () => {
  // A figure's style.css arrives with its chunk and then applies to the whole page. A rule must
  // name at least one class that nothing outside the figure's folder uses (or the figure's own
  // [data-explorable-id]); otherwise it would restyle other figures, or style them only when this
  // one happens to be on the same page, as a copied folder that kept its class names would.
  // Rules that several figures share belong in explorable.css.
  const files = sourceFiles(SRC).map((path) => {
    const text = readFileSync(path, "utf8");
    return {
      path,
      tokens: new Set(text.match(/[A-Za-z_][\w-]*/gu) ?? []),
      prefixes: [...text.matchAll(/([a-z][a-z0-9]*(?:-[a-z0-9]+)*-)\$\{/gu)].map((match) => match[1]),
    };
  });

  it("scope every rule to a class that nothing outside the figure's folder uses", () => {
    const problems: string[] = [];
    for (const folder of folders) {
      const stylePath = join(FIGURES, folder, "style.css");
      if (!existsSync(stylePath)) continue;
      const inside = join(FIGURES, folder) + sep;
      const outside = files.filter((file) => !file.path.startsWith(inside));
      const usersOutside = (name: string) => outside
        .filter((file) => file.tokens.has(name) || file.prefixes.some((prefix) => name.startsWith(prefix)))
        .map((file) => relative(SRC, file.path));
      for (const selector of selectorsOf(readFileSync(stylePath, "utf8"))) {
        const ids = [...selector.matchAll(/\[data-explorable-id="([^"]+)"\]/gu)].map((match) => match[1]);
        if (ids.some((id) => id !== folder)) problems.push(`${folder}/style.css: \`${selector}\` targets another figure`);
        if (ids.includes(folder)) continue;
        const users = classesIn(selector).map(usersOutside);
        if (users.every((list) => list.length > 0)) {
          problems.push(`${folder}/style.css: \`${selector}\` is not scoped to this figure (also used by ${[...new Set(users.flat())].slice(0, 3).join(", ")})`);
        }
      }
    }
    expect(problems).toEqual([]);
  });
});
