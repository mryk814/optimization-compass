import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, test } from "vitest";

import { PageOrientation } from "./PageOrientation";

describe("PageOrientation", () => {
  test("renders the four common orientation sections and next links", () => {
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
    expect(screen.getByRole("heading", { name: "このページで分かること" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "読み方" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "前提・限界" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "次に見る" })).toBeVisible();
    expect(screen.getByRole("link", { name: "Map →" })).toHaveAttribute("href", "/map");
  });
});
