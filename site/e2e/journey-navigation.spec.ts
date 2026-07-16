import { test, expect } from "./fixtures/test";
import { atlasUrl, gotoAtlasRoute } from "./helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

test("Case→Theater→Compare→Caseで共有可能なjourney文脈を保つ", async ({
  page,
  context,
  baseURL,
}) => {
  const root = requiredBaseURL(baseURL);
  await gotoAtlasRoute(page, root, "/gallery/EC017");
  await page.getByRole("link", { name: /固定した1 runを追う/u }).click();

  const journey = page.getByRole("complementary", { name: "Case learning journey" });
  await expect(journey).toContainText("Step 2/4");
  await expect(page).toHaveURL(/#\/theater\/learning\/SCENARIO_BIOBJECTIVE_QUADRATIC\?state=/u);
  await journey.getByRole("link", { name: /次はCompare/u }).click();
  await expect(journey).toContainText("Step 3/4");
  await expect(page).toHaveURL(/#\/compare\/COMPARE_PARETO_PREFERENCE\?state=/u);

  const sharedUrl = page.url();
  await page.reload();
  await expect(journey).toContainText("Step 3/4");
  const sharedPage = await context.newPage();
  await sharedPage.goto(sharedUrl);
  await expect(sharedPage.getByRole("complementary", { name: "Case learning journey" })).toContainText("Step 3/4");

  await journey.getByRole("link", { name: "Case", exact: true }).click();
  await expect(page).toHaveURL(/#\/gallery\/EC017\?state=/u);
  await expect(page.getByRole("heading", { name: "costと性能のPareto trade-offを探索する" })).toBeVisible();
  await expect(journey).toContainText("Step 1/4");
});

test("browser backと画面内Backがそれぞれ予測可能に動く", async ({ page, baseURL }) => {
  const root = requiredBaseURL(baseURL);
  await gotoAtlasRoute(page, root, "/gallery/EC017");
  await page.getByRole("link", { name: /固定した1 runを追う/u }).click();
  await expect(page.getByRole("complementary", { name: "Case learning journey" })).toContainText("Step 2/4");
  await page.getByRole("link", { name: /次はCompare/u }).click();
  await expect(page.getByRole("heading", { name: "Pareto front上でpreferenceを変える" })).toBeVisible();

  await page.goBack();
  await expect(page).toHaveURL(/#\/theater\/learning\/SCENARIO_BIOBJECTIVE_QUADRATIC\?state=/u);
  await page.getByRole("button", { name: "← このCaseへ戻る" }).click();
  await expect(page).toHaveURL(/#\/gallery\/EC017\?state=/u);
});

test("文脈のないdeep linkは従来の安全なfallbackを使う", async ({ page, baseURL }) => {
  await gotoAtlasRoute(
    page,
    requiredBaseURL(baseURL),
    "/theater/learning/SCENARIO_BIOBJECTIVE_QUADRATIC",
  );
  await expect(page.getByRole("complementary", { name: "Case learning journey" })).toHaveCount(0);
  await page.getByRole("button", { name: "← 戻る" }).click();
  await expect(page).toHaveURL(/#\/theater$/u);
});

test("dataset版が変わった共有URLは古いjourneyを誤復元しない", async ({ page, baseURL }) => {
  const root = requiredBaseURL(baseURL);
  await gotoAtlasRoute(page, root, "/gallery/EC017");
  await page.getByRole("link", { name: /固定した1 runを追う/u }).click();
  await expect(page.getByRole("complementary", { name: "Case learning journey" })).toContainText("Step 2/4");

  const hashUrl = new URL(`https://atlas.invalid${new URL(page.url()).hash.slice(1)}`);
  const token = hashUrl.searchParams.get("state");
  expect(token).toBeTruthy();
  const state = JSON.parse(Buffer.from(token ?? "", "base64url").toString("utf8")) as Record<string, unknown>;
  state.datasetVersion = "stale-dataset";
  hashUrl.searchParams.set("state", Buffer.from(JSON.stringify(state)).toString("base64url"));
  await page.goto(atlasUrl(root, `${hashUrl.pathname}${hashUrl.search}`));

  await expect(page.getByRole("alert")).toContainText("dataset版が現在版と異なる");
  await expect(page.getByRole("complementary", { name: "Case learning journey" })).toHaveCount(0);
});

test("CompareからMethodへ進んでも元のCaseへ戻れる", async ({ page, baseURL }) => {
  const root = requiredBaseURL(baseURL);
  await gotoAtlasRoute(page, root, "/gallery/EC017");
  await page.getByRole("link", { name: /固定した1 runを追う/u }).click();
  await page.getByRole("link", { name: /次はCompare/u }).click();
  await page.getByRole("link", { name: /次は手法の前提を読む/u }).click();

  await expect(page).toHaveURL(/#\/methods\/M_NSGA_II\?state=/u);
  await expect(page.getByRole("complementary", { name: "Case learning journey" })).toContainText("Step 4/4");
  await page.getByRole("button", { name: "← このCaseへ戻る" }).click();
  await expect(page).toHaveURL(/#\/gallery\/EC017\?state=/u);
});

test("壊れたstate tokenを静かに無視せず表示する", async ({ page, baseURL }) => {
  await gotoAtlasRoute(
    page,
    requiredBaseURL(baseURL),
    "/theater/learning/SCENARIO_BIOBJECTIVE_QUADRATIC?state=broken",
  );
  await expect(page.getByRole("alert")).toContainText("共有URLの状態を復元できません");
});
