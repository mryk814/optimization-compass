import { test, expect } from "./fixtures/test";
import { gotoAtlasRoute } from "./helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

test("Homeが実Caseを先に見せてTheaterとCompareまで進める", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/");

  await expect(
    page.getByRole("heading", { level: 1, name: "最適化したい。でも、何をどう解けばいい？" }),
  ).toBeVisible();
  await expect(page.getByRole("link", { name: "条件から診断する" })).toBeVisible();
  await expect(page.getByText("選ばない理由")).toBeVisible();

  const casePreview = page.locator(".home-case-preview");
  const caseTitle = casePreview.getByRole("heading", { level: 2 });
  const title = await caseTitle.textContent();
  await casePreview.getByRole("link", { name: "このCaseを辿る →" }).click();

  await expect(page).toHaveURL(/#\/gallery\//u);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(title ?? "");

  await page.getByRole("link", { name: /固定した1 runを追う/u }).click();
  await expect(page).toHaveURL(/#\/theater\//u);
  await page.waitForLoadState("networkidle");

  await page.goBack();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(title ?? "");
  await page.getByRole("link", { name: /固定条件と変えた条件を比べる/u }).click();
  await expect(page).toHaveURL(/#\/compare\//u);
});

test("Diagnoseの推薦カードから対応するMap nodeへ移動する", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/");
  await page.getByRole("link", { name: "条件から診断する" }).click();
  const firstQuestion = page.getByRole("group", {
    name: "x（決めるもの）はどの種類ですか？",
  });
  await firstQuestion.getByRole("button", { name: /^0-1/u }).click();

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

  await page.getByRole("link", { name: "問題構造Mapで位置を確認" }).click();
  await expect(page.getByRole("heading", { level: 2, name: "連続" })).toBeVisible();
  await expect(page.locator('[role="treeitem"][aria-selected="true"]')).toContainText("連続");

  await page.goBack();
  await expect(page.getByRole("heading", { level: 1, name: "高価な実験の設定を探す" })).toBeVisible();
  await page.getByRole("link", { name: "この特徴で診断する" }).click();
  await expect(page.getByRole("button", { name: "連続" })).toHaveAttribute("aria-pressed", "true");

  await page.goBack();
  await expect(page.getByRole("heading", { level: 1, name: "高価な実験の設定を探す" })).toBeVisible();
  await page.getByRole("link", { name: "Nelder–Mead単体法" }).click();
  await expect(page).toHaveURL(/#\/methods\/M_NELDER_MEAD\?state=/u);
  await expect(page.getByRole("heading", { level: 1, name: /Nelder[–-]Mead/u })).toBeVisible();
  await expect(page.getByRole("heading", { level: 1, name: "ページが見つかりません" })).toHaveCount(0);
});

test("canonical Gallery caseで候補・条件付き・除外理由を区別できる", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/gallery/EC013");

  await expect(page.getByRole("heading", { level: 1, name: "観測データから非線形model parameterを推定する" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 2, name: "候補・条件付き・除外を理由で分ける" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 3, name: "候補" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 3, name: "条件付き" })).toBeVisible();
  await expect(page.getByText(/初期値が十分よく/u)).toBeVisible();
  await expect(page.getByRole("heading", { level: 3, name: "避ける" })).toBeVisible();
  await expect(page.getByText(/残差とJacobianの構造を捨て/u)).toBeVisible();
  await expect(page.locator("pre code")).toContainText("least_squares");

  await page.getByRole("link", { name: "この特徴で診断する" }).click();
  await expect(page.getByRole("button", { name: "連続" })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByRole("button", { name: "誤差の一覧を計算できる" })).toHaveAttribute("aria-pressed", "true");
});

test("global検索が略語・自然文・URL filterを横断する", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/search?q=BO&type=method");

  await expect(page.getByRole("heading", { level: 2, name: /ベイズ最適化/u })).toBeVisible();
  await expect(page.getByText(/一致: 別名・略語/u).first()).toBeVisible();
  await expect(page.getByRole("checkbox", { name: /手法/u })).toBeChecked();

  const input = page.getByRole("searchbox", { name: "検索" });
  await input.fill("配送順を決めたい");
  await page.getByText(/^手法 \d+$/u).click();
  await page.getByText(/^問題 \d+$/u).click();
  await expect(page.getByRole("checkbox", { name: /手法/u })).not.toBeChecked();
  await expect(page.getByRole("checkbox", { name: /問題/u })).toBeChecked();
  await expect(page.getByRole("heading", { level: 2, name: "配送・経路最適化" })).toBeVisible();
  await expect(page).toHaveURL(/q=.*&type=problem/u);
});

test("concept教材がcanonical learning graphから次の手法を表示する", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/learn/concept.convexity");

  await expect(page.getByRole("heading", { level: 2, name: "Learning path" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 3, name: "次に見る" })).toBeVisible();
  await expect(page.getByRole("link", { name: /勾配降下法|最急降下法/u })).toBeVisible();
});

test("制約付きsliceで可行性とunconstrained failureを比較できる", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/theater/learning/SCENARIO_CONSTRAINED_DISK");

  await expect(page.getByRole("heading", { level: 1, name: "実行可能領域と制約を無視した失敗を比べる" })).toBeVisible();
  await expect(page.getByText("実行Trace / Executable teaching trace")).toBeVisible();
  await expect(page.getByRole("img", { name: /円の内側が実行可能領域/u })).toBeVisible();
  await expect(page.getByText("active constraint", { exact: true })).toBeVisible();

  const slider = page.getByRole("slider", { name: /現在の反復/u });
  await slider.press("Home");
  await expect(page.getByText("infeasible", { exact: true })).toBeVisible();
  await expect(page.getByText("Traceを進めて確認します。")).toBeVisible();
});

test("Pareto sliceでpreferenceに応じた点をkeyboardで選べる", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/theater/learning/SCENARIO_BIOBJECTIVE_QUADRATIC");

  await expect(page.getByRole("heading", { level: 1, name: "単一bestではなくPareto frontを読む" })).toBeVisible();
  await expect(page.getByText("実行結果 / Executable result")).toBeVisible();
  await expect(page.getByText(/単一bestではありません/u)).toBeVisible();
  await expect(page.getByText(/一般の非凸front/u)).toBeVisible();
  await expect(page.getByTestId("triobjective-scatter")).toBeVisible();
  await expect(page.getByRole("img", { name: "3目的のparallel coordinates fallback" })).toBeVisible();
  await expect(page.getByText(/9×9 gridから得たsampled teaching lens/u)).toBeVisible();

  const selectedF1 = page.locator("dl div").filter({ hasText: "Selected f₁" }).locator("dd");
  const before = await selectedF1.textContent();
  await page.getByRole("slider", { name: /f₁のweight/u }).press("ArrowRight");
  await expect(selectedF1).not.toHaveText(before ?? "");
  const camera = page.getByRole("slider", { name: "3目的表示のカメラ方位" });
  await camera.press("ArrowRight");
  await expect(page.locator(".triobjective-lens output")).toHaveText("320°");
});

test("制約付きCaseをprimary Theater、failure、CompareからCaseへ完走できる", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/gallery/constrained-design");

  await expect(page.getByRole("heading", { level: 1, name: "強度制約を守りながら軽量設計を探す" })).toBeVisible();
  await expect(page.getByRole("link", { name: /固定条件と変えた条件を比べる/u })).toBeVisible();
  const theaterJourney = page.getByRole("link", { name: /固定した1 runを追う/u });
  await theaterJourney.focus();
  await expect(theaterJourney).toBeFocused();
  await theaterJourney.press("Enter");
  await expect(page).toHaveURL(/#\/theater\/learning\/SCENARIO_CONSTRAINED_DISK_FEASIBLE_PATH\?state=/u);
  await expect(page.getByRole("heading", { level: 1, name: "制約を満たす経路で目的を改善する" })).toBeVisible();
  await expect(page.getByText("M_SLSQP", { exact: true }).first()).toBeVisible();

  await page.getByRole("link", { name: /Alternate: 実行可能領域と制約を無視した失敗/u }).click();
  await expect(page).toHaveURL(/#\/theater\/learning\/SCENARIO_CONSTRAINED_DISK\?state=/u);
  await expect(page.getByRole("heading", { level: 1, name: "実行可能領域と制約を無視した失敗を比べる" })).toBeVisible();

  await page.getByRole("link", { name: "Compare: COMPARE_CONSTRAINED_FAILURE" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "制約を守るrunと無視するrunを比べる" })).toBeVisible();
  await page.getByRole("link", { name: /Case: 強度制約/u }).click();
  await expect(page).toHaveURL(/#\/gallery\/constrained-design\?state=/u);
  await expect(page.getByRole("heading", { level: 1, name: "強度制約を守りながら軽量設計を探す" })).toBeVisible();
});

test("parameter推定CaseをTRF、初期値感度、条件比較からCaseへ完走できる", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/gallery/EC013");

  await page.getByRole("link", { name: /固定した1 runを追う/u }).click();
  await expect(page).toHaveURL(/#\/traces\/exponential-fit-trf\?state=/u);
  await expect(page.getByRole("heading", { level: 1, name: "TRFでbounds付き残差fitを追う" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 2, name: "Metric history" })).toBeVisible();
  await expect(page.getByRole("img", { name: /残差normをoracle evaluationで比較/u })).toBeVisible();

  await page.getByRole("link", { name: /Alternate: 悪い初期値でrankと残差を追う/u }).click();
  await expect(page).toHaveURL(/#\/traces\/exponential-fit-trf-poor-init\?state=/u);
  await expect(page.getByRole("heading", { level: 1, name: "悪い初期値でrankと残差を追う" })).toBeVisible();
  await page.getByRole("link", { name: "Compare: COMPARE_EXPONENTIAL_FIT_SOLVER_CONDITIONS" }).click();

  await expect(page.getByRole("heading", { level: 1, name: "非線形fitでsolver条件を比べる" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 2, name: "Metric history" })).toBeVisible();
  await expect(page.getByRole("img", { name: /oracle evaluationで比較/u })).toHaveCount(3);
  await page.getByRole("link", { name: /Case: 観測データから非線形model parameterを推定する/u }).click();
  await expect(page).toHaveURL(/#\/gallery\/EC013\?state=/u);
  await expect(page.getByRole("heading", { level: 1, name: "観測データから非線形model parameterを推定する" })).toBeVisible();
});

test("Galleryからcanonical comparisonへ移動できる", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/gallery/hyperparameter-search");

  await expect(page.getByRole("heading", { level: 1, name: "高価な実験の設定を探す" })).toBeVisible();
  await expect(page.getByText("primary Theater 未接続")).toBeVisible();
  await page.getByRole("link", { name: /固定条件と変えた条件を比べる/u }).click();
  await expect(page).toHaveURL(/#\/compare\/COMPARE_GRADIENT_FAMILY\?state=/u);
});
