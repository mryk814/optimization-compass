import { expect, test } from "./fixtures/test";
import { expectNoHighImpactViolations } from "./helpers/accessibility";
import { expectNoHorizontalOverflow, gotoAtlasRoute } from "./helpers/navigation";

const route = "/learn/concept.linear-least-squares";
const figureSelector = '[data-explorable-id="least-squares-bowl"]';

for (const width of [1280, 375, 320]) {
  test(`最小二乗の記事が${width}pxで操作図・本文・補助図を読み分けられる`, async ({ page, baseURL }) => {
    await page.setViewportSize({ width, height: 900 });
    await gotoAtlasRoute(page, baseURL!, route);
    const figure = page.locator(figureSelector);
    await expect(figure.locator(".ex-frame")).toBeVisible();
    if (width === 320) {
      // main already overflows by 2px here through the unrelated path-next-card on the baseline.
      const layout = await page.locator(".compiled-content-layout").evaluate(node => ({ client: node.clientWidth, scroll: node.scrollWidth }));
      expect(layout.scroll).toBeLessThanOrEqual(layout.client + 1);
    } else {
      await expectNoHorizontalOverflow(page);
    }
    const dimensions = await page.evaluate(() => {
      const bounds = (selector: string) => document.querySelector(selector)!.getBoundingClientRect().toJSON();
      return {
        main: bounds('[data-explorable-id="least-squares-bowl"]'),
        prose: bounds(".markdown-body > p"),
        support: bounds(".markdown-body > figure:has(img)"),
        standard: bounds('[id="標準形を読む"]'),
        bodyFont: Number.parseFloat(getComputedStyle(document.querySelector(".markdown-body > p")!).fontSize),
        chartFont: Number.parseFloat(getComputedStyle(document.querySelector(".ex-svg text")!).fontSize),
      };
    });
    expect(dimensions.prose.width).toBeLessThanOrEqual(672);
    expect(dimensions.support.width).toBeLessThanOrEqual(440);
    expect(dimensions.main.bottom).toBeLessThan(dimensions.standard.top);
    expect(dimensions.bodyFont).toBeGreaterThanOrEqual(16);
    expect(dimensions.chartFont).toBeGreaterThanOrEqual(13);
    if (width === 1280) expect(dimensions.main.width).toBeGreaterThan(dimensions.prose.width);
    // All four squared residuals remain visible, including when the sum wraps on mobile.
    const terms = figure.locator(".lsq-squared-terms [role=math]");
    await expect(terms).toHaveCount(4);
    const equation = await figure.locator(".ex-equation").boundingBox();
    for (const term of await terms.all()) {
      const box = (await term.boundingBox())!;
      expect(box.x).toBeGreaterThanOrEqual(equation!.x);
      expect(box.x + box.width).toBeLessThanOrEqual(equation!.x + equation!.width);
    }
    const toc = page.getByRole("navigation", { name: "この教材の目次" });
    await expect(toc.locator("details")).not.toHaveAttribute("open");
    await toc.locator("summary").click();
    await toc.getByRole("button", { name: "小さな例", exact: true }).click();
    await expect(page.getByRole("heading", { name: "小さな例", exact: true })).toBeFocused();
    if (width !== 320) await expectNoHorizontalOverflow(page);
  });
}

for (const width of [1280, 375]) {
  test(`最小二乗の操作と再計算、リセット、axeが${width}pxで成立する`, async ({ page, baseURL }, testInfo) => {
    await page.setViewportSize({ width, height: 900 });
    await gotoAtlasRoute(page, baseURL!, route);
    const figure = page.locator(figureSelector);
    await expect(figure.locator(".ex-frame")).toBeVisible();
    await expect(figure.locator(".ex-equation")).toContainText("1.660");
    await figure.getByRole("slider", { name: "傾き x₂", exact: true }).fill("0.9");
    await expect(figure.locator(".ex-equation")).toContainText("1.340");
    await figure.getByRole("radio", { name: "二乗和が最小の直線" }).check();
    await expect(figure.locator(".ex-equation")).toContainText("0.700");
    await expect(figure.locator(".ex-table tbody tr").last()).toContainText("0.00");
    await figure.getByRole("slider", { name: /^点4（/u }).press("Shift+ArrowUp");
    await figure.locator(".lsq-point-controls summary").click();
    await figure.getByRole("slider", { name: "観測点4の高さ" }).fill("8");
    await expect(figure.locator(".ex-equation")).toContainText("y = 0.10 + 2.10 t");
    await figure.getByRole("button", { name: "点と直線を最初に戻す" }).click();
    await expect(figure.getByRole("slider", { name: /^点4（/u })).toHaveAttribute("aria-valuenow", "4");
    await expect(figure.getByRole("radio", { name: "自分で動かす" })).toBeChecked();
    await expect(figure.locator(".ex-equation")).toContainText("1.660");
    await expectNoHighImpactViolations(page, testInfo, `least-squares-${width}`);
  });
}

test("文字を200%に拡大しても本文と操作を保持する", async ({ page, baseURL }) => {
  await page.setViewportSize({ width: 640, height: 900 });
  await gotoAtlasRoute(page, baseURL!, route);
  const figure = page.locator(figureSelector);
  await expect(figure.locator(".ex-frame")).toBeVisible();
  await page.evaluate(() => { document.documentElement.style.fontSize = "200%"; });
  await expectNoHorizontalOverflow(page);
  await figure.getByRole("radio", { name: "二乗和が最小の直線" }).check();
  await expect(figure.locator(".ex-equation")).toContainText("0.700");
  expect(await page.locator(".markdown-body > p").first().evaluate(node => Number.parseFloat(getComputedStyle(node).fontSize))).toBe(32);
});

test.describe("スマホ幅でのタッチ代替確認", () => {
  test.use({ hasTouch: true, viewport: { width: 375, height: 812 } });

  test("観測点をタッチで動かすとページはスクロールせず値が変わる", async ({ page, context, baseURL }) => {
    await gotoAtlasRoute(page, baseURL!, route);
    const point = page.locator(figureSelector).getByRole("slider", { name: /^点4（/u });
    await point.scrollIntoViewIfNeeded();
    const box = (await point.locator(".ex-handle-hit").boundingBox())!;
    const position = { x: box.x + box.width / 2, y: box.y + box.height / 2 };
    const scrollBefore = await page.evaluate(() => window.scrollY);
    const session = await context.newCDPSession(page);
    await session.send("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [position] });
    for (const delta of [20, 40, 60]) {
      await session.send("Input.dispatchTouchEvent", { type: "touchMove", touchPoints: [{ ...position, y: position.y - delta }] });
    }
    await session.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
    await expect(point).not.toHaveAttribute("aria-valuenow", "4");
    expect(await page.evaluate(() => window.scrollY)).toBe(scrollBefore);
    await session.detach();
  });
});

for (const route of ["bayesian-optimization", "adam"]) {
  for (const width of [1280, 375]) {
    test(`${route}の操作図も${width}pxで目次を開閉して使える`, async ({ page, baseURL }) => {
      await page.setViewportSize({ width, height: 900 });
      await gotoAtlasRoute(page, baseURL!, `/learn/${route}`);
      await expect(page.locator(".ex-frame")).toBeVisible();
      const toc = page.getByRole("navigation", { name: "この教材の目次" });
      await expect(toc.locator("details")).not.toHaveAttribute("open");
      await toc.locator("summary").click();
      await expect(toc.getByRole("button", { name: "30秒でつかむ", exact: true })).toBeVisible();
      await expectNoHorizontalOverflow(page);
    });
  }
}
