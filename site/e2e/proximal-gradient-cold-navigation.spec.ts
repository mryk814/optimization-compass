import { expect, test } from "./fixtures/test";
import type { Page } from "@playwright/test";
import { writeFile } from "node:fs/promises";

const selector = '[data-explorable-id="proximal-gradient-threshold"]';

async function openFromIndex(page: Page, baseURL: string) {
  await page.goto(baseURL);
  await page.getByRole("link", { name: "手法", exact: true }).click();
  await expect(page.getByRole("heading", { name: "手法・概念を学ぶ", exact: true })).toBeVisible();
  await page.getByRole("button", { name: /^手法 \d+件$/u }).click();
  await page.getByRole("searchbox", { name: "教材を検索" }).fill("近接勾配");
  const article = page.locator(".content-card-main").filter({ has: page.getByRole("heading", { name: "近接勾配法", exact: true }) });
  await expect(article).toHaveCount(1);
  // Follow the generated canonical link, rather than assigning the article hash.
  await article.click();
}

async function expectFirstStep(page: Page) {
  const region = page.locator(selector);
  await expect(region.locator(".ex-frame")).toHaveCount(1);
  await expect(region.getByRole("slider", { name: "操作", exact: true })).toHaveValue("0");
  const flow = region.locator('.prox-step-panel svg[role="img"]');
  await expect(flow).toHaveAccessibleName(/現在の係数0.000.*中間点0.750.*縮めた後は0.550/u);
  await expect(region.locator(".explorable-fallback, .ex-loading")).toHaveCount(0);
}

for (const width of [1280, 375]) {
  test(`cold home → index → proximal-gradient mounts controls at ${width}px`, { tag: "@critical" }, async ({ page, baseURL }, testInfo) => {
    await page.setViewportSize({ width, height: 900 });
    await page.emulateMedia({ reducedMotion: "reduce" });
    const scripts: Array<{ url: string; status: number }> = [];
    page.on("response", response => {
      if (response.request().resourceType() === "script") {
        scripts.push({ url: response.url(), status: response.status() });
      }
    });
    try {
      await openFromIndex(page, baseURL!);
      await expectFirstStep(page);
      const region = page.locator(selector);
      await region.scrollIntoViewIfNeeded();
      await region.screenshot({ path: testInfo.outputPath("cold-first-step.png") });
      await region.getByRole("slider", { name: "正則化の強さ λ", exact: true }).fill("3");
      await expect(region.locator('[data-prox-stage="proximal"]')).toContainText("0.000");
      await expect(region.locator(".ex-verdict")).toContainText("ちょうど0");
      await page.goBack();
      await expect(page.getByRole("heading", { name: "手法・概念を学ぶ", exact: true })).toBeVisible();
      await page.goForward();
      await expectFirstStep(page);
      await page.reload();
      await expectFirstStep(page);
      expect(scripts.some(response => /\/ProximalThreshold-[^/]+\.js$/u.test(response.url))).toBe(true);
      expect(scripts.filter(response => response.status >= 400)).toEqual([]);
    } finally {
      const path = testInfo.outputPath("script-responses.json");
      await writeFile(path, JSON.stringify(scripts, null, 2), "utf8");
      await testInfo.attach("script-responses", { path, contentType: "application/json" });
    }
  });
}

test("cold article shows loading while its figure chunk is pending, then mounts without reload", { tag: "@critical" }, async ({ page, baseURL }) => {
  let releaseChunk!: () => void;
  const pending = new Promise<void>(resolve => { releaseChunk = resolve; });
  await page.route(/\/ProximalThreshold-[^/]+\.js$/u, async route => {
    await pending;
    await route.continue();
  });
  try {
    await openFromIndex(page, baseURL!);
    const region = page.locator(selector);
    await expect(region.locator(".ex-loading")).toHaveText("図を読み込んでいます…");
    await expect(region.getByRole("slider")).toHaveCount(0);
    await expect(region.locator(".explorable-fallback")).toHaveCount(0);
    releaseChunk();
    await expectFirstStep(page);
  } finally {
    releaseChunk();
  }
});
