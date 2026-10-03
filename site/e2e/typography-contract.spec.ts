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
        || style.clip !== "auto"
        || style.clipPath !== "none"
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
    metadata: ".content-card-main > span",
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
    primary: ".coverage-heading p:not(.eyebrow)",
    metadata: ".coverage-pill:visible",
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

// Linear least squares is the reference article. Every other kind of article renders its body
// with exactly the same typography and reading column (docs/content-reading-principles.md §11),
// so a page-specific stylesheet cannot quietly restyle one kind of article.
const referenceArticle = "/learn/concept.linear-least-squares";
const articleKinds = [
  { kind: "method with explorable", route: "/learn/adam" },
  { kind: "method without explorable", route: "/learn/bfgs" },
  { kind: "method family", route: "/learn/family.trust-region" },
  { kind: "formulation without explorable", route: "/learn/concept.nonlinear-least-squares" },
  { kind: "concept", route: "/learn/concept.time-discretization" },
] as const;
const articleRoles = {
  h2: ":scope > h2",
  h3: ":scope > h3",
  paragraph: ":scope > p",
  list: ":scope > ul",
  listItem: ":scope > ul > li",
  link: ":scope > p a",
  inlineCode: ":scope > p code",
  codeBlock: ":scope pre",
  tableHeader: ":scope > table th, :scope > div > table th",
  tableCell: ":scope > table td, :scope > div > table td",
  figureCaption: ":scope > figure > figcaption",
} as const;
const articleProperties = [
  "fontSize", "fontWeight", "lineHeight", "color", "fontFamily", "marginTop", "marginBottom",
  "paddingLeft", "borderLeftWidth", "borderLeftColor", "backgroundColor", "borderRadius",
] as const;

async function articleSignature(page: Page) {
  await expect(page.locator(".markdown-body > p").first()).toBeVisible();
  await expect(page.locator(".content-toc")).toBeVisible();
  return page.locator(".markdown-body").first().evaluate(
    (body, { roles, properties }) => {
      const result: Record<string, string | null> = {};
      for (const [role, selector] of Object.entries(roles)) {
        const element = body.querySelector<HTMLElement>(selector);
        if (!element) {
          result[role] = null;
          continue;
        }
        const style = getComputedStyle(element);
        result[role] = properties.map((property) => `${property}=${style[property]}`).join(" ");
      }
      const paragraph = body.querySelector<HTMLElement>(":scope > p")!.getBoundingClientRect();
      result.readingColumn = `left=${Math.round(paragraph.left)} width=${Math.round(paragraph.width)}`;
      result.toc = body.parentElement?.querySelector(".content-toc details") ? "folded above" : "other";
      return result;
    },
    { roles: articleRoles, properties: articleProperties },
  );
}

for (const width of [1280, 375]) {
  test(`${width}pxで全種類の記事本文が線形最小二乗と同じ見た目になる`, async ({ page, baseURL }) => {
    await page.setViewportSize({ width, height: 900 });
    await gotoAtlasRoute(page, requiredBaseURL(baseURL), referenceArticle);
    const reference = await articleSignature(page);
    expect(reference.toc).toBe("folded above");
    for (const article of articleKinds) {
      await gotoAtlasRoute(page, requiredBaseURL(baseURL), article.route);
      const signature = await articleSignature(page);
      for (const [role, value] of Object.entries(signature)) {
        if (value === null || reference[role] === null) continue;
        expect(value, `${article.kind} (${article.route}) ${role}`).toBe(reference[role]);
      }
    }
  });
}
