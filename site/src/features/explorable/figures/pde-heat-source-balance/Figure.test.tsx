import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import PdeHeatSourceBalance from "./Figure";

afterEach(cleanup);

const slider = (name: RegExp) => screen.getByRole("slider", { name });

describe("PdeHeatSourceBalance", () => {
  it("opens at q = 4.5 where misfit and penalty are both 0.250 and the total is 0.500", () => {
    render(<PdeHeatSourceBalance />);
    expect(screen.getAllByText(/0\.250 がちょうど釣り合い/).length).toBeGreaterThan(0);
  });

  it("reproduces the article's rows for q = 0 and 9", () => {
    render(<PdeHeatSourceBalance />);
    fireEvent.change(slider(/熱源の強さ q/), { target: { value: "0" } });
    expect(screen.getAllByText(/温度のずれ 1\.000 が罰則 0\.000 より大きく/).length).toBeGreaterThan(0);
    fireEvent.change(slider(/熱源の強さ q/), { target: { value: "9" } });
    expect(screen.getAllByText(/熱源の罰則 1\.000 がずれ 0\.000 より大きく/).length).toBeGreaterThan(0);
  });

  it("keeps the state residual at 0 when u is computed from q", () => {
    render(<PdeHeatSourceBalance />);
    expect(screen.getAllByText(/状態残差はいつも 0/).length).toBeGreaterThan(0);
  });

  it("in the free-u mode u = 1 with q = 0 looks perfect but breaks the state equation; only q = 9 fixes it", () => {
    render(<PdeHeatSourceBalance />);
    fireEvent.click(screen.getByRole("radio", { name: /u を自由に決める/ }));
    expect(screen.getAllByText(/状態残差 ‖Ku − q‖ が 12\.73/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/この u は実現できません/).length).toBeGreaterThan(0);
    fireEvent.change(slider(/熱源の強さ q/), { target: { value: "9" } });
    expect(screen.getAllByText(/状態残差は 0 です。合計は 1\.000/).length).toBeGreaterThan(0);
  });
});
