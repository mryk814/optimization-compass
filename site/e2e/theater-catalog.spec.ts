import { expect, test } from "@playwright/test";

import { gotoAtlasRoute } from "./helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

test("Theater catalogからfailure runを選びCaseとCompareへ戻れる", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/theater");
  const filters = page.locator('.theater-catalog-filters[aria-label="シナリオの絞り込み"]');
  const scenarioCount = filters.getByText(/^\d+ \/ \d+ シナリオ$/u);
  await expect(scenarioCount).toHaveText(/^(\d+) \/ \1 シナリオ$/u);
  const publishedCount = (await scenarioCount.textContent())?.match(/^\d+ \/ (\d+) シナリオ$/u)?.[1];
  if (!publishedCount) throw new Error("Published scenario count is missing.");

  await page.getByLabel("見る目的").selectOption("failure_contrast");
  await expect(scenarioCount).toHaveText(`7 / ${publishedCount} シナリオ`);
  const failureRun = page.getByRole("link", { name: /実行可能領域と制約を無視した失敗を比べる/u });
  await expect(failureRun).toBeVisible();
  await failureRun.click();
  await expect(page.getByRole("heading", { level: 2, name: "このrunで見るもの" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 3, name: /ケース: 強度制約/u })).toBeVisible();
  await expect(page.getByRole("link", { name: "Caseへ戻る" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Compareへ: COMPARE_CONSTRAINED_FAILURE" })).toBeVisible();
});

test("Theater catalogのBO variantが指定presetを開く", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/theater");
  await page.locator('select[aria-label="問題領域"]').selectOption("black-box");
  await page.getByRole("link", { name: /exploit \/ small_noise/u }).click();
  await expect(page.getByLabel("探索方針")).toHaveValue("exploit");
  await expect(page.getByLabel("観測ノイズ")).toHaveValue("small_noise");
  await expect(page.getByText(/noise σ=0\.08/u)).toBeVisible();
});
