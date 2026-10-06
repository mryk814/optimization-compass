import { expect, test } from "./fixtures/test";
import { expectNoHighImpactViolations } from "./helpers/accessibility";
import { expectNoHorizontalOverflow, gotoAtlasRoute } from "./helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

const SLICE = [
  "/gallery",
  "/gallery/hyperparameter-search",
  "/theater/lenses/hyperparameter-search",
  "/methods/M_BFGS",
  "/compare/COMPARE_BO_ACQUISITION_NOISE_BASELINE",
] as const;

for (const route of SLICE) {
  test(`@critical ${route} は共通の記号で描かれ、axe違反がない`, async ({ page, baseURL }, testInfo) => {
    await gotoAtlasRoute(page, requiredBaseURL(baseURL), route);
    await expect(page.locator(".vs-signature").first()).toBeVisible();
    await expectNoHighImpactViolations(page, testInfo, `visual-system-${route.replaceAll("/", "-")}`);
  });

  test(`${route} は375pxで横にはみ出さない`, async ({ page, baseURL }) => {
    await page.setViewportSize({ width: 375, height: 800 });
    await gotoAtlasRoute(page, requiredBaseURL(baseURL), route);
    await expect(page.locator(".vs-signature").first()).toBeVisible();
    await expectNoHorizontalOverflow(page);
  });
}

test("Caseで除外した手法の目に切り替えると、規則上の扱いと候補に変わる条件が出る", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/gallery/hyperparameter-search");
  await page.getByRole("tab", { name: /BFGS/u }).click();
  const panel = page.getByRole("tabpanel");
  await expect(panel.getByText("診断規則には、この回答でこの手法を外す規則がありません", { exact: false })).toBeVisible();
  await expect(panel.getByText(/勾配が「解析勾配・数値差分」なら、この手法を支える/u)).toBeVisible();
});

test("アルゴリズムの視点では真の地形を隠し、人間の視点で重ねる", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/theater/lenses/hyperparameter-search");
  await expect(page.getByRole("heading", { name: "同じ地形を、3つの計器で測る" })).toBeVisible();
  await expect(page.locator(".vs-terrain")).toHaveCount(0);
  await expect(page.locator(".vs-unseen-field")).toHaveCount(3);
  await page.getByLabel("人間の視点（真の地形を重ねる）").check();
  await expect(page.locator(".vs-terrain")).toHaveCount(3);
  await page.getByRole("button", { name: "最初から" }).click();
  await expect(page.getByText(/切り替えの兆候/u).first()).toBeVisible();
});

test("検索結果のケースと手法に、同じ署名の記号が付く", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/search?q=" + encodeURIComponent("少ない実験で配合条件を絞る"));
  const caseCard = page.locator(".search-result-card").filter({ hasText: "少ない実験で配合条件を絞る" }).first();
  await expect(caseCard.locator(".vs-signature")).toBeVisible();
});

test("CaseからMapへ進むと、同じ回答の署名が詳細欄に出る", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/gallery/hyperparameter-search");
  await page.getByRole("link", { name: "問題構造Mapで位置を確認" }).click();
  await expect(page.locator(".map-signature")).toBeVisible();
  await expect(page.locator(".map-signature")).toContainText("まだ開いている軸 1");
});
