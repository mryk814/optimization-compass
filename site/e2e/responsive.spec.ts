import { test, expect } from "./fixtures/test";
import { expectNoHighImpactViolations } from "./helpers/accessibility";
import { expectNoHorizontalOverflow, gotoAtlasRoute } from "./helpers/navigation";
import { expectFitsViewport, expectNelderMeadSvg } from "./helpers/visualization";

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

test("375px DiagnoseとGallery detailの主要導線とprompt exportが操作できる", async ({ page, baseURL }, testInfo) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/diagnose");
  const question = page.getByRole("group", {
    name: "x（決めるもの）はどの種類ですか？",
  });
  await question.getByRole("button", { name: /^0-1/u }).click();
  await expect(page.getByRole("button", { name: "地図上で見る" })).toBeVisible();
  await expectNoHorizontalOverflow(page);

  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/gallery/hyperparameter-search");
  await expect(page.getByRole("link", { name: "問題構造Mapで位置を確認" })).toBeVisible();
  await expect(page.getByRole("link", { name: "この特徴で診断する" })).toBeVisible();
  await expect(page.getByRole("link", { name: /固定条件と変えた条件を比べる/u })).toBeVisible();
  await page.getByRole("button", { name: "実装用プロンプトを作る" }).click();
  await expect(page.getByRole("dialog", { name: "実装用プロンプトを作る" })).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await expectNoHighImpactViolations(page, testInfo, "mobile-prompt-export");
});

test("375px Theater controlsが横にはみ出さずstepできる", async ({ page, baseURL }, testInfo) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/theater/nelder-mead");
  const controls = page.getByRole("region", { name: "アルゴリズム再生コントロール" });
  const iteration = controls.getByLabel("iteration");
  const initial = await iteration.textContent();
  await controls.getByRole("button", { name: "1フレーム進む" }).click();
  await expect(iteration).not.toHaveText(initial ?? "");
  await controls.getByRole("button", { name: "1フレーム進む" }).click();
  await expectNoHorizontalOverflow(page);
  await expectNoHighImpactViolations(page, testInfo, "mobile-nelder-mead");
  const plot = page.getByTestId("nelder-mead-explanatory-plot");
  await expectNelderMeadSvg(plot);
  await expectFitsViewport(plot, page);
});

test("375px Theater catalogでscenarioを絞り込める", async ({ page, baseURL }, testInfo) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/theater");
  await expect(page.getByText("18 / 18 scenarios")).toBeVisible();
  await page.getByLabel("問題domain").selectOption("discrete");
  await expect(page.getByText("2 / 18 scenarios")).toBeVisible();
  await expect(page.getByRole("link", { name: /0-1 knapsack: 最適性証明/u })).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await expectNoHighImpactViolations(page, testInfo, "mobile-theater-catalog");
});

test("375px Compare Labで比較条件と非trajectory結果を読める", async ({ page, baseURL }, testInfo) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/compare/COMPARE_CONSTRAINED_FAILURE");
  await expect(page.getByRole("heading", { level: 3, name: "同じもの / Fixed" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 3, name: "違うもの / Changed" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 3, name: "見る指標 / Metrics" })).toBeVisible();
  await expect(page.getByRole("img", { name: /円の内側が実行可能領域/u })).toBeVisible();
  await expect(page.getByRole("link", { name: /Case: 強度制約/u })).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await expectNoHighImpactViolations(page, testInfo, "mobile-compare-feasible-region");
});

test("375px Search-tree Theaterを再生できる", async ({ page, baseURL }, testInfo) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/gallery/budget-allocation");
  await page.getByRole("link", { name: /固定した1 runを追う/u }).click();
  await expect(page.getByRole("heading", { name: "0-1 knapsack: 最適性証明" })).toBeVisible();
  const controls = page.getByRole("region", { name: "アルゴリズム再生コントロール" });
  await controls.getByRole("button", { name: "1フレーム進む" }).click();
  await expect(page.getByRole("tree")).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await expectNoHighImpactViolations(page, testInfo, "mobile-search-tree");
});

test("375px BO Theaterが横にはみ出さずkeyboardでstepできる", async ({ page, baseURL }, testInfo) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/theater/bayesian-optimization");
  const player = page.getByLabel(/Bayesian optimization再生領域/u);
  await player.focus();
  await page.keyboard.press("ArrowRight");
  await expect(page.getByText("Frame 2/8")).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await expectNoHighImpactViolations(page, testInfo, "mobile-bayesian-optimization");
});

test("375px Coverageが横にはみ出さずfilterできる", async ({ page, baseURL }, testInfo) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/coverage");
  await expect(page.getByRole("heading", { name: "Atlas Coverage" })).toBeVisible();
  await page.getByLabel("Subject").selectOption("feature_family");
  await expect(page.getByRole("row")).toHaveCount(11);
  await expectNoHorizontalOverflow(page);
  await expectNoHighImpactViolations(page, testInfo, "mobile-coverage");
});

test("375px Global Searchが横にはみ出さずfilterできる", async ({ page, baseURL }, testInfo) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/search?q=BO&type=method");
  await expect(page.getByRole("heading", { name: /ベイズ最適化/u })).toBeVisible();
  await page.getByRole("combobox", { name: "検索の目的" }).selectOption("understand_method");
  await expectNoHorizontalOverflow(page);
  await expectNoHighImpactViolations(page, testInfo, "mobile-global-search");
});

test("375px 追加教材のtableとcodeがpage全体をはみ出さない", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/learn/cp-sat");
  await expect(page.getByRole("heading", { level: 1, name: "CP-SAT" })).toBeVisible();
  await expect(page.getByRole("region", { name: "教材" })).toBeVisible();
  await expect(page.locator("table")).toBeVisible();
  await expect(page.locator("pre code")).toBeVisible();
  await expect(page.getByRole("heading", { level: 2, name: "Learning path" })).toBeVisible();
  await expectNoHorizontalOverflow(page);
});
