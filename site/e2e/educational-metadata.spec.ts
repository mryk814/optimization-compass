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
  await expect(page.getByRole("link", { name: "Transcriptを開く" })).toHaveAttribute("href", /transcript\.txt/u);
});

test("Nelder-Mead and Gradient share their trace frame with the linked 3D surface", async ({
  page,
  baseURL,
}) => {
  const base = requiredBaseURL(baseURL);
  await gotoAtlasRoute(page, base, "/traces/nelder-mead-quadratic");

  const nelderMeadSurface = page.getByTestId("linked-objective-surface");
  await expect(nelderMeadSurface).toHaveAttribute("data-current-frame", "0");
  await nelderMeadSurface.getByRole("button", { name: "frame 2へ移動" }).click();
  await expect(page).toHaveURL(/frame=1/u);
  await expect(nelderMeadSurface).toHaveAttribute("data-current-frame", "1");
  await expect(page.getByText(/Projection: orthographic/u)).toBeVisible();

  await gotoAtlasRoute(page, base, "/traces/gradient_descent-quadratic");
  const gradientSurface = page.getByTestId("linked-objective-surface");
  await expect(gradientSurface).toBeVisible();
  await gradientSurface.getByRole("button", { name: "frame 2へ移動" }).click();
  await expect(page.getByLabel("フレーム位置")).toHaveValue("1");

  await page.setViewportSize({ width: 375, height: 812 });
  const widths = await page.evaluate(() => ({
    client: document.documentElement.clientWidth,
    scroll: document.documentElement.scrollWidth,
  }));
  expect(widths.scroll).toBeLessThanOrEqual(widths.client + 1);
});
