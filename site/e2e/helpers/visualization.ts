import { expect, type Locator, type Page } from "@playwright/test";

export async function expectNelderMeadSvg(plot: Locator): Promise<void> {
  await expect(plot).toBeVisible();
  await expect(plot).toHaveAttribute("viewBox", "0 0 560 360");
  await expect(plot.locator("title")).not.toHaveText("");
  await expect(plot.locator("desc")).not.toHaveText("");

  const contours = plot.locator(".objective-contours line");
  expect(await contours.count()).toBeGreaterThan(20);
  await expect(contours.first()).toBeVisible();

  const simplex = plot.locator(".nm-simplex");
  await expect(simplex).toBeVisible();
  const simplexPoints = (await simplex.getAttribute("points"))?.trim().split(/\s+/u) ?? [];
  expect(simplexPoints).toHaveLength(3);
  expect(simplexPoints.every(finiteCoordinatePair)).toBe(true);

  await expect(plot.locator(".nm-vertex-best circle")).toBeVisible();
  await expect(plot.locator(".nm-vertex-second-worst rect")).toBeVisible();
  await expect(plot.locator(".nm-vertex-worst polygon")).toBeVisible();
  await expect(plot.locator(".nm-centroid")).toBeVisible();
  await expect(plot.locator(".nm-candidate polygon")).toBeVisible();

  const operation = plot.locator(".nm-operation-vector");
  await expect(operation).toBeVisible();
  await expect(operation).toHaveAttribute("marker-end", "url(#nm-arrow)");
  const [x1, y1, x2, y2] = await Promise.all(
    ["x1", "y1", "x2", "y2"].map(async (name) => Number(await operation.getAttribute(name))),
  );
  expect([x1, y1, x2, y2].every(Number.isFinite)).toBe(true);
  expect(Math.hypot(x2 - x1, y2 - y1)).toBeGreaterThan(0);
}

export async function expectGradientComparisonSvg(page: Page, evaluation: number): Promise<void> {
  const plots = page.locator(".comparison-plot");
  await expect(plots).toHaveCount(3);
  for (let index = 0; index < 3; index += 1) {
    const plot = plots.nth(index);
    await expect(plot).toBeVisible();
    await expect(plot).toHaveAttribute("viewBox", "0 0 300 194");
    await expect(plot).toHaveAttribute("aria-label", /等高線・軌跡・gradient・update vector/u);
    expect(await plot.locator(".objective-contours line").count()).toBeGreaterThan(20);

    const trajectory = plot.locator(".trajectory-line");
    await expect(trajectory).toBeVisible();
    const points = (await trajectory.getAttribute("points"))?.trim().split(/\s+/u) ?? [];
    expect(points.length).toBeGreaterThan(1);
    expect(points.every(finiteCoordinatePair)).toBe(true);

    await expect(plot.locator(".gradient-vector")).toBeVisible();
    await expect(plot.locator(".update-vector")).toBeVisible();
    await expect(plot.locator(".method-marker")).toHaveCount(1);
  }

  const history = page.getByRole("img", {
    name: "3件のmemberの目的関数値を同じoracle evaluation軸で比較",
  });
  await expect(history).toBeVisible();
  await expect(history.locator(".history-series")).toHaveCount(3);
  const cursor = history.locator(".history-cursor");
  const cursorX = Number(await cursor.getAttribute("x1"));
  expect(cursorX).toBe(Number(await cursor.getAttribute("x2")));
  for (let index = 0; index < 3; index += 1) {
    const points = (await history.locator(".history-series").nth(index).locator("polyline").getAttribute("points"))
      ?.trim().split(/\s+/u) ?? [];
    expect(points.length).toBeGreaterThan(1);
    const lastX = Number(points.at(-1)?.split(",")[0]);
    expect(lastX).toBeCloseTo(cursorX, 5);
  }

  const textAlternatives = page.locator(".objective-history .text-alternative li");
  await expect(textAlternatives).toHaveCount(3);
  for (let index = 0; index < 3; index += 1) {
    await expect(textAlternatives.nth(index)).toContainText(`evaluation ${evaluation}`);
  }
}

export async function expectFitsViewport(locator: Locator, page: Page): Promise<void> {
  const box = await locator.boundingBox();
  const viewport = page.viewportSize();
  expect(box).not.toBeNull();
  expect(viewport).not.toBeNull();
  expect(box!.width).toBeGreaterThan(0);
  expect(box!.height).toBeGreaterThan(0);
  expect(box!.x).toBeGreaterThanOrEqual(0);
  expect(box!.x + box!.width).toBeLessThanOrEqual(viewport!.width + 1);
}

function finiteCoordinatePair(value: string): boolean {
  const coordinates = value.split(",").map(Number);
  return coordinates.length === 2 && coordinates.every(Number.isFinite);
}
