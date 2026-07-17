import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import { comparisonId, searchTreeComparisonFixture } from "./search-tree-comparison-fixture";

const basePath = "/optimization-compass/";

test("search-tree comparisonを同じevaluationで同期し、停止状態を区別できる", async ({ page }) => {
  const published = await page.request.get(`${basePath}data/comparisons.json`);
  expect(published.ok()).toBe(true);
  const datasetVersion = String((await published.json()).dataset_version);
  await page.route(/\/optimization-compass\/data\/comparisons\.json$/u, (route) => route.fulfill({
    json: searchTreeComparisonFixture(datasetVersion),
  }));

  await page.goto(`${basePath}#/compare/${comparisonId}`);
  await expect(page.getByRole("heading", { level: 1, name: "探索を続けるrunとnode予算停止" })).toBeVisible();
  await page.getByLabel("評価回数位置").fill("4");

  await expect(page.getByLabel("探索継続runの同期指標")).toContainText("探索中");
  await expect(page.getByLabel("node予算停止runの同期指標")).toContainText("予算停止・未証明");
  await expect(page.getByLabel("node予算停止runの同期指標")).toContainText("Absolute gap2.00");
  await expect(page.getByText("node予算に到達 · evaluation 4")).toBeVisible();
  expect(await page.locator("#comparison-search-tree-heading-0").count()).toBe(1);
  expect(await page.locator("#comparison-search-tree-heading-1").count()).toBe(1);

  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  const serious = results.violations.filter((violation) => (
    violation.impact === "serious" || violation.impact === "critical"
  ));
  expect(serious).toEqual([]);
});
