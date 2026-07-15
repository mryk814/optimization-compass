import { test, expect } from "./fixtures/test";
import { expectNoHighImpactViolations } from "./helpers/accessibility";
import { gotoAtlasRoute } from "./helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

test("Diagnoseから現在stateのMarkdownを編集・copyし、URLとscrollを維持する", async ({ page, context, baseURL }, testInfo) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  const nonGetRequests: string[] = [];
  page.on("request", (request) => {
    if (request.method() !== "GET") nonGetRequests.push(`${request.method()} ${request.url()}`);
  });

  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/diagnose");
  const question = page.getByRole("group", {
    name: "どんなものを決めたいですか？",
  });
  await question.getByRole("button", { name: "0-1" }).click();
  const trigger = page.getByRole("button", { name: "実装用プロンプトを作る" });
  await trigger.scrollIntoViewIfNeeded();
  const urlBefore = page.url();
  const scrollBefore = await page.evaluate(() => window.scrollY);

  await trigger.click();
  const dialog = page.getByRole("dialog", { name: "実装用プロンプトを作る" });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByLabel("やりたいこと")).toBeFocused();
  await dialog.getByLabel("Programming language").fill("Python 3.12");
  await expect(dialog.getByLabel("実装用プロンプトのMarkdown preview")).toHaveValue(/Programming language: Python 3\.12/u);

  const preview = dialog.getByLabel("実装用プロンプトのMarkdown preview");
  await preview.fill("copy this exact implementation prompt");
  await dialog.getByRole("button", { name: "Markdownをコピー" }).click();
  await expect(dialog.getByText("実装用プロンプトをコピーしました。")).toBeVisible();
  await expect.poll(() => page.evaluate(() => navigator.clipboard.readText())).toBe("copy this exact implementation prompt");
  await expectNoHighImpactViolations(page, testInfo, "diagnose-prompt-export");

  await dialog.getByRole("button", { name: "実装用プロンプトを閉じる" }).click();
  await expect(dialog).toBeHidden();
  await expect(trigger).toBeFocused();
  expect(page.url()).toBe(urlBefore);
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(scrollBefore);
  expect(nonGetRequests).toEqual([]);
});

test("Gallery caseは明記済みproblemだけをprefillし、環境をunknownで残す", async ({ page, baseURL }, testInfo) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/gallery/EC019");
  const urlBefore = page.url();
  await page.getByRole("button", { name: "実装用プロンプトを作る" }).click();
  const dialog = page.getByRole("dialog", { name: "実装用プロンプトを作る" });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByLabel("やりたいこと")).toHaveValue("1000件の配送先と時間窓を満たす良いrouteを、10分以内に得たい。");
  await expect(dialog.getByLabel("Programming language")).toHaveValue("unknown");
  await expect(dialog.getByRole("group", { name: "Requested outputs" }).getByRole("checkbox", { checked: true })).toHaveCount(3);
  await expect(dialog.getByLabel("実装用プロンプトのMarkdown preview")).toHaveValue(/Atlas origin: Gallery EC019/u);
  expect(page.url()).toBe(urlBefore);
  await expectNoHighImpactViolations(page, testInfo, "gallery-prompt-export");
});
