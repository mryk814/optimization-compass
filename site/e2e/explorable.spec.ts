import { expect, test } from "./fixtures/test";
import { expectNoHighImpactViolations } from "./helpers/accessibility";
import { expectNoHorizontalOverflow, gotoAtlasRoute } from "./helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

const figures = [
  {
    label: "gradient-descent",
    route: "/learn/method.gradient-descent",
    id: "gradient-descent-valley",
  },
  { label: "primal-simplex", route: "/learn/primal-simplex", id: "lp-vertex-walk" },
  { label: "convexity", route: "/learn/concept.convexity", id: "convexity-chord" },
  { label: "nonlinear-least-squares", route: "/learn/concept.nonlinear-least-squares", id: "nonlinear-least-squares-landscape" },
  { label: "newton-method", route: "/learn/newton-method", id: "newton-parabola-jump" },
  { label: "cma-es", route: "/learn/cma-es", id: "cmaes-shape-learning" },
  { label: "interior-point-nlp", route: "/learn/interior-point-nlp", id: "interior-point-barrier-path" },
  { label: "multiobjective", route: "/learn/concept.multiobjective-optimization", id: "multiobjective-pareto-weights" },
];

for (const figure of figures) {
  test(`@critical ${figure.label}の動く図が表示され、axe違反がない`, async ({ page, baseURL }, testInfo) => {
    await gotoAtlasRoute(page, requiredBaseURL(baseURL), figure.route);
    const region = page.locator(`[data-explorable-id="${figure.id}"]`);
    await expect(region.getByText("見る問い")).toBeVisible();
    await expect(region.locator(".explorable-fallback")).toHaveCount(0);
    await expect(region.getByRole("group", { name: "図" })).toBeVisible();
    await region.scrollIntoViewIfNeeded();
    await expectNoHighImpactViolations(page, testInfo, `explorable-${figure.label}`);
  });

  test(`${figure.label}の図が375pxで横にはみ出さず、文字が縮まない`, async ({ page, baseURL }) => {
    await page.setViewportSize({ width: 375, height: 800 });
    await gotoAtlasRoute(page, requiredBaseURL(baseURL), figure.route);
    const region = page.locator(`[data-explorable-id="${figure.id}"]`);
    await expect(region.getByText("見る問い")).toBeVisible();
    await expectNoHorizontalOverflow(page);
    // The SVG uses one unit per CSS pixel, so rendered chart text keeps its 13px size.
    const rendered = await region.locator("svg text").first().evaluate((node) => {
      const box = node.getBoundingClientRect();
      const style = getComputedStyle(node);
      return { size: Number.parseFloat(style.fontSize), height: box.height };
    });
    expect(rendered.size).toBeGreaterThanOrEqual(12);
    expect(rendered.height).toBeGreaterThanOrEqual(10);
  });
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

test("LPの図で係数を動かすと最適な頂点が切り替わる", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/learn/primal-simplex");
  const region = page.locator('[data-explorable-id="lp-vertex-walk"]');
  await expect(region.getByText("見る問い")).toBeVisible();
  await expect(region.getByText(/最適解は頂点 \(1\.0, 3\.0\)/u).first()).toBeVisible();
  await region.getByRole("slider", { name: /係数 c₁/u }).fill("-1");
  await expect(region.getByText(/最適解は頂点 \(0\.0, 4\.0\)/u).first()).toBeVisible();
});
