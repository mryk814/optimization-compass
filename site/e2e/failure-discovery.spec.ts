import { expect, test } from "./fixtures/test";
import { gotoAtlasRoute } from "./helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

test("失敗の兆候を検索・絞り込みしcanonical手法へ進める", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/failures");

  await expect(page.getByRole("heading", { level: 1, name: "失敗の兆候から探す" })).toBeVisible();
  await expect(page.getByText("観測された失敗profileと、特定のCaseで選ばない理由を区別したまま、確認項目・対処候補・根拠へ進みます。")).toBeVisible();
  await expect(page.getByRole("heading", { level: 2, name: "noiseが微分を支配" })).toBeVisible();

  const search = page.getByRole("searchbox", { name: "失敗の兆候を検索" });
  await search.fill("noise");
  await expect(page.getByRole("heading", { level: 2, name: "noiseが微分を支配" })).toBeVisible();

  await search.clear();
  await page.getByLabel("情報の種類").selectOption("case_exclusion");
  await expect(page.locator("article.failure-card").filter({ hasText: "Case固有の除外" }).first()).toBeVisible();
  await page.getByLabel("情報の種類").selectOption("all");
  const failureCard = page.locator("article").filter({
    has: page.getByRole("heading", { level: 2, name: "noiseが微分を支配" }),
  });
  await failureCard.getByText("適用範囲・関連情報・根拠").click();
  const methodLink = failureCard.getByRole("link", { name: "BFGS法" });
  await expect(methodLink).toHaveAttribute("href", "#/methods/M_BFGS");
  await methodLink.click();
  await expect(page).toHaveURL(/#\/methods\/M_BFGS/u);
  await expect(page.getByRole("heading", { level: 1, name: "BFGS法" })).toBeVisible();
});
