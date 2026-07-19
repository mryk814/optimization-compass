import { expect, test } from "./fixtures/test";
import { gotoAtlasRoute } from "./helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

test("bilevel Theaterでouter・inner・complementarityを分けて読める", async ({
  page,
  baseURL,
}) => {
  await gotoAtlasRoute(
    page,
    requiredBaseURL(baseURL),
    "/traces/bilevel-regression-exact-inner",
  );

  await expect(
    page.getByRole("heading", { level: 1, name: "Bilevel回帰 · exact inner診断" }),
  ).toBeVisible();
  const history = page.getByRole("region", { name: "指標の履歴" });
  await expect(history).toBeVisible();
  await expect(history.getByRole("heading", { level: 3, name: /outer objective/u })).toBeVisible();
  await expect(history.getByRole("heading", { level: 3, name: /inner residual/u })).toBeVisible();
  await expect(
    history.getByRole("heading", { level: 3, name: /complementarity residual/u }),
  ).toBeVisible();
  await expect(page.getByText(/global最適性、CQ、solution map/u)).toBeVisible();
});

test("bilevel Compareはcomplementarity treatmentだけを変え、順位づけしない", async ({
  page,
  baseURL,
}) => {
  await gotoAtlasRoute(
    page,
    requiredBaseURL(baseURL),
    "/compare/COMPARE_BILEVEL_COMPLEMENTARITY_TREATMENT",
  );

  await expect(
    page.getByRole("heading", {
      level: 1,
      name: "exact KKTと有限relaxationを残差で読み分ける",
    }),
  ).toBeVisible();
  const conditions = page.getByRole("region", { name: "比較条件" });
  await expect(conditions.getByText("inner tolerance 1e-8 and maximum 100 iterations")).toBeVisible();
  await expect(conditions.getByText(/complementarity treatment only/u)).toBeVisible();
  await conditions.getByText("評価条件の詳細を開く", { exact: true }).click();
  await expect(conditions.getByText("順位づけ", { exact: true }).locator("..")).toContainText(
    "しない",
  );
});

test("hybrid failure Theaterはobjective改善とchattering停止を分ける", async ({
  page,
  baseURL,
}) => {
  await gotoAtlasRoute(
    page,
    requiredBaseURL(baseURL),
    "/traces/hybrid-mode-chattering-ledger",
  );

  await expect(
    page.getByRole("heading", { level: 1, name: "Hybrid mode discovery · chattering診断" }),
  ).toBeVisible();
  const history = page.getByRole("region", { name: "指標の履歴" });
  await expect(history.getByRole("heading", { level: 3, name: /mode切替数/u })).toBeVisible();
  await expect(history.getByRole("heading", { level: 3, name: /切替間隔/u })).toBeVisible();
  await expect(page.getByText(/contact\/friction model、物理simulationではない/u)).toBeVisible();
});
