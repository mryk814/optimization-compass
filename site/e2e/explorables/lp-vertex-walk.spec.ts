import { expect, test } from "../fixtures/test";
import { gotoAtlasRoute } from "../helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

test("LPのlessonが角で売上24に着き、自分で売値を動かすと最良の角が切り替わる", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/learn/concept.linear-program");
  const region = page.locator('[data-explorable-id="lp-vertex-walk"]');
  await expect(region.getByText("見る問い")).toBeVisible();
  const plan = region.getByRole("group", { name: /いまの計画/u });
  const show = (step: number) => page.evaluate(
    (index) => window.__ocLessons?.["lp-vertex-walk"]?.show(index),
    step - 1,
  );
  await page.waitForFunction(() => Boolean(window.__ocLessons?.["lp-vertex-walk"]));

  // 予想の段までは、角の売上も操作部品も出さない。
  await show(4);
  await expect(region.getByRole("math", { name: "売上は 3 × 2 + 4 × 1.5 = 12" })).toBeVisible();
  await expect(region.getByText(/売上 24/u)).toHaveCount(0);
  await expect(region.getByRole("slider")).toHaveCount(0);

  // 種明かしの段の終わりは、小麦粉もバターも使い切る角。
  await show(5);
  await expect(plan).toHaveAttribute("aria-label", /食パン 4個・クロワッサン 3個。小麦粉もバターも使い切りです/u);
  await expect(region.getByRole("math", { name: "売上は 3 × 4 + 4 × 3 = 24" })).toBeVisible();

  // 最後の段（クロワッサンの売上 1）の状態が、そのまま読者の操作に渡る。
  await show(8);
  await page.getByRole("button", { name: "自分で動かす" }).click();
  const croissant = region.getByRole("slider", { name: /クロワッサン1個の売上/u });
  await expect(croissant).toHaveValue("1");
  await expect(region.getByText(/売上がいちばん大きい計画は 食パン 6個・クロワッサン 0個 で、売上は 18 です/u).first()).toBeVisible();
  await croissant.fill("4");
  await expect(region.getByText(/売上がいちばん大きい計画は 食パン 4個・クロワッサン 3個 で、売上は 24 です/u).first()).toBeVisible();
  await region.getByRole("button", { name: "いちばん良い角へ" }).click();
  await expect(plan).toHaveAttribute("aria-label", /食パン 4個・クロワッサン 3個/u);
});
