import { test, expect } from "./fixtures/test";
import { gotoAtlasRoute } from "./helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

test("Nelder–Mead controlsがplay、pause、step、reloadを保持する", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/theater/nelder-mead");
  const controls = page.getByRole("region", { name: "アルゴリズム再生コントロール" });
  const iteration = controls.getByLabel("iteration");
  await expect(controls).toBeVisible();
  await expect(page.getByLabel("目的関数")).toHaveValue("OBJECTIVE_QUADRATIC_2D");
  await expect(page.getByRole("combobox", { name: "初期simplex", exact: true })).toHaveValue("standard");
  const shapeLegend = page.locator(".shape-legend");
  await expect(shapeLegend.getByText("Best", { exact: true })).toBeVisible();
  await expect(shapeLegend.getByText("Worst", { exact: true })).toBeVisible();
  await controls.getByRole("button", { name: "1フレーム進む" }).click();
  await controls.getByRole("button", { name: "1フレーム進む" }).click();
  await expect(page.locator(".nm-candidate")).toBeVisible();
  await expect(page.getByTestId("nelder-mead-explanatory-plot")).toHaveScreenshot(
    "nelder-mead-explanatory-plot.png",
    { animations: "disabled" },
  );
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
  await expect(page.locator(".comparison-grid")).toHaveScreenshot(
    "gradient-comparison-grid.png",
    { animations: "disabled" },
  );

  await page.reload();
  await expect(page.getByLabel("評価回数位置")).toHaveValue("7");
  for (let index = 0; index < memberCount; index += 1) {
    await expect(page.locator(".comparison-event").nth(index)).toContainText("evaluation 7");
  }
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
