import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import NewtonRootResidual from "./Figure";

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
