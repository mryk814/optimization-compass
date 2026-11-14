import { readdirSync, readFileSync } from "node:fs";

import type { Locator } from "@playwright/test";

import { expect, test } from "./fixtures/test";
import { expectNoHighImpactViolations } from "./helpers/accessibility";
import { expectNoHorizontalOverflow, gotoAtlasRoute } from "./helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

// Every figure folder, in every published article that embeds it, gets these checks; nothing
// here lists figures by hand. A figure's own interactions go in e2e/explorables/<id>.spec.ts.
const figuresDir = new URL("../src/features/explorable/figures/", import.meta.url);
const ids = readdirSync(figuresDir, { withFileTypes: true })
  .filter((entry) => entry.isDirectory())
  .map((entry) => (JSON.parse(readFileSync(new URL(`${entry.name}/meta.json`, figuresDir), "utf8")) as { id: string }).id)
  .sort();
const { pages } = JSON.parse(readFileSync(new URL("../public/data/content.json", import.meta.url), "utf8")) as {
  pages: Array<{ content_id: string; html: string }>;
};
const figures = ids.flatMap((id) => pages
  .filter((page) => page.html.includes(`data-explorable-id="${id}"`))
  .map((page) => ({ id, label: `${id}（${page.content_id}）`, route: `/learn/${page.content_id}` })));

test("記事に埋め込まれた動く図を見つける", () => {
  expect(ids.length).toBeGreaterThan(0);
  expect(figures.length).toBeGreaterThan(0);
});

// The live figure has replaced the static fallback and shows its question. `.ex-question`
// rather than the text 見る問い: the Bayesian optimisation figure opens on its own first step.
async function expectLiveFigure(region: Locator) {
  await expect(region.locator(".ex-question").first()).toBeVisible();
  await expect(region.locator(".explorable-fallback, .ex-loading")).toHaveCount(0);
}

for (const figure of figures) {
  test(`@critical ${figure.label}の動く図が表示され、axe違反がない`, async ({ page, baseURL }, testInfo) => {
    await gotoAtlasRoute(page, requiredBaseURL(baseURL), figure.route);
    const region = page.locator(`[data-explorable-id="${figure.id}"]`);
    await expectLiveFigure(region);
    await region.scrollIntoViewIfNeeded();
    await expectNoHighImpactViolations(page, testInfo, `explorable-${figure.label}`);
  });

  test(`${figure.label}の図が375pxで横にはみ出さず、文字が縮まない`, async ({ page, baseURL }) => {
    await page.setViewportSize({ width: 375, height: 800 });
    await gotoAtlasRoute(page, requiredBaseURL(baseURL), figure.route);
    const region = page.locator(`[data-explorable-id="${figure.id}"]`);
    await expectLiveFigure(region);
    await expectNoHorizontalOverflow(page);
    // The SVG uses one unit per CSS pixel, so rendered chart text keeps its 13px size.
    // A figure drawn in HTML (cards, tables) has no chart text to measure.
    const chartText = region.locator("svg text");
    if ((await chartText.count()) === 0) return;
    const rendered = await chartText.first().evaluate((node) => {
      const box = node.getBoundingClientRect();
      const style = getComputedStyle(node);
      return { size: Number.parseFloat(style.fontSize), height: box.height };
    });
    expect(rendered.size).toBeGreaterThanOrEqual(12);
    expect(rendered.height).toBeGreaterThanOrEqual(10);
  });
}
