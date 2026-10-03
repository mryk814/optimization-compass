import { expect, test } from "./fixtures/test";
import { expectNoHighImpactViolations } from "./helpers/accessibility";
import { expectNoHorizontalOverflow, gotoAtlasRoute } from "./helpers/navigation";

const route = "/learn/coordinate-descent";
const selector = '[data-explorable-id="coordinate-descent-walk"]';

for (const width of [1280, 375, 320]) {
  test(`座標降下法の主図・操作・式が${width}pxで近接し、文字が読める`, async ({ page, baseURL }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.emulateMedia({ reducedMotion: "reduce" });
    await gotoAtlasRoute(page, baseURL!, route);
    const fig = page.locator(selector);
    await expect(fig.locator(".ex-frame")).toBeVisible();
    await expectNoHorizontalOverflow(page);
    await fig.getByRole("button", { name: "最初から", exact: true }).click();
    await fig.getByRole("button", { name: "1つ進む", exact: true }).click();
    await expect(fig.locator(".cd-diagnostics")).toContainText("(−9.00, 3.00)");
    await expect(fig.getByRole("region", { name: "次の一手" })).toContainText("次はyだけ");
    const boxes = await fig.evaluate(node => {
      const box = (css: string) => node.querySelector(css)!.getBoundingClientRect().toJSON();
      return { main: box(".cd-walk"), player: box(".ex-player"), support: box(".cd-detail"),
        font: Number.parseFloat(getComputedStyle(node.querySelector("svg text")!).fontSize) };
    });
    expect(boxes.player.top - boxes.main.bottom).toBeLessThan(20);
    expect(boxes.font).toBeGreaterThanOrEqual(13);
    if (width === 1280) expect(boxes.main.width).toBeGreaterThan(boxes.support.width * 1.5);
    else expect(boxes.support.top).toBeGreaterThan(boxes.player.bottom);
    const toc = page.getByRole("navigation", { name: "この教材の目次" });
    await expect(toc.locator("details")).not.toHaveAttribute("open");
    await toc.locator("summary").click();
    await toc.getByRole("button", { name: "小さな例", exact: true }).click();
    await expect(page.getByRole("heading", { name: "小さな例", exact: true })).toBeFocused();
    await expectNoHorizontalOverflow(page);
  });
}

for (const width of [1280, 375]) {
  test(`@critical ${width}pxで一手・連続更新・表示切替・最適点・reset・axeを検収する`, async ({ page, baseURL }, testInfo) => {
    await page.setViewportSize({ width, height: 900 });
    await page.emulateMedia({ reducedMotion: "reduce" });
    await gotoAtlasRoute(page, baseURL!, route);
    const fig = page.locator(selector);
    await expect(fig.locator(".ex-verdict")).toContainText("24回の更新（12掃引）");
    await fig.getByRole("button", { name: "最初から", exact: true }).click();
    await expect(fig.locator(".cd-diagnostics")).toContainText("569.000");
    await fig.getByRole("button", { name: "1つ進む", exact: true }).click();
    await expect(fig.locator(".cd-diagnostics")).toContainText("400.000");
    await expect(fig.locator(".cd-diagnostics")).toContainText("160.000");
    await expect(fig.locator(".cd-diagnostics")).toContainText("偏微分 x: 0 · y: 160.000");
    const before = await fig.locator(".cd-diagnostics").innerText();
    const head = await fig.locator(".cd-walk .ex-head").getAttribute("cx");
    await fig.getByRole("radio", { name: "目的値の推移", exact: true }).check();
    expect(await fig.locator(".cd-diagnostics").innerText()).toBe(before);
    expect(await fig.locator(".cd-walk .ex-head").getAttribute("cx")).toBe(head);
    await expect(fig.locator(".ex-scrub output")).toHaveText("1 / 24回");
    // Same-turn repeated clicks exercise the timeline ref rather than a stale render closure.
    await fig.getByRole("button", { name: "1つ進む", exact: true }).evaluate(button => {
      for (let i = 0; i < 5; i += 1) (button as HTMLButtonElement).click();
    });
    await expect(fig.locator(".ex-scrub output")).toHaveText("6 / 24回");
    await expect(fig.locator(".cd-diagnostics")).toContainText("(0.60, −1.96)");
    await expect(fig.locator(".cd-diagnostics")).toContainText("0.128");
    await fig.getByRole("radio", { name: "軸に沿う", exact: true }).check();
    await expect(fig.locator(".ex-verdict")).toContainText("2回の更新（1掃引）");
    await fig.getByRole("radio", { name: "細く斜め", exact: true }).check();
    await expect(fig.locator(".ex-verdict")).toContainText("まだ収束していません");
    await expect(fig.locator(".ex-scrub output")).toHaveText("200 / 200回");
    await fig.locator(".cd-start summary").click();
    await fig.getByRole("radio", { name: "最小点 (1, −2)", exact: true }).check();
    await expect(fig.locator(".ex-verdict")).toContainText("更新せずに停止");
    await expect(fig.locator(".ex-scrub output")).toHaveText("0 / 0回");
    await expect(fig.getByRole("button", { name: "1つ進む", exact: true })).toBeDisabled();
    await expect(fig.locator(".cd-diagnostics")).toContainText("(1.00, −2.00)");
    await expect(fig.locator(".ex-equation")).toHaveCount(0);
    await fig.getByRole("button", { name: "谷と初期点を戻す" }).click();
    await expect(fig.getByRole("radio", { name: "本文の谷", exact: true })).toBeChecked();
    await expect(fig.getByRole("radio", { name: "一手の断面", exact: true })).toBeChecked();
    await expect(fig.locator(".ex-verdict")).toContainText("24回の更新（12掃引）");
    await expect(fig.locator(".ex-scrub output")).toHaveText("24 / 24回");
    await fig.getByRole("button", { name: "谷と初期点を戻す" }).click();
    await expect(fig.locator(".ex-scrub output")).toHaveText("24 / 24回");
    await expectNoHighImpactViolations(page, testInfo, `coordinate-descent-${width}`);
  });
}

test("谷の向き・曲率をキーボードで変え、200%文字拡大とreduced motionを保持する", async ({ page, baseURL }) => {
  await page.setViewportSize({ width: 640, height: 900 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await gotoAtlasRoute(page, baseURL!, route);
  const fig = page.locator(selector);
  await fig.locator(".cd-adjustments summary").click();
  await fig.getByRole("slider", { name: "谷の向き θ" }).fill("45");
  await fig.getByRole("slider", { name: "谷の細長さ κ（曲率比）" }).fill("100");
  await expect(fig.getByRole("radio", { name: "調整した谷" })).toBeChecked();
  await fig.getByRole("slider", { name: "谷の向き θ" }).press("Home");
  await expect(fig.getByRole("slider", { name: "谷の向き θ" })).toHaveValue("-90");
  await expect(fig.locator(".ex-verdict")).toContainText("2回の更新（1掃引）");
  await expect(fig.getByRole("button", { name: /再生/u })).toBeDisabled();
  await fig.getByRole("button", { name: "最初から", exact: true }).click();
  await fig.getByRole("button", { name: "1つ進む", exact: true }).click();
  await page.evaluate(() => { document.documentElement.style.fontSize = "200%"; });
  await expectNoHorizontalOverflow(page);
  for (const term of await fig.locator(".cd-substitution .live-math").all()) {
    const bounds = (await term.boundingBox())!;
    const equation = (await fig.locator(".ex-equation").boundingBox())!;
    expect(bounds.x + bounds.width).toBeLessThanOrEqual(equation.x + equation.width);
  }
});

test("通常の再生中でも表示切替は現在点を保ち、resetは初回状態へ戻す", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, baseURL!, route);
  const fig = page.locator(selector);
  await expect(fig.locator(".ex-scrub output")).toHaveText("24 / 24回");
  await fig.getByRole("radio", { name: "細く斜め", exact: true }).check();
  await expect(fig.getByRole("button", { name: /一時停止/u })).toBeVisible();
  await fig.getByRole("button", { name: /一時停止/u }).click();
  const position = await fig.locator(".ex-scrub input").inputValue();
  const current = await fig.locator(".cd-diagnostics").innerText();
  await fig.getByRole("radio", { name: "目的値の推移", exact: true }).check();
  expect(await fig.locator(".ex-scrub input").inputValue()).toBe(position);
  expect(await fig.locator(".cd-diagnostics").innerText()).toBe(current);
  await fig.getByRole("button", { name: "谷と初期点を戻す" }).click();
  await expect(fig.locator(".ex-scrub output")).toHaveText("24 / 24回");
  await expect(fig.getByRole("button", { name: /再生/u })).toHaveAttribute("aria-pressed", "false");
});

test.describe("スマホ幅のタッチ代替", () => {
  test.use({ hasTouch: true, viewport: { width: 375, height: 812 } });
  test("谷の選択・一手・表示切替をタッチで操作できる", async ({ page, baseURL }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await gotoAtlasRoute(page, baseURL!, route);
    const fig = page.locator(selector);
    await fig.getByRole("radio", { name: "軸に沿う", exact: true }).tap();
    await expect(fig.locator(".ex-verdict")).toContainText("2回の更新（1掃引）");
    await fig.getByRole("button", { name: "最初から", exact: true }).tap();
    await fig.getByRole("button", { name: "1つ進む", exact: true }).tap();
    await expect(fig.locator(".cd-diagnostics")).toContainText("(1.00, 3.00)");
    await fig.getByRole("radio", { name: "目的値の推移", exact: true }).tap();
    await expect(fig.locator(".cd-diagnostics")).toContainText("500.000");
  });
});
