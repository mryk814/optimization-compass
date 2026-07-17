import { test, expect } from "./fixtures/test";
import { gotoAtlasRoute } from "./helpers/navigation";
import { expectGradientComparisonSvg, expectNelderMeadSvg } from "./helpers/visualization";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

test("Nelder–Mead controlsがplay、pause、step、reloadを保持する", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/theater/nelder-mead");
  const controls = page.getByRole("region", { name: "アルゴリズム再生コントロール" });
  const iteration = controls.getByLabel("iteration");
  await expect(controls).toBeVisible();
  await expect(page.getByLabel("目的関数", { exact: true })).toHaveValue("OBJECTIVE_QUADRATIC_2D");
  await expect(page.getByRole("combobox", { name: "初期simplex", exact: true })).toHaveValue("standard");
  const shapeLegend = page.locator(".shape-legend");
  await expect(shapeLegend.getByText("Best", { exact: true })).toBeVisible();
  await expect(shapeLegend.getByText("Worst", { exact: true })).toBeVisible();
  await controls.getByRole("button", { name: "1フレーム進む" }).click();
  await controls.getByRole("button", { name: "1フレーム進む" }).click();
  await expect(page.locator(".nm-candidate")).toBeVisible();
  await expectNelderMeadSvg(page.getByTestId("nelder-mead-explanatory-plot"));
  const initialIteration = Number(await iteration.textContent());

  await controls.getByRole("button", { name: "再生", exact: true }).click();
  await expect(controls.getByRole("button", { name: "一時停止", exact: true })).toBeVisible();
  await expect.poll(async () => Number(await iteration.textContent()), { timeout: 3_000 })
    .toBeGreaterThan(initialIteration);
  await controls.getByRole("button", { name: "一時停止", exact: true }).click();

  const pausedIteration = Number(await iteration.textContent());
  await controls.getByRole("button", { name: "1フレーム進む" }).click();
  await expect.poll(async () => Number(await iteration.textContent())).toBeGreaterThanOrEqual(pausedIteration);
  await controls.getByRole("button", { name: "1フレーム戻る" }).click();
  await controls.getByLabel("再生速度").selectOption("2");
  await controls.getByRole("button", { name: "逆再生にする" }).click();
  const frameBeforeReload = await controls.getByText(/Frame \d+\//u).textContent();

  await page.reload();
  const reloadedControls = page.getByRole("region", { name: "アルゴリズム再生コントロール" });
  await expect(reloadedControls.getByLabel("再生速度")).toHaveValue("2");
  await expect(reloadedControls.getByRole("button", { name: "順再生にする" })).toBeVisible();
  await expect(reloadedControls.getByRole("button", { name: "再生", exact: true })).toBeVisible();
  await expect(reloadedControls.getByText(/Frame \d+\//u)).toHaveText(frameBeforeReload ?? "");
});

test("gradient comparisonが同じevaluationで同期しreloadする", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/compare/gradient-quadratic");
  const evaluation = page.getByLabel("評価回数位置");
  await expect(evaluation).toBeVisible();
  await expect(page.getByRole("combobox", { name: "比較preset", exact: true })).toHaveValue(
    "COMPARE_GRADIENT_FAMILY",
  );
  await expect(page.getByRole("heading", { level: 2, name: "勾配降下法" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 2, name: "モメンタム法" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 2, name: "Adam" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 2, name: "目的値 vs oracle evaluations" })).toBeVisible();
  await evaluation.fill("7");

  const eventLines = page.locator(".comparison-event");
  const memberCount = await eventLines.count();
  expect(memberCount).toBeGreaterThan(1);
  for (let index = 0; index < memberCount; index += 1) {
    await expect(eventLines.nth(index)).toContainText("evaluation 7");
  }
  await expectGradientComparisonSvg(page, 7);

  await page.reload();
  await expect(page.getByLabel("評価回数位置")).toHaveValue("7");
  for (let index = 0; index < memberCount; index += 1) {
    await expect(page.locator(".comparison-event").nth(index)).toContainText("evaluation 7");
  }
});

test("旧canonical comparison IDのdeep linkが現行の比較へ解決する", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/compare/COMPARE_FIRST_ORDER_ROSENBROCK");

  await expect(page.getByRole("heading", { level: 1, name: "細長い谷で一次法を比べる" })).toBeVisible();
  await expect(page.getByRole("combobox", { name: "比較preset", exact: true })).toHaveValue(
    "COMPARE_GRADIENT_FAMILY",
  );
  await expect(page.getByRole("heading", { level: 2, name: /同じ初期点と評価回数/u })).toBeVisible();
});

test("制約failure comparisonでfixed・changed・feasibilityを読める", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/compare/COMPARE_CONSTRAINED_FAILURE");

  await expect(page.getByRole("heading", { level: 1, name: "制約を守るrunと無視するrunを比べる" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 3, name: "同じもの / Fixed" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 3, name: "違うもの / Changed" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 3, name: "見る指標 / Metrics" })).toBeVisible();
  await expect(page.getByRole("img", { name: /円の内側が実行可能領域/u })).toBeVisible();
  await expect(page.getByText("制約違反", { exact: true }).first()).toBeVisible();
  await expect(page.getByRole("link", { name: /Case: 強度制約/u })).toBeVisible();
  await expect(page.getByRole("link", { name: /Theater: 実行可能領域/u })).toBeVisible();
});

test("Pareto result comparisonでpreferenceだけを変えられる", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/compare/COMPARE_PARETO_PREFERENCE");

  await expect(page.getByRole("heading", { level: 1, name: "Pareto front上でpreferenceを変える" })).toBeVisible();
  await expect(page.getByText("preference weight", { exact: false }).first()).toBeVisible();
  await expect(page.getByRole("slider", { name: /f₁のweight/u })).toBeVisible();
  await expect(page.getByLabel("Pareto coverage集計")).toContainText("Sampled81");
  await expect(page.getByLabel("f₂優先weightの選択結果")).toContainText("Decision(1.6, 1.6)");
  await expect(page.getByLabel("均衡weightの選択結果")).toContainText("f₁2");
  await expect(page.getByLabel("f₁優先weightの選択結果")).toContainText("f₂5.12");
  await expect(page.getByText("ranking=forbidden", { exact: false })).toHaveCount(0);
  await expect(page.getByText("forbidden", { exact: true })).toBeVisible();
});

test("Learn検索からmethod detailとrelated visualizationへ進む", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/learn");
  await page.getByRole("textbox", { name: "検索" }).fill("Nelder");
  await page.getByRole("link", { name: /Nelder–Mead単体法/u }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Nelder–Mead単体法" })).toBeVisible();
  await page.getByRole("link", { name: "Nelder–Meadの幾何操作" }).first().click();
  await expect(page).toHaveURL(/#\/traces\/nelder-mead-quadratic$/u);
  await expect(page.getByRole("heading", { level: 1, name: "Nelder–Meadの幾何操作" })).toBeVisible();
  await expect(page.getByRole("region", { name: "アルゴリズム再生コントロール" })).toBeVisible();
});

test("追加教材を検索しcanonical methodと実行例を読める", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/learn");
  await page.getByRole("textbox", { name: "検索" }).fill("CP-SAT");
  await page.getByRole("link", { name: /CP-SATと制約プログラミング/u }).click();

  await expect(page.getByRole("heading", { level: 1, name: "CP-SAT" })).toBeVisible();
  await expect(page.getByRole("region", { name: "教材" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 2, name: "現実の問いをmodelへ移す" })).toBeVisible();
  await expect(page.locator("pre code")).toContainText("cp_model.CpModel");
  await expect(page.getByRole("link", { name: "Branch-and-Cut" })).toHaveAttribute(
    "href",
    "#/learn/branch-and-cut",
  );
});
