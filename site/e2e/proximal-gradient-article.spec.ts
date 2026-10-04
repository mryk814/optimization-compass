import { expect, test } from "./fixtures/test";
import { expectNoHorizontalOverflow, gotoAtlasRoute } from "./helpers/navigation";

const selector = '[data-explorable-id="proximal-gradient-threshold"]';

test("近接勾配の二つの操作と0になる区間をキーボードでも確かめる", async ({ page, baseURL }, testInfo) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await gotoAtlasRoute(page, baseURL!, "/learn/proximal-gradient");
  const region = page.locator(selector);
  const position = region.getByRole("slider", { name: "操作", exact: true });
  await expect(position).toHaveValue("24");
  await position.fill("0");
  await expect(region.getByRole("math", { name: "中間点zは0.750", exact: true })).toBeVisible();
  await expect(region.getByRole("math", { name: /次の点.*0.550/u })).toBeVisible();
  await region.getByRole("button", { name: "1つ進む", exact: true }).click();
  await expect(position).toHaveValue("1");
  await expect(region.locator(".ex-player")).toContainText("0へ縮める");
  await region.getByRole("button", { name: "1つ進む", exact: true }).click();
  await expect(position).toHaveValue("2");
  await expect(region.getByRole("math", { name: /次の点.*0.963/u })).toBeVisible();

  const lambda = region.getByRole("slider", { name: "正則化の強さ λ", exact: true });
  await lambda.fill("3");
  await expect(region.locator(".ex-verdict")).toContainText("ちょうど0");
  await position.fill("0");
  await expect(region.getByRole("math", { name: "中間点zは0.750", exact: true })).toBeVisible();
  await expect(region.locator(".ex-readout")).toContainText("|Gη(xₖ)| = 0.000");
  const eta = region.getByRole("slider", { name: "歩幅 η", exact: true });
  await eta.focus();
  await eta.press("Home");
  await eta.press("ArrowRight");
  await expect(eta).toHaveValue("0.15");
  await expect(region.locator(".prox-equations")).toContainText("τ = ηλ = 0.450");
  await region.getByText("始点を変える", { exact: true }).click();
  const start = region.getByRole("slider", { name: "始点 x₀", exact: true });
  await start.focus();
  await start.press("Home");
  await start.press("ArrowRight");
  await expect(start).toHaveValue("-2.9");
  await expectNoHorizontalOverflow(page);
  await page.waitForLoadState("networkidle");
  await region.screenshot({ path: testInfo.outputPath("proximal-phone.png") });
});

test("近接勾配の図をデスクトップで再生し、本文の最初の一手を表示する", async ({ page, baseURL }, testInfo) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await gotoAtlasRoute(page, baseURL!, "/learn/proximal-gradient");
  const region = page.locator(selector);
  const position = region.getByRole("slider", { name: "操作", exact: true });
  await expect(position).toHaveValue("24");
  await region.getByRole("button", { name: "最初から", exact: true }).click();
  await expect(region.locator(".ex-play")).toHaveAttribute("aria-pressed", "true");
  await expect.poll(async () => Number(await position.inputValue())).toBeGreaterThan(0);
  await region.locator(".ex-play").click();
  await position.focus();
  await position.press("Home");
  await expect(position).toHaveValue("0");
  await expect(region.getByRole("math", { name: /次の点.*0.550/u })).toBeVisible();
  await expectNoHorizontalOverflow(page);
  const geometry = await region.locator(".ex-svg").evaluateAll(nodes => nodes.map(node => ({
    cssWidth: node.getBoundingClientRect().width,
    svgWidth: (node as SVGSVGElement).viewBox.baseVal.width,
    invalid: /NaN|Infinity/u.test(node.outerHTML),
  })));
  expect(geometry).toHaveLength(2);
  for (const panel of geometry) {
    expect(Math.abs(panel.cssWidth - panel.svgWidth)).toBeLessThanOrEqual(1);
    expect(panel.invalid).toBe(false);
  }
  await page.waitForLoadState("networkidle");
  await region.screenshot({ path: testInfo.outputPath("proximal-desktop-first-step.png") });
});

test("近接勾配と最小二乗の記事を往復しても図が重複せず停止理由が保たれる", async ({ page, baseURL }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await gotoAtlasRoute(page, baseURL!, "/learn/proximal-gradient");
  for (let visit = 0; visit < 5; visit += 1) {
    await expect(page.locator(`${selector} .ex-frame`)).toHaveCount(1);
    await expect(page.locator(selector).getByRole("slider", { name: "操作", exact: true })).toHaveValue("24");
    await page.waitForLoadState("networkidle");
    await page.evaluate(() => { window.location.hash = "/learn/concept.nonlinear-least-squares"; });
    const nonlinear = page.locator('[data-explorable-id="nonlinear-least-squares-landscape"]');
    await nonlinear.getByRole("slider", { name: /振幅 a/u }).fill("0");
    await nonlinear.getByRole("button", { name: "この点から下る", exact: true }).click();
    await expect(nonlinear.locator(".ex-readout")).toContainText("更新方向を安定して求められず");
    await expect(nonlinear.locator(".ex-readout")).not.toContainText("別の谷");
    await page.waitForLoadState("networkidle");
    await page.evaluate(() => { window.location.hash = "/learn/proximal-gradient"; });
  }
  await expect(page.locator(`${selector} .ex-frame`)).toHaveCount(1);
  await page.waitForLoadState("networkidle");
});
