import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative, resolve } from "node:path";
import { describe, expect, it } from "vitest";

// Article bodies share one look, with linear least squares as the reference
// (docs/content-reading-principles.md §11). Only the shared layout may scope `.markdown-body`;
// a page-specific ancestor (`.formulation-article`, `.method-learning`, …) would restyle one kind
// of article. Rules inside explorable frames (`.markdown-body .ex-…`) style figures, not prose.
const SOURCE = resolve(__dirname, "../..");
const ALLOWED_SCOPES = new Set([".compiled-content-layout", ".compiled-content-layout--lesson"]);

function cssFiles(directory: string): string[] {
  return readdirSync(directory).flatMap((name) => {
    const path = join(directory, name);
    if (statSync(path).isDirectory()) return cssFiles(path);
    return path.endsWith(".css") ? [path] : [];
  });
}

function selectors(css: string): string[] {
  const withoutComments = css.replace(/\/\*[\s\S]*?\*\//g, "");
  return [...withoutComments.matchAll(/([^{}]+)\{/g)]
    .flatMap((match) => match[1].split(","))
    .map((selector) => selector.trim())
    .filter((selector) => selector.includes(".markdown-body") && !selector.startsWith("@"));
}

describe("article body style contract", () => {
  it("lets only the shared article layout scope .markdown-body", () => {
    const violations: string[] = [];
    for (const file of cssFiles(SOURCE)) {
      for (const selector of selectors(readFileSync(file, "utf8"))) {
        const ancestors = selector.split(/\.markdown-body\b/)[0].trim();
        if (!ancestors || selector.includes(":not(.markdown-body")) continue;
        const scopes = ancestors.split(/\s+/).filter((part) => part !== ">");
        if (scopes.every((scope) => ALLOWED_SCOPES.has(scope))) continue;
        violations.push(`${relative(SOURCE, file)}: ${selector}`);
      }
    }
    expect(violations).toEqual([]);
  });
});
