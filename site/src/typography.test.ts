import { readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, test } from "vitest";

const contract = readFileSync(join(process.cwd(), "src", "typography.css"), "utf8");

function remToken(name: string): number {
  const match = contract.match(new RegExp(`--${name}:\\s*([0-9.]+)rem;`, "u"));
  if (!match) throw new Error(`Missing rem typography token --${name}`);
  return Number(match[1]);
}

function pixelToken(name: string): number {
  const match = contract.match(new RegExp(`--${name}:\\s*([0-9.]+)px;`, "u"));
  if (!match) throw new Error(`Missing pixel typography token --${name}`);
  return Number(match[1]);
}

describe("Atlas typography contract", () => {
  test("keeps primary, metadata, and chart roles above their readability floors", () => {
    expect(remToken("type-body")).toBeGreaterThanOrEqual(1);
    expect(remToken("type-support")).toBeGreaterThanOrEqual(1);
    expect(remToken("type-meta")).toBeGreaterThanOrEqual(0.875);
    expect(remToken("type-label")).toBeGreaterThanOrEqual(0.875);
    expect(pixelToken("type-chart")).toBeGreaterThanOrEqual(13);
    expect(pixelToken("type-chart-compact")).toBeGreaterThanOrEqual(12);
  });

  test("uses semantic tokens instead of new one-off font sizes", () => {
    const declarations = contract
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line.startsWith("font-size:"));

    expect(declarations.length).toBeGreaterThan(0);
    for (const declaration of declarations) {
      expect(declaration).toMatch(/^font-size:\s*(?:var\(--type-|clamp\()/u);
    }
  });

  test.each([
    ".atlas-page-header p:not(.eyebrow)",
    ".content-card p",
    ".gallery-question-panel p:not(.eyebrow)",
    ".comparison-contract-v2 .comparison-question",
    ".map-tree",
    ".theater-first-action p:not(.eyebrow)",
    ".coverage-table-wrap table",
    ".bo-figure text",
  ])("covers the shared surface %s", (selector) => {
    expect(contract).toContain(selector);
  });
});
