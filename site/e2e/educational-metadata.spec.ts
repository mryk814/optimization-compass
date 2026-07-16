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
  await expect(page.getByText("見るポイント / Reading cues")).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "単体の幾何操作と候補の受理判断を結び付けて読む" }),
  ).toBeVisible();
  await expect(page.getByText(/単体の頂点 · 受理操作/u)).toBeVisible();

  await gotoAtlasRoute(page, base, "/compare/COMPARE_GRADIENT_DIVERGENCE");
  await expect(page.getByText(/解く誤解:.*学習率/u)).toBeVisible();
  await expect(page.getByText(/更新後に目的値と振幅が増大する/u)).toBeVisible();

  await gotoAtlasRoute(page, base, "/theater/search-tree/binary-knapsack-bnb-budget");
  await expect(page.getByText(/incumbentは最適性が証明されている/u)).toBeVisible();
  await expect(page.getByText(/node予算到達時に未探索node/u)).toBeVisible();

  await gotoAtlasRoute(page, base, "/theater/bayesian-optimization");
  await expect(
    page.getByRole("heading", {
      name: "観測からsurrogateとacquisitionを更新して次の評価点を選ぶ流れを読む",
    }),
  ).toBeVisible();
  await expect(page.getByText(/optimizerが参照しない真の目的関数/u)).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("bo-lesson-panel.png"), fullPage: true });
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
  await expect(page.getByText(/Frame 2\/8 · 0\.5×/u)).toBeVisible();
});
