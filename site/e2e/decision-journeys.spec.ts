import { test, expect } from "./fixtures/test";
import { gotoAtlasRoute } from "./helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

test("Diagnoseの推薦カードから対応するMap nodeへ移動する", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/");
  await page.getByRole("link", { name: "診断を始める" }).click();
  const firstQuestion = page.getByRole("group", {
    name: "変数は連続・整数・0-1・カテゴリ・混合のどれですか？",
  });
  await firstQuestion.getByRole("button", { name: "0-1" }).click();

  const firstChoiceBand = page.locator("section").filter({
    has: page.getByRole("heading", { level: 2, name: "第一候補" }),
  });
  const recommendation = firstChoiceBand.locator("article").filter({
    has: page.getByRole("button", { name: "地図で見る" }),
  }).first();
  const methodName = await recommendation.getByRole("heading", { level: 3 }).textContent();
  await recommendation.getByRole("button", { name: "地図で見る" }).click();

  await expect(page).toHaveURL(/#\/map\?state=/u);
  await expect(page.getByRole("tree", { name: "最適化問題の構造" })).toBeVisible();
  await expect(page.locator('[role="treeitem"][aria-selected="true"]')).toHaveCount(1);
  await expect(page.getByRole("complementary").getByText(methodName ?? "", { exact: true })).toBeVisible();
});

test("Gallery caseからMap、Diagnose、method pageへ遷移する", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/gallery");
  await page.getByRole("link", { name: /高価な実験の設定を探す/u }).click();
  await expect(page.getByRole("heading", { level: 1, name: "高価な実験の設定を探す" })).toBeVisible();

  await page.getByRole("link", { name: "分類図上で見る" }).click();
  await expect(page.getByRole("heading", { level: 2, name: "連続" })).toBeVisible();
  await expect(page.locator('[role="treeitem"][aria-selected="true"]')).toContainText("連続");

  await page.goBack();
  await expect(page.getByRole("heading", { level: 1, name: "高価な実験の設定を探す" })).toBeVisible();
  await page.getByRole("link", { name: "この特徴で診断する" }).click();
  await expect(page.getByRole("button", { name: "連続" })).toHaveAttribute("aria-pressed", "true");

  await page.goBack();
  await expect(page.getByRole("heading", { level: 1, name: "高価な実験の設定を探す" })).toBeVisible();
  await page.getByRole("link", { name: "Nelder–Mead単体法" }).click();
  await expect(page).toHaveURL(/#\/methods\/M_NELDER_MEAD$/u);
  await expect(page.getByRole("heading", { level: 1, name: /Nelder[–-]Mead/u })).toBeVisible();
  await expect(page.getByRole("heading", { level: 1, name: "ページが見つかりません" })).toHaveCount(0);
});

test("canonical Gallery caseで候補・条件付き・除外理由を区別できる", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/gallery/EC013");

  await expect(page.getByRole("heading", { level: 1, name: "観測データから非線形model parameterを推定する" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 2, name: "候補手法" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 3, name: "条件付き" })).toBeVisible();
  await expect(page.getByText(/初期値が十分よく/u)).toBeVisible();
  await expect(page.getByRole("heading", { level: 3, name: "避ける" })).toBeVisible();
  await expect(page.getByText(/残差とJacobianの構造を捨て/u)).toBeVisible();
  await expect(page.locator("pre code")).toContainText("least_squares");

  await page.getByRole("link", { name: "この特徴で診断する" }).click();
  await expect(page.getByRole("button", { name: "連続" })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByRole("button", { name: "残差ベクトル" })).toHaveAttribute("aria-pressed", "true");
});
