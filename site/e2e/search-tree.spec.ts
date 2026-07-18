import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const basePath = "/optimization-compass/";

test("0-1 Gallery caseから決定的search-treeをkeyboardで再生できる", async ({ page }) => {
  await page.goto(`${basePath}#/gallery/budget-allocation`);
  const theaterLink = page.getByRole("link", { name: /固定した1回の実行を追う/u });
  await expect(theaterLink).toBeVisible();
  await theaterLink.click();
  await expect(page).toHaveURL(/#\/theater\/search-tree\/binary-knapsack-bnb-complete\?state=/u);
  await expect(page.getByRole("heading", { name: "0-1 knapsack: 最適性証明" })).toBeVisible();
  await expect(page.getByText(/実行可能.*search_tree/u)).toBeVisible();
  await expect(page.getByLabel("Best feasible")).toBeVisible();
  await expect(page.getByText("Textual tree summary")).toBeVisible();

  const tree = page.getByRole("tree");
  await expect(tree).toBeVisible();
  await page.getByLabel("フレーム位置").fill("5");
  const firstNode = tree.getByRole("treeitem").first();
  await firstNode.focus();
  await page.keyboard.press("ArrowDown");
  await expect(tree.getByRole("treeitem").nth(1)).toBeFocused();
  await page.getByRole("button", { name: "1フレーム進む" }).click();
  await expect(page.getByLabel("イベント説明")).not.toContainText("説明は未登録");

  await page.getByText("静止画 fallback").click();
  const fallback = page.getByRole("img", { name: /0-1 knapsackの探索木/u });
  await expect(fallback).toBeVisible();
  const response = await page.request.get(await fallback.getAttribute("src") ?? "");
  expect(response.ok()).toBe(true);
});

test("最適性証明とnode予算停止を区別し、重大なa11y違反がない", async ({ page }) => {
  await page.goto(`${basePath}#/theater/search-tree/binary-knapsack-bnb-budget`);
  await expect(page.getByRole("heading", { name: "0-1 knapsack: node予算で停止" })).toBeVisible();
  const seek = page.getByLabel("フレーム位置");
  await seek.fill(await seek.getAttribute("max") ?? "0");
  await expect(page.getByText(/node予算で停止 — 実行可能な候補解/u)).toBeVisible();
  await expect(page.getByLabel("Gap")).not.toHaveText("0.00 (0.0%)");
  await expect(page.getByText(/MIPのBranch-and-Cutは連続緩和/u)).toBeVisible();

  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  const serious = results.violations.filter((violation) => violation.impact === "serious" || violation.impact === "critical");
  expect(serious).toEqual([]);
});
