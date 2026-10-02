import { StrictMode } from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { CompiledContent } from "../content/CompiledContent";

vi.mock("./PhysicalSceneFigure", () => ({
  default: ({ id }: { id: string }) => <div>計算例 {id}</div>,
}));

describe("article-owned computed figures", () => {
  it("embeds registered paragraph links once and preserves the prose and ordinary links", async () => {
    const html = '<p>配置の説明。<a href="#/theater/physical/topology">材料の計算例</a></p><p><a href="#/theater/physical/topology">同じ例へのリンク</a></p><p><a href="#/theater/physical/unknown">未登録の例</a></p>';
    const { container, rerender } = render(<MemoryRouter><StrictMode><CompiledContent page={{ html, toc: [] }} /></StrictMode></MemoryRouter>);
    expect(await screen.findByText("計算例 topology")).toBeVisible();
    expect(container.querySelectorAll(".physical-article-mount")).toHaveLength(1);
    expect(screen.getByRole("link", { name: "材料の計算例" })).toHaveAttribute("href", "#/theater/physical/topology");
    expect(screen.getByText(/配置の説明/u)).toBeVisible();
    expect(screen.getByRole("link", { name: "未登録の例" })).toBeVisible();
    rerender(<MemoryRouter><StrictMode><CompiledContent page={{ html: '<p><a href="#/theater/physical/arm">腕の計算例</a></p>', toc: [] }} /></StrictMode></MemoryRouter>);
    expect(await screen.findByText("計算例 arm")).toBeVisible();
    expect(screen.queryByText("計算例 topology")).not.toBeInTheDocument();
    expect(container.querySelectorAll(".physical-article-mount")).toHaveLength(1);
  });
});
