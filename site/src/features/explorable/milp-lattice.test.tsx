import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import MilpLattice from "./MilpLattice";

afterEach(cleanup);

describe("MilpLattice", () => {
  it("follows the article: LP (3, 1.5)=21, the rounded (3, 2) breaks both limits, integer optimum (4, 0)=20", () => {
    render(<MilpLattice />);

    expect(
      screen.getAllByText(
        /LP緩和の最適解は \(3\.00, 1\.50\)、利益 21\.00 が上界です。丸めた点 \(3, 2\) は実行できません（資源1が2超過、資源2が1超過）。整数の最適解は \(4, 0\)で利益 20、上界との差は 1\.00/u,
      ).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText("実行できない（資源1が2超過、資源2が1超過）")).toBeTruthy();
  });

  it("b2=4 makes the LP optimum an integer point, so the gap is 0", () => {
    render(<MilpLattice />);

    fireEvent.change(screen.getByRole("slider", { name: /資源2の上限/u }), { target: { value: "4" } });

    expect(
      screen.getAllByText(/LP緩和の最適解 \(4, 0\) がもともと整数で、そのまま実行できます。利益は 20、上界との差は 0/u).length,
    ).toBeGreaterThan(0);
  });

  it("b1=23, b2=5: the rounded (3, 1)=19 is proven optimal because integer profits stay at most ⌊19.75⌋", () => {
    render(<MilpLattice />);

    fireEvent.change(screen.getByRole("slider", { name: /資源1の上限/u }), { target: { value: "23" } });
    fireEvent.change(screen.getByRole("slider", { name: /資源2の上限/u }), { target: { value: "5" } });

    expect(
      screen.getAllByText(/丸めた点 \(3, 1\) は実行できて利益 19、整数の最適解と一致しました。利益の係数が整数なので、整数解の利益は上界を切り捨てた 19 以下です。/u).length,
    ).toBeGreaterThan(0);
  });

  it("b2=7 widens the gap to 1.50 while the integer optimum stays 20", () => {
    render(<MilpLattice />);

    fireEvent.change(screen.getByRole("slider", { name: /資源2の上限/u }), { target: { value: "7" } });

    expect(screen.getAllByText(/\(2\.50, 2\.25\)、利益 21\.50 が上界.*利益 20、上界との差は 1\.50/u).length).toBeGreaterThan(0);
  });
});
