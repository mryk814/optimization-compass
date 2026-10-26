import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import NewtonRootResidual from "./NewtonRootResidual";
import PdeHeatSourceBalance from "./PdeHeatSourceBalance";
import PsdSliceBoundary from "./PsdSliceBoundary";
import SimplexProjectionTheta from "./SimplexProjectionTheta";

afterEach(cleanup);

const slider = (name: RegExp) => screen.getByRole("slider", { name });

describe("NewtonRootResidual", () => {
  it("opens on the finished three steps and the residual falls 7.82e-6 → 1.22e-11 on the last", () => {
    render(<NewtonRootResidual />);
    expect(screen.getAllByText(/7\.82e-6 から 1\.22e-11/).length).toBeGreaterThan(0);
  });

  it("steps one move at a time: the first step starts at 0.7 and lands on 0.620833", () => {
    render(<NewtonRootResidual />);
    fireEvent.click(screen.getByRole("button", { name: "最初から" }));
    fireEvent.click(screen.getByRole("button", { name: "1つ進む" }));
    expect(screen.getAllByText(/t₁ = 0\.620833/).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: "1つ進む" }));
    expect(screen.getAllByText(/t₂ = 0\.618037/).length).toBeGreaterThan(0);
  });

  it("switches to bisection, where the bracket halves and residual need not fall", () => {
    render(<NewtonRootResidual />);
    fireEvent.click(screen.getByRole("radio", { name: /二分法/ }));
    expect(screen.getByText(/残差 \|F\| は回ごとに減るとは限りません/)).toBeInTheDocument();
    expect(screen.queryByRole("slider", { name: /始点/ })).not.toBeInTheDocument();
  });

  it("labels the zoom factor and drops it when zoom is off", () => {
    render(<NewtonRootResidual />);
    expect(screen.getByText(/根の周りを ×/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("radio", { name: /拡大しない/ }));
    expect(screen.getByText(/拡大なし/)).toBeInTheDocument();
  });
});

describe("NewtonRootResidual plane panel", () => {
  it("draws the plane with three starts and names the point where the step is undefined", () => {
    render(<NewtonRootResidual />);
    expect(screen.getByText(/二変数の平面 \(x₁, x₂\)/)).toBeInTheDocument();
    expect(screen.getByText(/特異点 \(0\.5, 0\.5\)/)).toBeInTheDocument();
  });

  it("stops the diagonal start at the singular point when t₀ = 0.5", () => {
    render(<NewtonRootResidual />);
    fireEvent.change(slider(/始点/), { target: { value: "0.5" } });
    expect(screen.getByText(/その点なので、橙の印は動きません/)).toBeInTheDocument();
  });

  it("names the icon buttons next to their icons", () => {
    render(<NewtonRootResidual />);
    expect(screen.getByRole("button", { name: "1つ進む" })).toHaveTextContent("▶ 1つ進む");
    expect(screen.getByRole("button", { name: "▶ 再生" })).toBeInTheDocument();
  });

  it("hides the plane in bisection mode", () => {
    render(<NewtonRootResidual />);
    fireEvent.click(screen.getByRole("radio", { name: /二分法/ }));
    expect(screen.queryByText(/二変数の平面 \(x₁, x₂\)/)).not.toBeInTheDocument();
  });
});

describe("SimplexProjectionTheta triangle panel", () => {
  it("draws the triangle with y's shadow and the distance to the projection", () => {
    render(<SimplexProjectionTheta />);
    expect(screen.getByText(/三角形（合計 1 の領域）の上の動き/)).toBeInTheDocument();
    expect(screen.getByText(/影から射影までの距離は 0\.041/)).toBeInTheDocument();
  });

  it("adds the divided point and a longer distance when the comparison is on", () => {
    render(<SimplexProjectionTheta />);
    fireEvent.click(screen.getByRole("radio", { name: /合計で割った配分/ }));
    expect(screen.getByText(/^割った配分$/)).toBeInTheDocument();
    expect(screen.getByText(/辺に直角ではありません/)).toBeInTheDocument();
  });

  it("switches between the zoomed edge and the whole triangle", () => {
    render(<SimplexProjectionTheta />);
    expect(screen.getByText(/確認 = 0 の辺/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("radio", { name: /三角形全体/ }));
    expect(screen.queryByText(/確認 = 0 の辺$/)).not.toBeInTheDocument();
  });
});

describe("SimplexProjectionTheta", () => {
  it("opens with the total back at 1 and the article's allocation", () => {
    render(<SimplexProjectionTheta />);
    expect(screen.getAllByText(/合計が 1 に戻りました/).length).toBeGreaterThan(0);
    expect(screen.getAllByText("0.800").length).toBeGreaterThan(0);
    expect(screen.getAllByText("0.01805").length).toBeGreaterThan(0);
  });

  it("subtracting too little leaves a total above 1, too much falls below", () => {
    render(<SimplexProjectionTheta />);
    fireEvent.change(slider(/引く量/), { target: { value: "0.05" } });
    expect(screen.getAllByText(/合計は 1\.100/).length).toBeGreaterThan(0);
    fireEvent.change(slider(/引く量/), { target: { value: "0.2" } });
    expect(screen.getAllByText(/合計は 0\.800/).length).toBeGreaterThan(0);
    fireEvent.change(slider(/引く量/), { target: { value: "0.1" } });
    expect(screen.getAllByText(/合計が 1 に戻りました/).length).toBeGreaterThan(0);
    expect(screen.getAllByText("0.01125").length).toBeGreaterThan(0);
  });
});

describe("PsdSliceBoundary", () => {
  it("is feasible inside, on the boundary at r = 2, and infeasible beyond with a negative eigenvalue", () => {
    render(<PsdSliceBoundary />);
    expect(screen.getAllByText(/半正定値（可行）/).length).toBeGreaterThan(0);
    fireEvent.change(slider(/共分散 r/), { target: { value: "2" } });
    expect(screen.getAllByText(/境界（可行で、固有値の一つが 0）/).length).toBeGreaterThan(0);
    fireEvent.change(slider(/共分散 r/), { target: { value: "3" } });
    expect(screen.getAllByText(/半正定値ではない/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/−0\.854/).length).toBeGreaterThan(0);
  });

  it("draws the objective −r and the eigenvalue sum and product 4 − r²", () => {
    render(<PsdSliceBoundary />);
    fireEvent.change(slider(/共分散 r/), { target: { value: "2.5" } });
    expect(screen.getAllByText(/−r = −2\.50/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/和 λ₁ \+ λ₂ = 5\.00/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/積 λ₁λ₂ = 4 − r² = −2\.25/).length).toBeGreaterThan(0);
  });

  it("names the icon buttons next to their icons", () => {
    render(<PsdSliceBoundary />);
    expect(screen.getByRole("button", { name: "1つ進む" })).toHaveTextContent("▶ 1つ進む");
  });
});

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
