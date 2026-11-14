import { expect, test } from "../fixtures/test";
import { gotoAtlasRoute } from "../helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

test("LPの図で係数を動かすと最適な頂点が切り替わる", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/learn/concept.linear-program");
  const region = page.locator('[data-explorable-id="lp-vertex-walk"]');
  await expect(region.getByText("見る問い")).toBeVisible();
  await expect(region.getByText(/最適解は頂点 \(4\.0, 3\.0\)、目的値は z=24/u).first()).toBeVisible();
  await region.getByRole("slider", { name: /係数 c₁/u }).fill("-1");
  await expect(region.getByText(/最適解は頂点 \(0\.0, 4\.3\)/u).first()).toBeVisible();
});
