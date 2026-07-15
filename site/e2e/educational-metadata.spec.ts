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
