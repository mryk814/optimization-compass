import { test, expect } from "./fixtures/test";
import { gotoAtlasRoute, pagesBasePath } from "./helpers/navigation";

function requiredBaseURL(baseURL: string | undefined): string {
  if (!baseURL) throw new Error("Playwright baseURL is required.");
  return baseURL;
}

test("HomeからMapを展開し、共有URLとreloadで選択を復元する", async ({
  page,
  context,
  baseURL,
}) => {
  const jsonPaths: string[] = [];
  page.on("response", (response) => {
    const url = new URL(response.url());
    if (url.pathname.endsWith(".json")) jsonPaths.push(url.pathname);
  });

  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/");
  await page.getByRole("link", { name: "地図を見る" }).click();
  const tree = page.getByRole("tree", { name: "最適化問題の構造" });
  await expect(tree).toBeVisible();

  const firstRoot = tree.getByRole("treeitem").first();
  await firstRoot.focus();
  await page.keyboard.press("ArrowRight");
  await expect(firstRoot).toHaveAttribute("aria-expanded", "true");
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("Enter");

  const selected = tree.locator('[role="treeitem"][aria-selected="true"]');
  await expect(selected).toHaveCount(1);
  const selectedLabel = await selected.locator(".map-tree-label").textContent();
  expect(selectedLabel).toBeTruthy();
  await expect(page).toHaveURL(/#\/map\?state=/u);
  expect(new URL(page.url()).pathname).toBe(pagesBasePath);
  expect(jsonPaths.length).toBeGreaterThan(0);
  expect(jsonPaths.every((path) => path.startsWith(`${pagesBasePath}data/`))).toBe(true);

  const shareUrl = page.url();
  const sharedPage = await context.newPage();
  await sharedPage.goto(shareUrl);
  const sharedTree = sharedPage.getByRole("tree", { name: "最適化問題の構造" });
  const sharedSelection = sharedTree
    .locator('[role="treeitem"][aria-selected="true"]')
    .filter({ hasText: selectedLabel ?? "" });
  await expect(sharedSelection).toHaveCount(1);

  await sharedPage.reload();
  await expect(
    sharedPage
      .getByRole("tree", { name: "最適化問題の構造" })
      .locator('[role="treeitem"][aria-selected="true"]')
      .filter({ hasText: selectedLabel ?? "" }),
  ).toHaveCount(1);
});

test("Mapの選択をbrowser backとforwardで復元する", async ({ page, baseURL }) => {
  await gotoAtlasRoute(page, requiredBaseURL(baseURL), "/map");
  const tree = page.getByRole("tree", { name: "最適化問題の構造" });
  await expect(tree).toBeVisible();
  const roots = tree.locator(':scope > div > [role="treeitem"]');
  const first = roots.nth(0);
  const second = roots.nth(1);
  const firstLabel = await first.locator(".map-tree-label").textContent();
  const secondLabel = await second.locator(".map-tree-label").textContent();

  await first.click();
  await expect(first).toHaveAttribute("aria-selected", "true");
  await second.click();
  await expect(second).toHaveAttribute("aria-selected", "true");

  await page.goBack();
  await expect(
    tree.locator('[role="treeitem"][aria-selected="true"]').filter({ hasText: firstLabel ?? "" }),
  ).toHaveCount(1);
  await page.goForward();
  await expect(
    tree.locator('[role="treeitem"][aria-selected="true"]').filter({ hasText: secondLabel ?? "" }),
  ).toHaveCount(1);
});
