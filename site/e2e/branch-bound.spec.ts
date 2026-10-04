import { expect, test } from "./fixtures/test";
import { expectNoHighImpactViolations } from "./helpers/accessibility";
import { expectNoHorizontalOverflow, gotoAtlasRoute } from "./helpers/navigation";

for (const width of [1280, 375, 390]) {
  for (const advanced of [false, true]) {
    test(`selected packing and comparison ${advanced ? "eight" : "four"} items ${width}px`, async ({ page, baseURL }, testInfo) => {
      await page.setViewportSize({ width, height: width > 640 ? 720 : 844 });
      await page.emulateMedia({ reducedMotion: "reduce" });
      await gotoAtlasRoute(page, baseURL!, "/learn/branch-and-bound");
      const region = page.locator('[data-explorable-id="branch-bound-proof"]');
      if (advanced) {
        await region.getByRole("radio", { name: "発展・8品" }).check();
        const catalogue = await region.locator(".bnb-items").evaluate(n => {
          const cells = [...n.children].map(e => e.getBoundingClientRect());
          return { rows: [...new Set(cells.map(r => r.top))].length, columns: [...new Set(cells.map(r => r.left))].length, minHeight: Math.min(...cells.map(r => r.height)), font: getComputedStyle(n.querySelector(".bnb-choice-metrics")!).fontSize };
        });
        expect(catalogue.rows).toBe(2);
        expect(catalogue.columns).toBe(4);
        expect(catalogue.minHeight).toBeGreaterThanOrEqual(44);
        expect(parseFloat(catalogue.font)).toBeGreaterThanOrEqual(16);
        await expectNoHorizontalOverflow(page);
        await region.locator(".bnb-items").evaluate(n => n.scrollIntoView({ block: "center" }));
        await page.screenshot({ path: `../output/playwright/bnb-v6-initial-eight-${width}.png` });
      }
      for (const name of advanced ? ["A", "B", "G"] : ["A", "B"]) await region.getByRole("checkbox", { name: new RegExp(`^${name} `) }).check();
      await region.getByRole("button", { name: "Aを入れる／入れないで比べる" }).click();
      const card = region.locator(".bnb-candidate");
      const graph = region.locator(".bnb-branch-focus");
      await expect(card).toHaveCount(1);
      await expect(region.locator(".bnb-candidate-summary")).toHaveCount(2);
      await expect(graph.locator(".bnb-bag")).toHaveCount(0);
      await graph.locator('[data-branch-id="1"]').focus();
      await page.keyboard.press("Enter");
      await expect(card).toBeFocused();
      await expect(card).toHaveAttribute("data-candidate-id", "1");
      await expect(graph.locator('[data-branch-id="1"]')).toHaveAttribute("aria-controls", "bnb-selected-candidate");
      await card.locator(".ex-action").evaluate(n => n.scrollIntoView({ block: "center" }));
      const scrollBefore = await page.evaluate(() => window.scrollY);
      await card.locator(".ex-action").click();
      await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(scrollBefore);
      await expect(card.locator(".ex-action")).toBeFocused();
      await region.locator('[data-summary-id="11"]').click();
      await card.locator(".ex-action").click();
      await region.locator('[data-summary-id="111"]').click();
      await expect(graph.locator(".bnb-branch-parent")).toContainText("A✓");
      if (advanced) {
        await expect(region.locator(".bnb-candidate-summary")).toHaveCount(4);
        await expect(card.locator(".bnb-bag-value")).toContainText("固定品の得点17");
        await expect(card.locator(".bnb-capacity")).toContainText("9 / 10");
        await expect(card.locator(".bnb-ceiling")).toContainText("18.5");
        await expect(region.locator(".bnb-proof")).toContainText("16 ≤ 最適値 ≤ 18.5");
      }
      const geometry = await region.evaluate((root) => {
        const detail = root.querySelector(".bnb-candidate")!;
        const bag = detail.querySelector(".bnb-bag")!.getBoundingClientRect();
        const action = detail.querySelector(".ex-action")!.getBoundingClientRect();
        const overview = root.querySelector(".bnb-overview")!.getBoundingClientRect();
        const targets = [...root.querySelectorAll("button, summary")].map(n => n.getBoundingClientRect().height).filter(Boolean);
        const texts = [...root.querySelectorAll(".bnb-candidate-summary,.bnb-capacity,.bnb-node-state")].map(n => parseFloat(getComputedStyle(n).fontSize));
        return { distance: action.bottom - bag.top, overview: overview.height, targets: Math.min(...targets), text: Math.min(...texts), animation: getComputedStyle(detail).animationName };
      });
      expect(geometry.distance).toBeLessThan(400);
      expect(geometry.targets).toBeGreaterThanOrEqual(44);
      expect(geometry.text).toBeGreaterThanOrEqual(16);
      expect(geometry.animation).toBe("none");
      await region.locator(".bnb-overview").evaluate(n => n.scrollIntoView({ block: "start" }));
      expect(await region.locator(".bnb-overview").evaluate(n => n.getBoundingClientRect().bottom)).toBeLessThanOrEqual(page.viewportSize()!.height);
      await page.screenshot({ path: `../output/playwright/bnb-v5-${advanced ? "eight" : "four"}-${width}.png` });
      await expectNoHorizontalOverflow(page);
      await expectNoHighImpactViolations(page, testInfo, `bnb-v5-${advanced}-${width}`);
      for (let i = 0; i < 80 && await card.count(); i++) {
        const summaries = region.locator(".bnb-candidate-summary");
        await summaries.nth(i % 2 ? (await summaries.count()) - 1 : 0).click();
        await card.locator(".ex-action").click();
        expect(await graph.locator(".bnb-branch-node").count()).toBeLessThanOrEqual(5);
      }
      const optimum = advanced ? 18 : 13;
      await expect(region.locator(".bnb-proof")).toContainText(`${optimum} ≤ 最適値 ≤ ${optimum}`);
      await region.getByRole("button", { name: "一手戻す" }).click();
      await expect(card).toHaveCount(1);
      await region.getByRole("radio", { name: advanced ? "入門・4品" : "発展・8品" }).check();
      await expect(card).toHaveCount(0);
      await expect(region.getByRole("checkbox")).toHaveCount(advanced ? 4 : 8);
      await expectNoHorizontalOverflow(page);
    });
  }
}

test("touch selects a compact comparison and operates its single packing", async ({ browser, baseURL }) => {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
  const page = await context.newPage();
  await gotoAtlasRoute(page, baseURL!, "/learn/branch-and-bound");
  const region = page.locator('[data-explorable-id="branch-bound-proof"]');
  await region.getByRole("checkbox", { name: /^A / }).tap();
  await region.getByRole("checkbox", { name: /^B / }).tap();
  await region.getByRole("button", { name: "Aを入れる／入れないで比べる" }).tap();
  await region.locator('[data-summary-id="0"]').tap();
  const card = region.locator(".bnb-candidate");
  await expect(card).toBeFocused();
  await card.locator(".ex-action").tap();
  await expect(region.locator('[data-branch-id="0"]')).toContainText("終了：記録以下");
  await expectNoHorizontalOverflow(page);
  await context.close();
});


test("an optimal initial packing receives proof without a fabricated record change", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, baseURL!, "/learn/branch-and-bound");
  const region = page.locator('[data-explorable-id="branch-bound-proof"]');
  await region.getByRole("radio", { name: "発展・8品" }).check();
  for (const name of ["A", "D", "E"]) await region.getByRole("checkbox", { name: new RegExp(`^${name} `) }).check();
  await region.getByRole("button", { name: "Aを入れる／入れないで比べる" }).click();
  await expect(region.locator(".bnb-proof")).toContainText("選んだ袋の18点は記録です");
  const card = region.locator(".bnb-candidate");
  for (let i = 0; i < 80 && await card.count(); i++) await card.locator(".ex-action").click();
  await expect(region.locator(".bnb-proof")).toContainText("18 ≤ 最適値 ≤ 18");
  await expect(region.locator(".bnb-proof")).toContainText("最初に選んだ袋が最適でした。");
});
