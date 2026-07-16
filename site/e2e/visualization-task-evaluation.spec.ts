import { expect, test } from "./fixtures/test";
import { expectNoHorizontalOverflow, gotoAtlasRoute } from "./helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

test("continuous 3D selection keeps the 2D contour and playback frame linked", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/traces/nelder-mead-quadratic");

  await expect(page.getByTestId("nelder-mead-explanatory-plot")).toBeVisible();
  const surface = page.getByTestId("linked-objective-surface");
  await expect(surface).toHaveAttribute("data-current-frame", "0");
  await surface.getByRole("button", { name: "frame 2へ移動" }).click();
  await expect(surface).toHaveAttribute("data-current-frame", "1");
  await expect(page.getByLabel("フレーム位置")).toHaveValue("1");
  await expect(page.getByText(/Projection: orthographic/u)).toBeVisible();
});

test("three-objective preference is shared with a precise mobile fallback", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/theater/learning/SCENARIO_BIOBJECTIVE_QUADRATIC");

  await expect(page.getByTestId("triobjective-scatter")).toBeVisible();
  await expect(page.getByRole("img", { name: "3目的のparallel coordinates fallback" })).toBeVisible();
  await expect(page.getByText(/9×9 gridから得たsampled teaching lens/u)).toBeVisible();
  const selected = page.locator(".triobjective-values dd");
  const before = await selected.allTextContents();
  await page.getByRole("slider", { name: /f₁のweight/u }).press("ArrowRight");
  await expect.poll(async () => selected.allTextContents()).not.toEqual(before);
  await page.getByRole("slider", { name: "3目的表示のカメラ方位" }).press("ArrowRight");
  await expect(page.locator(".triobjective-lens output")).toHaveText("320°");

  await page.setViewportSize({ width: 375, height: 812 });
  await expectNoHorizontalOverflow(page);
  await expect(page.getByTestId("triobjective-scatter")).toBeVisible();
  await expect(page.getByRole("img", { name: "3目的のparallel coordinates fallback" })).toBeVisible();
});

test("derived video retains captions, transcript, and independent formats", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/traces/nelder-mead-quadratic");

  const video = page.locator(".derived-media-preview video");
  await expect(video).toBeVisible();
  await expect(video).toHaveAttribute("poster", /thumbnail\.png/u);
  await expect(video.locator("source")).toHaveAttribute("src", /animation\.webm/u);
  await expect(video.locator("track")).toHaveAttribute("src", /captions\.vtt/u);
  await expect(page.getByRole("link", { name: "GIFを開く" })).toHaveAttribute("href", /animation\.gif/u);
  await expect(page.getByRole("link", { name: "Transcriptを開く" })).toHaveAttribute("href", /transcript\.txt/u);
});
