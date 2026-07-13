import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test } from "vitest";

import App from "./App";

const routes = [
  ["#/", "Optimization Atlas"],
  ["#/map", "問題構造マップ"],
  ["#/diagnose", "診断"],
  ["#/methods/sample-method", "手法を理解する"],
  ["#/compare/sample-comparison", "手法を比較する"],
  ["#/gallery", "ケースギャラリー"],
  ["#/gallery/sample-case", "ケース詳細"],
] as const;

describe("application routes", () => {
  beforeEach(() => {
    window.location.hash = "#/";
  });

  afterEach(() => {
    cleanup();
  });

  test.each(routes)("%s renders %s", (hash, heading) => {
    window.location.hash = hash;

    render(<App />);

    expect(screen.getByRole("heading", { level: 1, name: heading })).toBeVisible();
  });

  test("direct parameter routes display their identifiers", () => {
    window.location.hash = "#/methods/gaussian-process";
    const { unmount } = render(<App />);
    expect(screen.getByText("gaussian-process")).toBeVisible();
    unmount();

    window.location.hash = "#/compare/fixed-budget";
    const comparison = render(<App />);
    expect(screen.getByText("fixed-budget")).toBeVisible();
    comparison.unmount();

    window.location.hash = "#/gallery/materials-case";
    render(<App />);
    expect(screen.getByText("materials-case")).toBeVisible();
  });

  test("primary navigation stays reachable at 375px", () => {
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 375,
    });

    render(<App />);

    const navigation = screen.getByRole("navigation", { name: "主要ナビゲーション" });
    const links = within(navigation).getAllByRole("link");
    expect(links).toHaveLength(6);
    links.forEach((link) => expect(link).toBeVisible());
    expect(links[0]).toHaveAttribute("aria-current", "page");
  });

  test("dynamic routes keep their navigation family active", () => {
    window.location.hash = "#/methods/gaussian-process";

    render(<App />);

    expect(screen.getByRole("link", { name: "手法" })).toHaveAttribute("aria-current", "page");
  });

  test("unknown routes render a useful error page inside the shell", () => {
    window.location.hash = "#/unknown";

    render(<App />);

    expect(screen.getByRole("heading", { level: 1, name: "ページが見つかりません" })).toBeVisible();
    expect(screen.getByRole("main")).toBeVisible();
    expect(screen.getByRole("contentinfo")).toBeVisible();
  });

  test.each(["#/mapping", "#/diagnose-old", "#/gallery-old"])(
    "%s does not activate a prefix-colliding navigation item",
    (hash) => {
      window.location.hash = hash;

      render(<App />);

      expect(
        screen.getByRole("heading", { level: 1, name: "ページが見つかりません" }),
      ).toBeVisible();
      expect(
        within(screen.getByRole("navigation", { name: "主要ナビゲーション" })).queryByRole(
          "link",
          { current: "page" },
        ),
      ).not.toBeInTheDocument();
    },
  );
});
