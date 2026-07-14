import { expect, type Page } from "@playwright/test";

export const pagesBasePath = "/optimization-compass/";

export function atlasUrl(baseURL: string, route: string): string {
  const url = new URL(baseURL);
  const normalized = route.startsWith("/") ? route : `/${route}`;
  url.hash = normalized;
  return url.toString();
}

export async function gotoAtlasRoute(page: Page, baseURL: string, route: string) {
  await page.goto(atlasUrl(baseURL, route));
  expect(new URL(page.url()).pathname).toBe(pagesBasePath);
}

export async function expectNoHorizontalOverflow(page: Page) {
  const dimensions = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth + 1);
}
