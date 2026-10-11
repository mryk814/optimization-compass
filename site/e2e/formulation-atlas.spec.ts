import { expect, test } from "./fixtures/test";
import { expectNoHighImpactViolations } from "./helpers/accessibility";
import { expectNoHorizontalOverflow, gotoAtlasRoute } from "./helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

test("@critical 定式化の辞書で日常の言葉から形を引ける", async ({ page, baseURL }, testInfo) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/formulations");
  await expect(page.getByRole("heading", { level: 1, name: "定式化の辞書" })).toBeVisible();
  await page.getByLabel("形を引く").fill("外れ値");
  await page.getByRole("link", { name: /外れ値を含むrobust regression/u }).click();
  await expect(page.getByRole("heading", { level: 1, name: "外れ値を含むrobust regression" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 2, name: "標準形を読む", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { level: 2, name: "小さな例", exact: true })).toBeVisible();
  await expectNoHighImpactViolations(page, testInfo, "formulation-robust-regression");
});

test("記事のない型も標準形と候補手法を引ける", async ({ page, baseURL }, testInfo) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/formulations/PA019");
  await expect(page.getByText("この形の解説はまだありません")).toBeVisible();
  await expect(page.getByRole("region", { name: "定式化のコンパス" })).toBeVisible();
  await expectNoHighImpactViolations(page, testInfo, "formulation-skeleton");
});

test("@critical 線形計画のコンパスから一般の形へ進み、解説と動く図を読める", async ({ page, baseURL }, testInfo) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/formulations/PA017");
  const compass = page.getByRole("region", { name: "定式化のコンパス" });
  await expect(compass.getByRole("link", { name: "凸二次計画" })).toBeVisible();
  await expect(page.locator('[data-explorable-id="lp-vertex-walk"]')).toBeVisible();
  await expectNoHighImpactViolations(page, testInfo, "formulation-article");
  await compass.getByRole("link", { name: "凸二次計画" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "凸二次計画" })).toBeVisible();
});

test("formulation article alias redirects to its formulation page", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/learn/concept.linear-program");
  await expect(page).toHaveURL(/#\/formulations\/PA017$/u);
});

test("定式化から辞書へ戻ると同じ分類の見出しへ移動する", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/formulations/PA034");
  await page.getByRole("link", { name: "定式化の辞書 / データへの当てはめ", exact: true }).click();
  await expect(page).toHaveURL(/#\/formulations#family-fitting$/u);
  const heading = page.locator("#family-fitting");
  await expect.poll(() => heading.evaluate((element) => Math.abs(element.getBoundingClientRect().top))).toBeLessThan(150);
});

test("解説の通信失敗を記事未作成と区別する", async ({ page, baseURL, browserLog }) => {
  browserLog.allowError(/net::ERR_FAILED.*\/data\/content\.json/u);
  await page.route("**/data/content.json", (route) => route.abort());
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/formulations/PA017");
  await expect(page.getByRole("alert")).toContainText("解説の読み込みに失敗しました");
  await expect(page.getByText("この形の解説はまだありません")).toHaveCount(0);
});

test("@critical 道筋の次の問いへ進むと、進み具合が残る", async ({ page, baseURL }, testInfo) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/paths/formulation-basics");
  await expect(page.getByRole("heading", { level: 1, name: "定式化の最初の一歩" })).toBeVisible();
  await expectNoHighImpactViolations(page, testInfo, "learning-path");
  await page.getByRole("link", { name: "線形計画", exact: true }).click();
  await expect(page.getByRole("navigation", { name: "学ぶ道筋での位置" })).toContainText("2 / 11");
  const next = page.getByRole("complementary", { name: "道筋の次の一歩" });
  await next.getByRole("link", { name: /次の問い（3 \/ 11）/u }).click();
  await expect(page.getByRole("navigation", { name: "学ぶ道筋での位置" })).toContainText("3 / 11");
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/paths/formulation-basics");
  await expect(page.getByText("1 / 11 ステップ")).toBeVisible();
});

test("@critical はじめての人は診断なしで道筋に入り、つまずいたら戻って帰ってこられる", async ({ page, baseURL }, testInfo) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/");
  await page.getByRole("link", { name: /はじめての人へ/u }).click();
  await expect(page.getByRole("heading", { level: 1, name: "最適化って、結局なにをするの？" })).toBeVisible();
  await expect(page.getByRole("link", { name: /定式化の辞書で式から引く/u })).toBeVisible();
  await expectNoHighImpactViolations(page, testInfo, "beginner-path");
  await page.getByRole("link", { name: /最初の問いへ/u }).click();
  await expect(page.getByRole("navigation", { name: "学ぶ道筋での位置" })).toContainText("1 / 4");
  const next = page.getByRole("complementary", { name: "道筋の次の一歩" });
  await expect(next.getByRole("heading", { name: "つまずいたら戻る" })).toBeVisible();
  await next.getByRole("link", { name: /「守ること（制約）」が/u }).click();
  await expect(page.getByRole("heading", { level: 1, name: "制約の分類" })).toBeVisible();
  await page.getByRole("link", { name: /1 番目「線形計画」へ帰る/u }).click();
  await expect(page.getByRole("navigation", { name: "学ぶ道筋での位置" })).toContainText("1 / 4");
});

for (const route of ["/formulations", "/formulations/PA017", "/paths/formulation-basics", "/paths/what-is-optimization"]) {
  test(`${route} は375pxで横にはみ出さない`, async ({ page, baseURL }) => {
    await page.setViewportSize({ width: 375, height: 800 });
    await gotoAtlasRoute(page, requiredBaseURL(baseURL), route);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expectNoHorizontalOverflow(page);
  });
}
