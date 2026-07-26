import { expect, test } from "./fixtures/test";
import { gotoAtlasRoute } from "./helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

test("日本語IMEの変換確定まで検索条件を更新しない", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/search");
  const input = page.getByRole("searchbox", { name: "検索" });
  await expect(page.getByText(/件を検索できます/u)).toBeVisible();

  await input.evaluate((element) => {
    element.dispatchEvent(new CompositionEvent("compositionstart", { bubbles: true }));
    element.value = "ベイズ";
    element.dispatchEvent(new InputEvent("input", {
      bubbles: true,
      data: "ベイズ",
      inputType: "insertCompositionText",
      isComposing: true,
    }));
  });

  await expect(input).toHaveValue("ベイズ");
  await expect(page).not.toHaveURL(/[?&]q=/u);
  await expect(page.getByText(/件を検索できます/u)).toBeVisible();

  await input.evaluate((element) => {
    element.dispatchEvent(new CompositionEvent("compositionend", { bubbles: true, data: "ベイズ" }));
  });

  await expect.poll(() => page.evaluate(() => {
    const query = window.location.hash.split("?", 2)[1] ?? "";
    return new URLSearchParams(query).get("q");
  })).toBe("ベイズ");
  await expect(page.getByRole("heading", { name: "ベイズ最適化", exact: true }).first()).toBeVisible();
});

test("主要導線を常設し、探索導線を必要なときだけ展開する", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/");
  const navigation = page.getByRole("navigation", { name: "主要ナビゲーション" });
  await expect(navigation.getByRole("link")).toHaveText(["条件で診断", "事例を見る", "手法を学ぶ"]);

  await expect(navigation.getByRole("link", { name: "横断検索" })).not.toBeVisible();
  await navigation.getByText("探索", { exact: true }).click();
  await expect(navigation.getByRole("link", { name: "横断検索" })).toBeVisible();
  await expect(navigation.getByRole("link", { name: "根拠を見る" })).toBeVisible();
});
