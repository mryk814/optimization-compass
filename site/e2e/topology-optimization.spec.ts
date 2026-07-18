import { expect, test } from "@playwright/test";

import { gotoAtlasRoute } from "./helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

test("topology Caseからfield Theater、Compare、教材を辿れる", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/gallery/topology-cantilever");
  await expect(page.getByRole("heading", { level: 1, name: "片持ちはりの材料配置を軽くする" })).toBeVisible({ timeout: 15_000 });

  await page.getByRole("link", { name: /固定した1回の実行を追う/u }).click();
  await expect(page).toHaveURL(/#\/theater\/learning\/SCENARIO_TOPOLOGY_SIMP_OC\?state=/u);
  await expect(page.getByRole("heading", { level: 1, name: "片持ちはりの設計fieldを更新過程で読む" })).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole("img", { name: "設計密度 density" })).toBeVisible();
  await expect(page.getByRole("img", { name: "状態 state" })).toBeVisible();
  await expect(page.getByRole("img", { name: "filter後の感度" })).toBeVisible();
  await expect(page.getByText("checkerboard score", { exact: true })).toBeVisible();

  await page.getByRole("link", { name: /Compareへ: COMPARE_TOPOLOGY_OC_MMA/u }).click();
  await expect(page).toHaveURL(/#\/compare\/COMPARE_TOPOLOGY_OC_MMA\?state=/u);
  await expect(page.getByRole("heading", { level: 1, name: "同じ密度fieldでOCとMMAを比べる" })).toBeVisible({ timeout: 15_000 });

  await page.getByRole("link", { name: /ケース: 片持ちはりの材料配置を軽くする/u }).click();
  await expect(page).toHaveURL(/#\/gallery\/topology-cantilever\?state=/u);
  await page.getByRole("link", { name: /SIMP密度法/u }).first().click();
  await expect(page).toHaveURL(/#\/methods\/M_SIMP_TOPOLOGY/u);
  await expect(page.getByRole("heading", { level: 1, name: "SIMP密度法" })).toBeVisible({ timeout: 15_000 });
});

test("topology failure Theaterはfailure contrastを最初に表示する", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/theater/learning/SCENARIO_TOPOLOGY_CHECKERBOARD");

  await expect(page.getByRole("heading", { level: 1, name: "filterなしのcheckerboard failureを見つける" })).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole("note")).toContainText("Failure Theater");
  await expect(page.getByText("失敗を観察する順番:")).toBeVisible();
  await expect(page.getByRole("combobox", { name: /経路/u })).toHaveValue("topology-no-filter");
  await expect(page.getByText("checkerboard risk", { exact: false }).first()).toBeVisible();
});
