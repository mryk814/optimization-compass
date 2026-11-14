import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import LpVertexWalk from "./Figure";

afterEach(cleanup);

function slider(name: RegExp) {
  return screen.getByRole("slider", { name });
}

describe("LpVertexWalk", () => {
  it("shows the bakery LP's optimum (4, 3) with revenue 24 and that vertices are enough", () => {
    render(<LpVertexWalk />);

    expect(screen.getAllByText(/最適解は頂点 \(4\.0, 3\.0\)、目的値は z=24/).length).toBeGreaterThan(0);
    const table = screen.getByRole("table");
    expect(within(table).getAllByRole("row")).toHaveLength(5);
    expect(within(table).getByText("最良")).toBeInTheDocument();
  });

  it("matches the article's numbered checks for c₂ = 1 and c₂ = 2", () => {
    render(<LpVertexWalk />);

    fireEvent.change(slider(/係数 c₂/), { target: { value: "1" } });
    expect(screen.getAllByText(/最適解は頂点 \(6\.0, 0\.0\)、目的値は z=18.*1回移って/).length).toBeGreaterThan(0);

    fireEvent.change(slider(/係数 c₂/), { target: { value: "2" } });
    expect(screen.getAllByText(/辺全体が最適です（z=18/).length).toBeGreaterThan(0);
  });

  it("reports a whole optimal edge when the cost is perpendicular to it", () => {
    render(<LpVertexWalk />);

    fireEvent.change(slider(/係数 c₁/), { target: { value: "1" } });
    fireEvent.change(slider(/係数 c₂/), { target: { value: "3" } });

    expect(screen.getAllByText(/辺全体が最適です/).length).toBeGreaterThan(0);
  });

  it("keeps the probe inside the feasible region when moved by keyboard", () => {
    render(<LpVertexWalk />);
    const probe = screen.getByRole("group", { name: /動かせる点/ });

    for (let press = 0; press < 30; press += 1) fireEvent.keyDown(probe, { key: "ArrowRight", shiftKey: true });

    const label = screen.getByRole("group", { name: /動かせる点/ }).getAttribute("aria-label") ?? "";
    const [, x, y] = /\(([\d.−-]+), ([\d.−-]+)\)/u.exec(label) ?? [];
    const [px, py] = [Number(x.replace("−", "-")), Number(y.replace("−", "-"))];
    expect(3 * px + 2 * py).toBeLessThanOrEqual(18.01);
    expect(px + 3 * py).toBeLessThanOrEqual(13.01);
  });
});
