import { expect, test } from "@playwright/test";

import { gotoAtlasRoute } from "./helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

test("Theater catalogからfailure runを選びCaseとCompareへ戻れる", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/theater");
  await expect(page.getByText("19 / 19 scenarios")).toBeVisible();
  await page.getByLabel("見る目的").selectOption("failure_contrast");
  await expect(page.getByText("5 / 19 scenarios")).toBeVisible();
  await page.getByRole("link", { name: /実行可能領域と制約を無視した失敗を比べる/u }).click();
  await expect(page.getByRole("heading", { level: 2, name: "このrunで見るもの" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 3, name: /Case: 強度制約/u })).toBeVisible();
  await expect(page.getByRole("link", { name: "Caseへ戻る" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Compare: COMPARE_CONSTRAINED_FAILURE" })).toBeVisible();
});

test("Theater catalogのBO variantが指定presetを開く", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/theater");
  await page.getByLabel("問題domain").selectOption("black-box");
  await page.getByRole("link", { name: /exploit \/ small_noise/u }).click();
  await expect(page.getByLabel("探索方針")).toHaveValue("exploit");
  await expect(page.getByLabel("観測noise")).toHaveValue("small_noise");
  await expect(page.getByText(/noise σ=0\.08/u)).toBeVisible();
});
