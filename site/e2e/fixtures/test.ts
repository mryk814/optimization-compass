import { expect, test as base, type BrowserContext, type Page } from "@playwright/test";
import { writeFile } from "node:fs/promises";

type BrowserEventKind = "console" | "pageerror" | "requestfailed";

export type BrowserEvent = {
  kind: BrowserEventKind;
  level?: string;
  text: string;
  url?: string;
};

type BrowserLog = {
  events: readonly BrowserEvent[];
  allowError(pattern: RegExp): void;
};

type Fixtures = {
  browserLog: BrowserLog;
};

function wirePage(page: Page, events: BrowserEvent[], wiredPages: WeakSet<Page>) {
  if (wiredPages.has(page)) return;
  wiredPages.add(page);

  page.on("console", (message) => {
    const location = message.location();
    events.push({
      kind: "console",
      level: message.type(),
      text: message.text(),
      url: location.url || undefined,
    });
  });
  page.on("pageerror", (error) => {
    events.push({ kind: "pageerror", text: error.stack ?? error.message });
  });
  page.on("requestfailed", (request) => {
    events.push({
      kind: "requestfailed",
      text: request.failure()?.errorText ?? "request failed",
      url: request.url(),
    });
  });
}

function wireContext(context: BrowserContext, events: BrowserEvent[]) {
  const wiredPages = new WeakSet<Page>();
  context.pages().forEach((page) => wirePage(page, events, wiredPages));
  context.on("page", (page) => wirePage(page, events, wiredPages));
}

export const test = base.extend<Fixtures>({
  browserLog: [async ({ context }, use, testInfo) => {
    const events: BrowserEvent[] = [];
    const allowedErrors: RegExp[] = [];
    wireContext(context, events);

    await use({
      events,
      allowError(pattern) {
        allowedErrors.push(pattern);
      },
    });

    const consolePath = testInfo.outputPath("browser-console.json");
    await writeFile(consolePath, JSON.stringify(events, null, 2), "utf8");
    await testInfo.attach("browser-console", { path: consolePath, contentType: "application/json" });

    const errors = events.filter(
      (event) =>
        event.kind === "pageerror" ||
        event.kind === "requestfailed" ||
        (event.kind === "console" && event.level === "error"),
    );
    const serialized = (event: BrowserEvent) => JSON.stringify(event);
    const unexpected = errors.filter(
      (event) => !allowedErrors.some((pattern) => pattern.test(serialized(event))),
    );
    const missing = allowedErrors.filter(
      (pattern) => !errors.some((event) => pattern.test(serialized(event))),
    );

    expect(unexpected, "unexpected browser errors").toEqual([]);
    expect(missing.map((pattern) => pattern.source), "expected browser errors").toEqual([]);
  }, { auto: true }],
});

export { expect } from "@playwright/test";
