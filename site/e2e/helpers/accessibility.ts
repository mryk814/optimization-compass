import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, type TestInfo } from "@playwright/test";

const wcagTags = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"];

export async function expectNoHighImpactViolations(
  page: Page,
  testInfo: TestInfo,
  label: string,
) {
  const results = await new AxeBuilder({ page }).withTags(wcagTags).analyze();
  await testInfo.attach(`axe-${label}`, {
    body: JSON.stringify(results, null, 2),
    contentType: "application/json",
  });
  const highImpact = results.violations
    .filter(({ impact }) => impact === "critical" || impact === "serious")
    .map(({ id, impact, help, nodes }) => ({
      id,
      impact,
      help,
      targets: nodes.map((node) => node.target),
    }));
  expect(highImpact, `${label}: axe critical/serious violations`).toEqual([]);
}
