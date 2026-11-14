import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { CompiledContent } from "../content/CompiledContent";

afterEach(cleanup);

describe("ExplorableMounts inside compiled content", () => {
  const figure = (id: string) => `<figure class="explorable" role="group" data-explorable-id="${id}" aria-label="図">`
    + '<div class="explorable-mount" data-explorable-mount><p class="explorable-fallback">静的な代替</p></div>'
    + '<figcaption class="explorable-caption"><p>説明</p></figcaption></figure>';

  it("replaces the static fallback with the live figure and keeps the caption", async () => {
    render(<MemoryRouter><CompiledContent page={{ html: figure("convexity-chord"), toc: [] }} /></MemoryRouter>);

    expect(await screen.findByText("見る問い")).toBeInTheDocument();
    expect(screen.queryByText("静的な代替")).not.toBeInTheDocument();
    expect(screen.getByText("説明")).toBeInTheDocument();
  });

  it("preserves the live figure on an unchanged article rerender", async () => {
    const page = { html: figure("convexity-chord"), toc: [] };
    const view = render(<MemoryRouter><CompiledContent page={page} /></MemoryRouter>);
    const liveFigure = await screen.findByText("見る問い");
    expect(liveFigure).toBeInTheDocument();
    view.rerender(<MemoryRouter><CompiledContent page={page} /></MemoryRouter>);
    expect(screen.queryByText("静的な代替")).not.toBeInTheDocument();
    expect(screen.getByText("見る問い")).toBe(liveFigure);

    view.rerender(<MemoryRouter><CompiledContent page={{
      html: figure("convexity-chord").replace("説明", "更新された説明"), toc: [],
    }} /></MemoryRouter>);
    expect(await screen.findByText("見る問い")).toBeInTheDocument();
    expect(screen.getByText("更新された説明")).toBeInTheDocument();
    expect(screen.queryByText("説明", { exact: true })).not.toBeInTheDocument();
    expect(screen.queryByText("静的な代替")).not.toBeInTheDocument();
  });

  it("leaves the fallback for an id the site does not know", () => {
    render(<MemoryRouter><CompiledContent page={{ html: figure("not-registered"), toc: [] }} /></MemoryRouter>);

    expect(screen.getByText("静的な代替")).toBeInTheDocument();
  });
});
