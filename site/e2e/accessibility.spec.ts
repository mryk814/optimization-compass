import { test } from "./fixtures/test";
import { expectNoHighImpactViolations } from "./helpers/accessibility";
import { gotoAtlasRoute } from "./helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

test("Homeにaxe critical/serious違反がない", async ({ page, baseURL }, testInfo) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/");
  await page.getByRole("heading", {
    level: 1,
    name: "最適化したい。でも、何をどう解けばいい？",
  }).waitFor();
  await expectNoHighImpactViolations(page, testInfo, "home");
});

test("選択後のMapにaxe critical/serious違反がない", async ({ page, baseURL }, testInfo) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/map");
  const tree = page.getByRole("tree", { name: "最適化問題の構造" });
  await tree.waitFor();
  await tree.getByRole("treeitem").first().click();
  await expectNoHighImpactViolations(page, testInfo, "map-selected");
});

test("回答後のDiagnoseにaxe critical/serious違反がない", async ({ page, baseURL }, testInfo) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/diagnose");
  const question = page.getByRole("group", {
    name: "x（決めるもの）はどの種類ですか？",
  });
  await question.getByRole("button", { name: /^0-1/u }).click();
  await expectNoHighImpactViolations(page, testInfo, "diagnose-answered");
});

const staticScans = [
  { route: "/gallery/hyperparameter-search", heading: "高価な実験の設定を探す", label: "gallery-detail" },
  { route: "/learn/method.nelder-mead", heading: "Nelder–Mead単体法", label: "learn-detail" },
  { route: "/traces/nelder-mead-quadratic", heading: "Nelder–Meadの幾何操作", label: "nelder-mead" },
  { route: "/compare/gradient-quadratic", heading: "細長い谷で一次法を比べる", label: "gradient-compare" },
  { route: "/theater/learning/SCENARIO_CONSTRAINED_DISK", heading: "実行可能領域と制約を無視した失敗を比べる", label: "constrained-slice" },
  { route: "/theater/learning/SCENARIO_BIOBJECTIVE_QUADRATIC", heading: "単一bestではなくPareto frontを読む", label: "pareto-slice" },
  { route: "/coverage", heading: "Atlas Coverage", label: "coverage" },
  { route: "/failures", heading: "失敗の兆候から探す", label: "failure-discovery" },
  { route: "/search?q=BO&type=method", heading: "Atlas全体から探す", label: "global-search" },
  { route: "/missing-route", heading: "ページが見つかりません", label: "not-found" },
];

for (const scan of staticScans) {
  test(`${scan.label}にaxe critical/serious違反がない`, async ({ page, baseURL }, testInfo) => {
    await gotoAtlasRoute(page, requiredBaseURL(baseURL), scan.route);
    await page.getByRole("heading", { level: 1, name: scan.heading }).waitFor();
    if (scan.label === "learn-detail") {
      await page.getByRole("heading", { level: 2, name: "Learning path" }).waitFor();
    }
    if (scan.label === "nelder-mead" || scan.label === "gradient-compare") {
      await page.getByRole("region", { name: "アルゴリズム再生コントロール" }).waitFor();
    }
    await expectNoHighImpactViolations(page, testInfo, scan.label);
  });
}
