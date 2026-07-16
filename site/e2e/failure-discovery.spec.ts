import { expect, test } from "./fixtures/test";
import { gotoAtlasRoute } from "./helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

test("失敗の兆候を検索・絞り込みしcanonical手法へ進める", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/failures");

  await expect(page.getByRole("heading", { level: 1, name: "失敗の兆候から探す" })).toBeVisible();
  await expect(page.getByText("何が起きているかから、確認項目・対処候補・影響する手法・根拠へ進みます。")).toBeVisible();
  await expect(page.getByRole("heading", { level: 2, name: "noiseが微分を支配" })).toBeVisible();

  const search = page.getByRole("searchbox", { name: "失敗の兆候を検索" });
  await search.fill("悪条件");
  await expect(page.getByRole("heading", { level: 2, name: "悪条件" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 2, name: "noiseが微分を支配" })).toHaveCount(0);

  await search.clear();
  await page.getByLabel("重大度").selectOption("warning");
  await expect(page.getByRole("heading", { level: 2, name: "過度に厳しいtolerance" })).toBeVisible();
  await expect(page.getByText("1件を表示")).toBeVisible();

  await page.getByLabel("重大度").selectOption("all");
  await page.getByLabel("対象範囲").selectOption("implementation_specific");
  await expect(page.getByRole("heading", { level: 2, name: "status code誤読" })).toBeVisible();

  await page.getByLabel("対象範囲").selectOption("all");
  const failureCard = page.locator("article").filter({
    has: page.getByRole("heading", { level: 2, name: "noiseが微分を支配" }),
  });
  await failureCard.getByText("影響する手法・可視化・根拠").click();
  const methodLink = failureCard.getByRole("link", { name: "BFGS法" });
  await expect(methodLink).toHaveAttribute("href", "#/methods/M_BFGS");
  await methodLink.click();
  await expect(page).toHaveURL(/#\/methods\/M_BFGS/u);
  await expect(page.getByRole("heading", { level: 1, name: "BFGS法" })).toBeVisible();
});
