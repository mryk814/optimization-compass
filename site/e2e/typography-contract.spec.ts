import { expect, test, type Locator, type Page } from "@playwright/test";

import { gotoAtlasRoute } from "./helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

async function expectTypeRole(
  locator: Locator,
  minimumFontSize: number,
  minimumLineHeightRatio: number,
): Promise<void> {
  await expect(locator.first()).toBeVisible();
  const metrics = await locator.first().evaluate((element) => {
    const style = getComputedStyle(element);
    return {
      fontSize: Number.parseFloat(style.fontSize),
      lineHeight: Number.parseFloat(style.lineHeight),
    };
  });
  expect(metrics.fontSize).toBeGreaterThanOrEqual(minimumFontSize);
  expect(metrics.lineHeight / metrics.fontSize).toBeGreaterThanOrEqual(minimumLineHeightRatio);
}

async function expectNoPageOverflow(page: Page): Promise<void> {
  const dimensions = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth + 1);
}

async function expectNoTinyInterfaceText(page: Page): Promise<void> {
  const violations = await page.locator("body").evaluate((body) => {
    const results: string[] = [];
    for (const element of body.querySelectorAll<HTMLElement>("*")) {
      if (element.closest("svg") || element.matches("script, style")) continue;
      const hasDirectText = [...element.childNodes].some(
        (node) => node.nodeType === Node.TEXT_NODE && Boolean(node.textContent?.trim()),
      );
      if (!hasDirectText) continue;
      const bounds = element.getBoundingClientRect();
      const style = getComputedStyle(element);
      if (
        bounds.width === 0
        || bounds.height === 0
        || style.display === "none"
        || style.visibility === "hidden"
      ) continue;
      const fontSize = Number.parseFloat(style.fontSize);
      if (fontSize < 14) {
        const label = element.textContent?.trim().replace(/\s+/gu, " ").slice(0, 60) ?? "";
        results.push(`${element.tagName.toLowerCase()}.${element.className || "-"}: ${fontSize}px (${label})`);
      }
    }
    return results;
  });
  expect(violations, `Visible non-SVG text below 14px:\n${violations.join("\n")}`).toEqual([]);
}

const surfaces = [
  {
    route: "/",
    primary: ".home-case-question",
    metadata: ".home-case-journey small",
    control: ".home-case-disclosure summary",
  },
  {
    route: "/learn",
    primary: ".atlas-page-header p:not(.eyebrow)",
    metadata: ".content-card > span",
    control: ".content-search",
  },
  {
    route: "/map",
    primary: ".map-page-header p:not(.eyebrow)",
    metadata: ".map-tree",
    control: ".map-toolbar button",
  },
  {
    route: "/gallery/hyperparameter-search",
    primary: ".gallery-question-panel p:not(.eyebrow)",
    metadata: ".gallery-context-grid article > span",
    control: ".gallery-disclosure summary",
  },
  {
    route: "/compare/COMPARE_CONSTRAINED_FAILURE",
    primary: ".comparison-question",
    metadata: ".comparison-member-strip strong",
    control: ".comparison-policy-details summary",
  },
  {
    route: "/theater",
    primary: ".theater-first-action p:not(.eyebrow)",
    metadata: ".theater-card > span",
    control: ".theater-catalog-filters label",
  },
  {
    route: "/coverage",
    primary: ".coverage-language-note",
    metadata: ".coverage-pill",
    control: ".coverage-filters label",
  },
  {
    route: "/traces/so3-riemannian-alignment",
    primary: ".metric-history > header p",
    metadata: ".scenario-context-grid dt",
    control: ".playback-actions button",
  },
] as const;

test(
  "主要surfaceが共通の本文16px・metadata14px契約を守る",
  { tag: "@critical" },
  async ({ page, baseURL }) => {
    for (const surface of surfaces) {
      await gotoAtlasRoute(page, requiredBaseURL(baseURL), surface.route);
      await expectTypeRole(page.locator(surface.primary), 16, 1.6);
      await expectTypeRole(page.locator(surface.metadata), 14, 1.45);
      await expectTypeRole(page.locator(surface.control), 16, 1.45);
      await expectNoTinyInterfaceText(page);
    }

    await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/theater/bayesian-optimization");
    await expectTypeRole(page.locator(".bo-figure text"), 13, 1);
  },
);

test(
  "375pxで主要surfaceが小文字化せずreflowする",
  { tag: "@critical" },
  async ({ page, baseURL }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    for (const surface of surfaces) {
      await gotoAtlasRoute(page, requiredBaseURL(baseURL), surface.route);
      await expectTypeRole(page.locator(surface.primary), 16, 1.6);
      await expectTypeRole(page.locator(surface.metadata), 14, 1.45);
      await expectTypeRole(page.locator(surface.control), 16, 1.45);
      await expectNoTinyInterfaceText(page);
      await expectNoPageOverflow(page);
    }
  },
);
