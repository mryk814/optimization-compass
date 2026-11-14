import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import PsdSliceBoundary from "./Figure";

afterEach(cleanup);

const slider = (name: RegExp) => screen.getByRole("slider", { name });

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
