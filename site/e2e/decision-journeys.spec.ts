import type { Locator } from "@playwright/test";

import { test, expect } from "./fixtures/test";
import { gotoAtlasRoute } from "./helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

function metricValue(scope: Locator, label: string): Locator {
  return scope.getByText(label, { exact: true }).locator("..").locator("dd");
}

test("Homeが実Caseを先に見せてTheaterとCompareまで進める", { tag: "@critical" }, async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/");

  await expect(
    page.getByRole("heading", { level: 1, name: "最適化したい問いを、問題の形にする" }),
  ).toBeVisible();
  await expect(page.getByRole("link", { name: "条件から診断を始める" })).toBeVisible();
  const journey = page.locator(".home-case-journey");
  await expect(journey).toBeVisible();
  await expect(journey.getByText("問いを選ぶ")).toBeVisible();
  await expect(journey.getByText("問題の形にする")).toBeVisible();
  await expect(journey.getByText("動きを見る")).toBeVisible();
  await expect(journey.getByText("条件を比べる")).toBeVisible();

  const details = page.locator(".home-case-disclosure");
  const excludedLabel = details.locator(".home-disposition-excluded > span");
  await expect(excludedLabel).not.toBeVisible();
  await details.locator("summary").click();
  await expect(excludedLabel).toBeVisible();

  const casePreview = page.locator(".home-case-preview");
  const caseTitle = casePreview.getByRole("heading", { level: 2 });
  const title = await caseTitle.textContent();
  await casePreview.getByRole("link", { name: "このCaseの詳細を見る →" }).click();

  await expect(page).toHaveURL(/#\/gallery\//u);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(title ?? "");

  await page.getByRole("link", { name: /固定した1回の実行を追う/u }).click();
  await expect(page).toHaveURL(/#\/theater\//u);
  await page.waitForLoadState("networkidle");

  await page.goBack();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(title ?? "");
  await page.getByRole("link", { name: /固定条件と変えた条件を比べる/u }).click();
  await expect(page).toHaveURL(/#\/compare\//u);
});

test("release dataとCoverage routeが同じdataset identityを読む", { tag: "@critical" }, async ({ page, baseURL }) => {
  const base = requiredBaseURL(baseURL);
  const [manifestResponse, releaseResponse] = await Promise.all([
    page.request.get(new URL("data/manifest.json", base).toString()),
    page.request.get(new URL("data/release.json", base).toString()),
  ]);
  expect(manifestResponse.ok()).toBe(true);
  expect(releaseResponse.ok()).toBe(true);
  const manifest = await manifestResponse.json() as { dataset_version: string };
  const release = await releaseResponse.json() as { dataset_version: string };
  expect(manifest.dataset_version).toBe(release.dataset_version);

  await gotoAtlasRoute(page, base, "/coverage");
  await expect(page.getByRole("heading", { level: 1, name: "Atlasの接続状況" })).toBeVisible();
  await expect(page.getByText(`Dataset ${release.dataset_version}`)).toBeVisible();
});

test("Diagnoseの推薦カードから対応するMap nodeへ移動する", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/");
  await page.getByRole("link", { name: "条件から診断を始める" }).click();
  const firstQuestion = page.getByRole("group", {
    name: "x（決めるもの）はどの種類ですか？",
  });
  await firstQuestion.getByRole("button", { name: /^0-1/u }).click();

  const firstChoiceBand = page.locator("section").filter({
    has: page.getByRole("heading", { level: 2, name: "第一候補" }),
  });
  const recommendation = firstChoiceBand.locator("article").filter({
    has: page.getByRole("button", { name: "地図で確認" }),
  }).first();
  const methodName = await recommendation.getByRole("heading", { level: 3 }).textContent();
  await recommendation.getByRole("button", { name: "地図で確認" }).click();

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
  await expect(page.getByRole("heading", { level: 2, name: "時間以上（hours or more）" })).toBeVisible();
  await expect(page.locator('[role="treeitem"][aria-selected="true"]')).toContainText("時間以上");

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

  await expect(page.getByRole("heading", { level: 1, name: "観測データから非線形モデルのパラメータを推定する" })).toBeVisible();
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
  await expect(page.getByRole("link", { name: "勾配降下法" })).toBeVisible();
});

test("制約付きsliceで可行性とunconstrained failureを比較できる", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/theater/learning/SCENARIO_CONSTRAINED_DISK");

  await expect(page.getByRole("heading", { level: 1, name: "実行可能領域と制約を無視した失敗を比べる" })).toBeVisible();
  await expect(page.getByText("実行可能領域 (feasible_region) · 1.0.0")).toBeVisible();
  await expect(page.getByRole("img", { name: /円の内側が実行可能領域/u })).toBeVisible();
  await expect(page.getByText("制約が有効", { exact: true })).toBeVisible();

  const slider = page.getByRole("slider", { name: /現在の反復/u });
  await slider.press("Home");
  await expect(page.getByText("実行不可能", { exact: true })).toBeVisible();
  await expect(page.getByText("Traceを進めて確認します。")).toBeVisible();
});

test("Pareto sliceでpreferenceに応じた点をkeyboardで選べる", { tag: "@critical" }, async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/theater/learning/SCENARIO_BIOBJECTIVE_QUADRATIC");

  await expect(page.getByRole("heading", { level: 1, name: "単一bestではなくPareto frontを読む" })).toBeVisible();
  await expect(page.getByText("パレート前線 (pareto_front) · 1.1.0")).toBeVisible();
  await expect(page.getByText(/単一の最良解ではありません/u)).toBeVisible();
  await expect(page.getByTestId("triobjective-scatter")).toBeVisible();
  await expect(page.getByRole("img", { name: "3目的のparallel coordinates表示" })).toBeVisible();

  const selectedF1 = page.locator("dl div").filter({ hasText: "選択した f₁" }).locator("dd");
  const before = await selectedF1.textContent();
  await page.getByRole("slider", { name: /f₁の重み/u }).press("ArrowRight");
  await expect(selectedF1).not.toHaveText(before ?? "");
  const camera = page.getByRole("slider", { name: "3目的表示のカメラ方位" });
  await camera.press("ArrowRight");
  await expect(page.locator(".triobjective-lens output")).toHaveText("320°");
});

test("制約付きCaseをprimary Theater、failure、CompareからCaseへ完走できる", { tag: "@critical" }, async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/gallery/constrained-design");

  await expect(page.getByRole("heading", { level: 1, name: "強度制約を守りながら軽量設計を探す" })).toBeVisible();
  await expect(page.getByRole("link", { name: /固定条件と変えた条件を比べる/u })).toBeVisible();
  const theaterJourney = page.getByRole("link", { name: /固定した1回の実行を追う/u });
  await theaterJourney.focus();
  await expect(theaterJourney).toBeFocused();
  await theaterJourney.press("Enter");
  await expect(page).toHaveURL(/#\/theater\/learning\/SCENARIO_CONSTRAINED_DISK_FEASIBLE_PATH\?state=/u);
  await expect(page.getByRole("heading", { level: 1, name: "制約を満たす経路で目的を改善する" })).toBeVisible();
  await expect(page.getByText("M_SLSQP", { exact: true }).first()).toBeVisible();

  await page.getByRole("link", { name: /別のシナリオ: 実行可能領域と制約を無視した失敗/u }).click();
  await expect(page).toHaveURL(/#\/theater\/learning\/SCENARIO_CONSTRAINED_DISK\?state=/u);
  await expect(page.getByRole("heading", { level: 1, name: "実行可能領域と制約を無視した失敗を比べる" })).toBeVisible();

  await page.getByRole("link", { name: "Compareへ: COMPARE_CONSTRAINED_FAILURE" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "制約を守るrunと無視するrunを比べる" })).toBeVisible();
  await page.getByRole("link", { name: /ケース: 強度制約/u }).click();
  await expect(page).toHaveURL(/#\/gallery\/constrained-design\?state=/u);
  await expect(page.getByRole("heading", { level: 1, name: "強度制約を守りながら軽量設計を探す" })).toBeVisible();
});

test("離散配分Caseを最適性証明、予算停止、CompareからCaseへ完走できる", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/gallery/budget-allocation");

  await expect(
    page.getByRole("heading", { level: 1, name: "限られた予算を施策へ配分する" }),
  ).toBeVisible();
  await expect(page.getByText("Journey complete")).toBeVisible();

  const primaryTheater = page.getByRole("link", { name: /固定した1回の実行を追う/u });
  await expect(primaryTheater).toBeVisible();
  await page.waitForLoadState("networkidle");
  await primaryTheater.click();

  await expect(page).toHaveURL(
    /#\/theater\/search-tree\/binary-knapsack-bnb-complete\?state=/u,
  );
  await expect(
    page.getByRole("heading", { level: 1, name: "0-1 knapsack: 最適性証明" }),
  ).toBeVisible();

  const alternate = page.getByRole("link", {
    name: "別のシナリオ: 0-1 knapsack: node予算で停止",
  });
  await expect(alternate).toBeVisible();
  await page.waitForLoadState("networkidle");
  await alternate.click();

  await expect(page).toHaveURL(
    /#\/theater\/search-tree\/binary-knapsack-bnb-budget\?state=/u,
  );
  await expect(
    page.getByRole("heading", { level: 1, name: "0-1 knapsack: node予算で停止" }),
  ).toBeVisible();

  const compare = page.getByRole("link", {
    name: "Compareへ: COMPARE_KNAPSACK_BNB_BUDGET",
  });
  await expect(compare).toBeVisible();
  await page.waitForLoadState("networkidle");
  await compare.click();

  await expect(page).toHaveURL(
    /#\/compare\/COMPARE_KNAPSACK_BNB_BUDGET\?state=/u,
  );
  await expect(
    page.getByRole("heading", {
      level: 1,
      name: "探索完了とnode予算停止を同じ上限で比べる",
    }),
  ).toBeVisible();

  await page.getByLabel("評価回数位置").fill("9");

  const proof = page.getByLabel("9 node以内で証明完了の同期指標");
  await expect(metricValue(proof, "Terminal status")).toHaveText("最適性証明済み");
  await expect(metricValue(proof, "最良値")).toHaveText("15");
  await expect(metricValue(proof, "Global bound")).toHaveText("15.00");
  await expect(metricValue(proof, "Absolute gap")).toHaveText("0.00");
  await expect(page.getByText("最適性を証明 · evaluation 9")).toBeVisible();

  const stopped = page.getByLabel("4 nodeで予算停止の同期指標");
  await expect(metricValue(stopped, "Terminal status")).toHaveText("予算停止・未証明");
  await expect(metricValue(stopped, "最良値")).toHaveText("13");
  await expect(metricValue(stopped, "Global bound")).toHaveText("15.00");
  await expect(metricValue(stopped, "Absolute gap")).toHaveText("2.00");
  await expect(page.getByText("node予算に到達 · evaluation 4")).toBeVisible();

  const caseLink = page.getByRole("link", {
    name: "ケース: 限られた予算を施策へ配分する",
  });
  await expect(caseLink).toBeVisible();
  await page.waitForLoadState("networkidle");
  await caseLink.click();

  await expect(page).toHaveURL(/#\/gallery\/budget-allocation\?state=/u);
  await expect(
    page.getByRole("heading", { level: 1, name: "限られた予算を施策へ配分する" }),
  ).toBeVisible();
});

test("parameter推定CaseをTRF、初期値感度、条件比較からCaseへ完走できる", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/gallery/EC013");

  await page.getByRole("link", { name: /固定した1回の実行を追う/u }).click();
  await expect(page).toHaveURL(/#\/traces\/exponential-fit-trf\?state=/u);
  await expect(page.getByRole("heading", { level: 1, name: "共通診断probe · TRF適用条件" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 2, name: /指標の履歴/u })).toBeVisible();
  await expect(page.getByRole("img", { name: /残差.*評価回数ごとに比較/u })).toBeVisible();

  await page.getByRole("link", { name: /別のシナリオ: 共通診断probe · 悪い初期値/u }).click();
  await expect(page).toHaveURL(/#\/traces\/exponential-fit-trf-poor-init\?state=/u);
  await expect(page.getByRole("heading", { level: 1, name: "共通診断probe · 悪い初期値" })).toBeVisible();
  await page.getByRole("link", { name: "Compareへ: COMPARE_EXPONENTIAL_FIT_SOLVER_CONDITIONS" }).click();

  await expect(page.getByRole("heading", { level: 1, name: "非線形fitでsolver条件を比べる" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 2, name: /指標の履歴/u })).toBeVisible();
  await expect(page.getByLabel("指標の履歴").getByRole("img", { name: /評価回数ごとに比較/u })).toHaveCount(3);
  await expect(page.getByText(/3本とも1つのsolver非依存診断probe/u)).toBeVisible();
  await page.getByRole("link", { name: /ケース: 観測データから非線形モデルのパラメータを推定する/u }).click();
  await expect(page).toHaveURL(/#\/gallery\/EC013\?state=/u);
  await expect(page.getByRole("heading", { level: 1, name: "観測データから非線形モデルのパラメータを推定する" })).toBeVisible();
});

test("高価なblack-box CaseをBO Theater、noise感度、CompareからCaseへ完走できる", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/gallery/hyperparameter-search");

  await expect(page.getByRole("heading", { level: 1, name: "高価な実験の設定を探す" })).toBeVisible();
  await expect(page.getByText("Journey complete")).toBeVisible();
  await page.getByRole("link", { name: /固定した1回の実行を追う/u }).click();
  await expect(page).toHaveURL(/#\/theater\/bayesian-optimization\/SCENARIO_BO_1D_EXPLORE_NOISELESS\?state=/u);
  await expect(page.getByRole("heading", { level: 1, name: "ベイズ最適化の1回の実行" })).toBeVisible();
  await expect(page.getByText(/ケース: 高価な実験の設定を探す/u)).toBeVisible();

  await page.getByRole("link", { name: /別のシナリオ: 高価な1次元black-box: explore \/ small_noise/u }).click();
  await expect(page).toHaveURL(/#\/theater\/bayesian-optimization\/SCENARIO_BO_1D_EXPLORE_SMALL_NOISE\?state=/u);
  await expect(page.getByLabel("観測ノイズ")).toHaveValue("small_noise");
  await page.getByRole("link", { name: "Compareへ: COMPARE_BO_ACQUISITION_NOISE_BASELINE" }).click();

  await expect(page.getByRole("heading", { level: 1, name: "acquisition・noise・random baselineを同じbudgetで読む" })).toBeVisible();
  const evaluation = page.getByRole("slider", { name: "BO比較のevaluation" });
  await evaluation.press("End");
  await expect(page.getByText("Oracle evaluations: 10/10")).toBeVisible();
  await expect(page.getByText(/一般的な優劣や因果効果は推論できません/u)).toBeVisible();
  const primaryTheater = page.getByRole("link", { name: "Theater: 高価な1次元black-box: explore / noiseless" });
  await expect(primaryTheater).toHaveAttribute(
    "href",
    /#\/theater\/bayesian-optimization\/SCENARIO_BO_1D_EXPLORE_NOISELESS\?state=/u,
  );
  await primaryTheater.click();
  await expect(page).toHaveURL(/#\/theater\/bayesian-optimization\/SCENARIO_BO_1D_EXPLORE_NOISELESS\?state=/u);
  await page.getByRole("link", { name: "Caseへ戻る" }).click();
  await expect(page).toHaveURL(/#\/gallery\/hyperparameter-search\?state=/u);
});
