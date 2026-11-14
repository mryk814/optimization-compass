import { expect, test } from "../fixtures/test";
import { gotoAtlasRoute } from "../helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

test("勾配降下法の図で学習率を動かすと結果と安定限界が切り替わる", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/learn/method.gradient-descent");
  const region = page.locator('[data-explorable-id="gradient-descent-valley"]');
  await expect(region.getByText("見る問い")).toBeVisible();
  await region.getByRole("slider", { name: /学習率/u }).fill("0.06");
  await expect(region.getByText(/発散しました/u).first()).toBeVisible();
  await region.getByRole("slider", { name: /学習率/u }).fill("0.03");
  await expect(region.getByText(/発散しました/u)).toHaveCount(0);
  await region.getByRole("radio", { name: "Momentum" }).check({ force: true });
  await expect(region.getByRole("slider", { name: /持ち越し/u })).toBeVisible();
});
