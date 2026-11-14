import { expect, test } from "../fixtures/test";
import { gotoAtlasRoute } from "../helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

test("凸性の図で二つの谷を選ぶと定義の違反が見つかり、点をキーボードで動かせる", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/learn/concept.convexity");
  const region = page.locator('[data-explorable-id="convexity-chord"]');
  await expect(region.getByText("見る問い")).toBeVisible();
  await expect(region.getByText(/この関数は凸なので/u).first()).toBeVisible();
  await region.getByRole("radio", { name: /二つの谷/u }).check({ force: true });
  await expect(region.getByText(/この関数は凸ではありません/u).first()).toBeVisible();
  const handle = region.getByRole("slider", { name: "点aの位置" });
  await handle.focus();
  const before = await handle.getAttribute("aria-valuenow");
  await handle.press("ArrowRight");
  expect(await handle.getAttribute("aria-valuenow")).not.toBe(before);
});
