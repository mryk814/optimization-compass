import { expect, test } from "@playwright/test";

import { comparisonId, searchTreeComparisonFixture } from "./search-tree-comparison-fixture";

const basePath = "/optimization-compass/";

test("search-tree comparisonは375pxで1列になり、page全体を横overflowさせない", async ({ page }) => {
  const published = await page.request.get(`${basePath}data/comparisons.json`);
  expect(published.ok()).toBe(true);
  const datasetVersion = String((await published.json()).dataset_version);
  await page.route(/\/optimization-compass\/data\/comparisons\.json$/u, (route) => route.fulfill({
    json: searchTreeComparisonFixture(datasetVersion),
  }));

  await page.goto(`${basePath}#/compare/${comparisonId}`);
  const cards = page.locator(".search-tree-comparison-card");
  await expect(cards).toHaveCount(2);
  const first = await cards.nth(0).boundingBox();
  const second = await cards.nth(1).boundingBox();
  expect(first).not.toBeNull();
  expect(second).not.toBeNull();
  expect(Math.abs(second!.x - first!.x)).toBeLessThan(2);
  expect(second!.y).toBeGreaterThan(first!.y + first!.height);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});
