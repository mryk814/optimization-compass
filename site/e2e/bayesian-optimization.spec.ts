import { test, expect } from "./fixtures/test";
import { expectNoHighImpactViolations } from "./helpers/accessibility";
import { gotoAtlasRoute } from "./helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

test("BO Theaterでcanonical scenarioを切り替え、keyboardで次点選択を追える", async ({ page, baseURL }, testInfo) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/gallery/hyperparameter-search");
  await page.getByRole("link", { name: "BO Theaterで点選択を見る" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Bayesian Optimization Theater" })).toBeVisible();
  await expect(page.getByText(/surrogate_uncertainty 1\.0\.0/u)).toBeVisible();
  await expect(page.getByRole("img", { name: /surrogate平均/u })).toBeVisible();

  const player = page.getByLabel(/Bayesian optimization再生領域/u);
  await player.focus();
  await expect(player).toBeFocused();
  await page.keyboard.press("ArrowRight");
  await expect(page.getByText("Frame 2/8")).toBeVisible();
  await page.keyboard.press(" ");
  await expect(page.getByRole("button", { name: "一時停止" })).toBeVisible();
  await page.keyboard.press(" ");

  await page.getByRole("combobox", { name: "観測noise" }).selectOption("small_noise");
  await expect(page.getByText(/noise σ=0\.08/u)).toBeVisible();
  await expect(page.getByRole("link", { name: "Gaussian process Bayesian optimization" })).toBeVisible();
  await expect(page.getByRole("link", { name: "random search" })).toBeVisible();
  await expect(page.getByRole("link", { name: /S059/u })).toBeVisible();
  await expectNoHighImpactViolations(page, testInfo, "bayesian-optimization");
});

test("DiagnoseとMapの高価なblack-box導線からBO Theaterへ進める", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/diagnose");
  const evaluationCost = page.getByRole("group", {
    name: "f(x)や制約を1回計算する時間は？",
  });
  await evaluationCost.getByRole("button", { name: "1時間以上" }).click();
  await expect(page.getByRole("link", { name: "Bayesian Optimization Theaterへ" })).toBeVisible();

  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/map");
  const tree = page.getByRole("tree", { name: "最適化問題の構造" });
  await tree.getByRole("button", { name: "変数と計算資源 を展開" }).click();
  await tree.getByRole("button", { name: "変数の数と疎性・block構造はどの程度ですか？ を展開" }).click();
  await tree.getByRole("treeitem", { name: /10未満（under 10）/u }).click();
  await expect(page.getByRole("link", { name: "Bayesian Optimization Theaterへ" })).toBeVisible();
});
