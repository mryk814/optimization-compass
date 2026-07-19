import { test, expect } from "./fixtures/test";
import { gotoAtlasRoute } from "./helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

test("all current renderer families consume the shared educational metadata", async ({
  page,
  baseURL,
}, testInfo) => {
  const base = requiredBaseURL(baseURL);

  await gotoAtlasRoute(page, base, "/theater/nelder-mead");
  const scenarioContext = page.getByRole("region", { name: "ケースとシナリオの関連情報" });
  await expect(scenarioContext.getByRole("heading", { name: "このrunで見るもの" })).toBeVisible();
  await expect(scenarioContext.getByText("単体の幾何操作と候補の受理判断を結び付けて読む")).toBeVisible();
  await expect(scenarioContext.getByText(/単体の頂点 \/ 受理操作/u)).toBeVisible();

  await gotoAtlasRoute(page, base, "/compare/COMPARE_GRADIENT_DIVERGENCE");
  const comparisonConditions = page.getByRole("region", { name: "比較条件" });
  await expect(comparisonConditions.getByRole("heading", { name: "この比較で確かめること" })).toBeVisible();
  await expect(comparisonConditions.getByText(/目的と初期点を固定し、学習率だけを攻める/u)).toBeVisible();
  await expect(comparisonConditions.getByText(/更新後に目的値と振幅が増大する/u)).toBeVisible();

  await gotoAtlasRoute(page, base, "/theater/search-tree/binary-knapsack-bnb-budget");
  const searchTreeContext = page.getByRole("region", { name: "ケースとシナリオの関連情報" });
  await expect(searchTreeContext.getByText("上界とincumbentが探索範囲を狭める過程を読む")).toBeVisible();
  await expect(searchTreeContext.getByText(/探索node \/ 大域上界 \/ 暫定解/u)).toBeVisible();

  await gotoAtlasRoute(page, base, "/theater/bayesian-optimization");
  const boContext = page.getByRole("region", { name: "ケースとシナリオの関連情報" });
  await expect(boContext.getByText("観測からsurrogateとacquisitionを更新して次の評価点を選ぶ流れを読む")).toBeVisible();
  await expect(boContext.getByText(/観測点 \/ surrogate平均 \/ 予測不確実性 \/ Expected Improvement \/ 次候補/u)).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("bo-lesson-panel.png"), fullPage: true });
});

test("optimal control historyはstate/controlと制約診断を同じ履歴で読める", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/traces/optimal-control-ec020-history");
  await expect(page.getByRole("heading", { level: 1, name: "Direct collocation · state/control診断" })).toBeVisible();
  await expect(page.getByText("state norm", { exact: false }).first()).toBeVisible();
  await expect(page.getByText("dynamics defect", { exact: false }).first()).toBeVisible();
  await expect(page.getByText("path violation", { exact: false }).first()).toBeVisible();
  await expect(page.getByText(/連続時間の可行性/u).first()).toBeVisible();
});

test("Nelder-Mead guided story applies the authored frame, speed, and focus cue", async ({
  page,
  baseURL,
}) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/theater/nelder-mead");

  await page.getByRole("button", { name: /最初の候補と受理判断/u }).click();

  await expect(page).toHaveURL(/frame=2&speed=0\.5/u);
  await expect(page.getByText(/worstを重心の反対側へ動かし/u)).toBeVisible();
  await expect(page.getByLabel("再生速度")).toHaveValue("0.5");
  await expect(page.getByLabel("フレーム位置")).toHaveValue("2");
  await expect(page.getByTestId("nelder-mead-explanatory-plot")).toHaveAttribute(
    "data-guided-focus",
    "accepted_operation",
  );
});

test("guided stories drive four renderer families from one contract", async ({ page, baseURL }) => {
  const base = requiredBaseURL(baseURL);

  await gotoAtlasRoute(page, base, "/traces/gradient_descent-quadratic");
  await page.getByRole("button", { name: /最初のupdateを追う/u }).click();
  await expect(page).toHaveURL(/frame=1&speed=0\.5/u);
  await expect(page.locator(".trace-snapshot")).toHaveAttribute("data-guided-focus", "update_vector");

  await gotoAtlasRoute(page, base, "/theater/search-tree/binary-knapsack-bnb-complete");
  await page.getByRole("button", { name: /最初のbranchとbound更新/u }).click();
  await expect(page).toHaveURL(/frame=1&speed=0\.5/u);
  await expect(page.locator(".search-tree-renderer")).toHaveAttribute("data-guided-focus", "search_nodes");

  await gotoAtlasRoute(page, base, "/theater/bayesian-optimization");
  await page.getByRole("button", { name: /最初のsurrogate更新と次点選択/u }).click();
  await expect(page.getByLabel("評価位置")).toHaveValue("1");
  await expect(page.locator(".bo-layout")).toHaveAttribute("data-guided-focus", "selected_candidate");
  await expect(page.getByText(/フレーム 2\/8 · 0\.5倍/u)).toBeVisible();
});

test("derived thumbnail and static formats are discoverable from the scenario", async ({
  page,
  baseURL,
}) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/traces/nelder-mead-quadratic");

  const video = page.getByLabel(/各frameの頂点順位/u);
  await expect(video).toBeVisible();
  await expect(video).toHaveAttribute("poster", /media\/scenario-nm-quadratic\/thumbnail\.png/u);
  await expect(video.locator("source")).toHaveAttribute("src", /media\/scenario-nm-quadratic\/animation\.webm/u);
  await expect(video.locator("track")).toHaveAttribute("src", /media\/scenario-nm-quadratic\/captions\.vtt/u);
  await expect(page.getByRole("link", { name: "PNGを開く" })).toHaveAttribute(
    "href",
    /media\/scenario-nm-quadratic\/static\.png/u,
  );
  await expect(page.getByRole("link", { name: "SVGを開く" })).toHaveAttribute(
    "href",
    /media\/scenario-nm-quadratic\/static\.svg/u,
  );
  await expect(page.getByRole("link", { name: "GIFを開く" })).toHaveAttribute("href", /animation\.gif/u);
  await expect(page.getByRole("link", { name: "WebMを開く" })).toHaveAttribute("href", /animation\.webm/u);
  await expect(page.getByRole("link", { name: "文字起こしを開く" })).toHaveAttribute("href", /transcript\.txt/u);
});

test("Nelder-Mead and Gradient share their trace frame with the linked 3D surface", async ({
  page,
  baseURL,
}) => {
  const base = requiredBaseURL(baseURL);
  await gotoAtlasRoute(page, base, "/traces/nelder-mead-quadratic");

  const nelderMeadSurface = page.getByTestId("linked-objective-surface");
  await expect(nelderMeadSurface).toHaveAttribute("data-current-frame", "0");
  await nelderMeadSurface.getByRole("button", { name: "フレーム 2へ移動" }).click();
  await expect(page).toHaveURL(/frame=1/u);
  await expect(nelderMeadSurface).toHaveAttribute("data-current-frame", "1");
  await expect(page.getByText(/直交投影 \(orthographic\)/u)).toBeVisible();

  await gotoAtlasRoute(page, base, "/traces/gradient_descent-quadratic");
  const gradientSurface = page.getByTestId("linked-objective-surface");
  await expect(gradientSurface).toBeVisible();
  await gradientSurface.getByRole("button", { name: "フレーム 2へ移動" }).click();
  await expect(page.getByLabel("フレーム位置")).toHaveValue("1");

  await page.setViewportSize({ width: 375, height: 812 });
  const widths = await page.evaluate(() => ({
    client: document.documentElement.clientWidth,
    scroll: document.documentElement.scrollWidth,
  }));
  expect(widths.scroll).toBeLessThanOrEqual(widths.client + 1);
});
