import { expect, test } from "../fixtures/test";
import { gotoAtlasRoute } from "../helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

test("単体法の図で増やす変数を選び、比の最小値まで進めると最適な頂点に着く", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/learn/primal-simplex");
  const region = page.locator('[data-explorable-id="simplex-pivot"]');
  await expect(region.getByText("見る問い")).toBeVisible();
  await region.getByRole("button", { name: /x₂（クロワッサン）を増やす/u }).click();
  await region.getByRole("slider", { name: /増やす量 θ/u }).fill("5");
  await expect(region.getByText(/バターの余りが負になりました/u).first()).toBeVisible();
  await region.getByRole("button", { name: "比の最小値 θ=13/3 まで進めて s₂ と入れ替える" }).click();
  await region.getByRole("button", { name: /x₁（食パン）を増やす/u }).click();
  await region.getByRole("button", { name: "比の最小値 θ=4 まで進めて s₁ と入れ替える" }).click();
  await expect(region.getByText(/頂点 \(4, 3\) が最適で、売上は 24 です/u).first()).toBeVisible();
});
