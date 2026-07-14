import { test, expect } from "./fixtures/test";
import { gotoAtlasRoute } from "./helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

const unknownRoutes = [
  "/learn/missing-content",
  "/methods/M_MISSING",
  "/gallery/missing-case",
  "/compare/missing-comparison",
  "/definitely-not-a-route",
];

for (const route of unknownRoutes) {
  test(`${route} は共通Not Foundを表示する`, async ({ page, baseURL }) => {
    await gotoAtlasRoute(page, requiredBaseURL(baseURL), route);
    await expect(page.getByRole("heading", { level: 1, name: "ページが見つかりません" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Atlasへ戻る" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Mapを見る" })).toBeVisible();
  });
}

test("壊れたassetを画面上のrecoverable errorとして表示する", async ({
  page,
  baseURL,
  browserLog,
}) => {
  browserLog.allowError(/content\.json/u);
  await page.route(/\/optimization-compass\/data\/content\.json$/u, (route) => route.abort("failed"));
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/learn");
  await expect(page.getByRole("alert")).toContainText("Failed to fetch");
  await expect(page.getByRole("heading", { level: 1, name: "ページが見つかりません" })).toHaveCount(0);
});
