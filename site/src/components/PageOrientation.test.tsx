import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, test } from "vitest";

import { PageOrientation } from "./PageOrientation";

describe("PageOrientation", () => {
  test("keeps repeated guidance collapsed and exposes all sections on request", () => {
    render(
      <MemoryRouter>
        <PageOrientation
          limits="固定されたデータの範囲で読む。"
          next={[{ label: "Map", to: "/map" }]}
          purpose="この画面の目的。"
          readingSteps={["最初に見出しを見る。", "次に詳細を見る。"]}
        />
      </MemoryRouter>,
    );

    expect(screen.getByRole("complementary", { name: "このページの使い方" })).toBeVisible();
    const summary = screen.getByText("このページでの読み方");
    expect(summary).toBeVisible();
    expect(screen.getByRole("heading", { name: "このページの目的", hidden: true })).not.toBeVisible();

    fireEvent.click(summary);

    expect(screen.getByRole("heading", { name: "このページの目的" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "読む順番" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "前提・限界" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "次に進む" })).toBeVisible();
    expect(screen.getByRole("link", { name: "Map →" })).toHaveAttribute("href", "/map");
  });
});
