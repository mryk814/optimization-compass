import { test, expect } from "./fixtures/test";
import { gotoAtlasRoute } from "./helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

test("skip linkとprimary navigationをkeyboardだけで操作する", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/");
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "本文へ移動" })).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("#main-content")).toBeFocused();

  await page.reload();
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "本文へ移動" })).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Optimization Atlas ホーム" })).toBeFocused();
  await page.keyboard.press("Tab");
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "地図", exact: true })).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("tree", { name: "最適化問題の構造" })).toBeVisible();
});

test("Map treeを矢印、Enter、Spaceで操作する", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/map");
  const tree = page.getByRole("tree", { name: "最適化問題の構造" });
  const first = tree.getByRole("treeitem").first();
  await first.focus();
  await page.keyboard.press("ArrowRight");
  await expect(first).toHaveAttribute("aria-expanded", "true");
  await page.keyboard.press("ArrowDown");
  const focused = tree.locator('[role="treeitem"]:focus');
  await expect(focused).toHaveCount(1);
  await page.keyboard.press("Enter");
  await expect(focused).toHaveAttribute("aria-selected", "true");
  await page.keyboard.press(" ");
  await expect(focused).toHaveAttribute("aria-selected", "true");
  await page.keyboard.press("ArrowLeft");
  await expect(first).toBeFocused();
});

test("playback controlsをkeyboardでstepする", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/theater/nelder-mead");
  const controls = page.getByRole("region", { name: "アルゴリズム再生コントロール" });
  const forward = controls.getByRole("button", { name: "1フレーム進む" });
  const iteration = controls.getByLabel("iteration");
  const initial = await iteration.textContent();
  await forward.focus();
  await page.keyboard.press("Enter");
  await expect(iteration).not.toHaveText(initial ?? "");

  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.reload();
  const reducedControls = page.getByRole("region", { name: "アルゴリズム再生コントロール" });
  await expect(reducedControls.getByRole("button", { name: "自動再生オフ" })).toBeDisabled();
  await expect(reducedControls.getByText(/動きを減らす設定を検出しました/u)).toBeVisible();
  await reducedControls.getByRole("button", { name: "1フレーム進む" }).focus();
  await page.keyboard.press("Enter");
  await expect(reducedControls.getByLabel("iteration")).toBeVisible();
});
