import { expect, test } from "./fixtures/test";
import { expectNoHighImpactViolations } from "./helpers/accessibility";
import { expectNoHorizontalOverflow, gotoAtlasRoute } from "./helpers/navigation";

for (const [id, article] of [
  ["topology", "topology-optimization"],
  ["arm", "concept.constrained-nlp"],
  ["drone", "concept.optimal-control"],
]) {
  test(`${id}を記事の説明の中で再生し、大きく見て記事へ戻れる`, async ({ page, baseURL }, testInfo) => {
    if (!baseURL) throw new Error("baseURL required");
    await gotoAtlasRoute(page, baseURL, `/learn/${article}`);
    await page.locator(".physical-article-mount").scrollIntoViewIfNeeded();
    const figure = page.locator(".physical-embedded");
    await expect(figure.locator("canvas")).toBeVisible();
    const articleUrl = page.url();
    await page.screenshot({ path: `output/playwright/physical-${id}-article.png` });
    if (id !== "topology") await figure.getByRole("button", { name: "最後まで進める" }).click();
    await figure.getByRole("button", { name: "1つ戻る" }).click();
    await expect(figure.getByRole("button", { name: "最後まで進める" })).toBeEnabled();
    await expectNoHighImpactViolations(page, testInfo, `physical-${id}-article`);
    await page.setViewportSize({ width: 375, height: 812 });
    await expectNoHorizontalOverflow(page);
    await figure.screenshot({ path: `output/playwright/physical-${id}-article-mobile.png` });
    await figure.getByRole("link", { name: "大きく見る →" }).click();
    await expect(page).toHaveURL(new RegExp(`#/theater/physical/${id}$`));
    await page.getByRole("button", { name: "← 記事に戻る" }).click();
    await expect(page).toHaveURL(`${articleUrl}?figure=${id}`);
    await expect(page.locator(".physical-viewport")).toBeFocused();
    const restored = await figure.boundingBox();
    expect(restored?.y).toBeGreaterThanOrEqual(-1);
    expect(restored?.y).toBeLessThan(180);
  });
}

for (const id of ["topology", "arm", "drone"]) {
  test(`${id}の3D計算結果を再生し、条件と視点を変えられる`, async ({ page, baseURL }, testInfo) => {
    if (!baseURL) throw new Error("baseURL required");
    await gotoAtlasRoute(page, baseURL, `/theater/physical/${id}`);
    await expect(page.getByRole("combobox", { name: "計算した条件" })).toBeVisible();
    await expect(page.locator(".physical-viewport canvas")).toBeVisible();
    await page.screenshot({ path: `output/playwright/physical-${id}-initial.png`, fullPage: true });
    if (id === "topology") await expect(page.getByRole("button", { name: "最後まで進める" })).toBeDisabled();
    else await page.getByRole("button", { name: "最後まで進める" }).click();
    await page.getByRole("button", { name: "1つ戻る" }).click();
    await expect(page.getByRole("button", { name: "最後まで進める" })).toBeEnabled();
    await page.getByRole("button", { name: "横から", exact: true }).click();
    await page.locator(".physical-viewport").focus();
    await page.locator(".physical-viewport").press("ArrowRight");
    await page.getByRole("combobox", { name: "計算した条件" }).selectOption("0");
    await page.getByRole("button", { name: "最後まで進める" }).click();
    if (id === "topology") {
      await page.getByRole("checkbox", { name: "最終形の変形を重ねる" }).check();
      await expect(page.getByText("表示用の変位倍率")).toBeVisible();
    } else await page.getByRole("checkbox", { name: "もう一方の条件の軌道を重ねる" }).check();
    await expectNoHighImpactViolations(page, testInfo, `physical-${id}`);
    await page.screenshot({ path: `output/playwright/physical-${id}.png`, fullPage: true });
    await page.setViewportSize({ width: 375, height: 812 });
    await expectNoHorizontalOverflow(page);
    await page.screenshot({ path: `output/playwright/physical-${id}-mobile.png`, fullPage: true });
  });
}

test("3Dが使えなくても計算結果と2D図が残り、reduced motionで自動再生しない", async ({ page, baseURL }) => {
  if (!baseURL) throw new Error("baseURL required");
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (...args) {
      if (String(args[0]).includes("webgl")) return null;
      return Reflect.apply(original, this, args);
    } as typeof original;
  });
  await gotoAtlasRoute(page, baseURL, "/theater/physical/drone");
  await expect(page.getByText(/3D表示を利用できません/u)).toBeVisible();
  await expect(page.getByRole("img", { name: "3Dと同じ状態の2D射影" })).toBeVisible();
  await expect(page.getByRole("button", { name: "▶ 再生" })).toBeDisabled();
  await page.getByRole("combobox", { name: "計算した条件" }).selectOption("1");
  await expect(page.getByRole("button", { name: "最後まで進める" })).toBeDisabled();
  await expect(page.getByRole("table")).toBeVisible();
});
