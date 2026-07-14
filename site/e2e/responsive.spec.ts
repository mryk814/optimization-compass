import { test, expect } from "./fixtures/test";
import { expectNoHighImpactViolations } from "./helpers/accessibility";
import { expectNoHorizontalOverflow, gotoAtlasRoute } from "./helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

test("375px HomeとMapが横にはみ出さず操作できる", async ({ page, baseURL }, testInfo) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/");
  await expect(page.getByRole("link", { name: "地図を見る" })).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await expectNoHighImpactViolations(page, testInfo, "mobile-home");

  await page.getByRole("link", { name: "地図を見る" }).click();
  const tree = page.getByRole("tree", { name: "最適化問題の構造" });
  await tree.getByRole("treeitem").first().click();
  await page.getByRole("button", { name: "詳細" }).click();
  await expect(page.getByRole("button", { name: "詳細" })).toHaveAttribute("aria-pressed", "true");
  await expectNoHorizontalOverflow(page);
  await expectNoHighImpactViolations(page, testInfo, "mobile-map-detail");
});

test("375px DiagnoseとGallery detailの主要導線が操作できる", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/diagnose");
  const question = page.getByRole("group", {
    name: "変数は連続・整数・0-1・カテゴリ・混合のどれですか？",
  });
  await question.getByRole("button", { name: "0-1" }).click();
  await expect(page.getByRole("button", { name: "地図上で見る" })).toBeVisible();
  await expectNoHorizontalOverflow(page);

  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/gallery/hyperparameter-search");
  await expect(page.getByRole("link", { name: "分類図上で見る" })).toBeVisible();
  await expect(page.getByRole("link", { name: "この特徴で診断する" })).toBeVisible();
  await expectNoHorizontalOverflow(page);
});

test("375px Theater controlsが横にはみ出さずstepできる", async ({ page, baseURL }, testInfo) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/theater/nelder-mead");
  const controls = page.getByRole("region", { name: "アルゴリズム再生コントロール" });
  const iteration = controls.getByLabel("iteration");
  const initial = await iteration.textContent();
  await controls.getByRole("button", { name: "1フレーム進む" }).click();
  await expect(iteration).not.toHaveText(initial ?? "");
  await expectNoHorizontalOverflow(page);
  await expectNoHighImpactViolations(page, testInfo, "mobile-nelder-mead");
});
