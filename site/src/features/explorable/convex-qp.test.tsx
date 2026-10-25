import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import ConvexQpProjection from "./ConvexQpProjection";

afterEach(cleanup);

/** Changing a control replays the motion; jump to the settled state like a reader pressing the last-step button. */
function settle() {
  fireEvent.click(screen.getByRole("button", { name: "最後まで進める" }));
}

describe("ConvexQpProjection", () => {
  it("follows the article: (2, 1), objective 2, λ = 2, vertices alone give 4", () => {
    render(<ConvexQpProjection />);

    expect(
      screen.getAllByText(/最も近い点は \(2\.00, 1\.00\)、目的値は 2\.00 です。合計の上限 x₁\+x₂ ≤ b が効いていて λ は 2\.00 です。辺の途中が答えで、頂点だけを比べると最小が 4\.00 になり 2\.00 だけ取り逃がします/u).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText(/予測が 0\.200、解き直した値が 0\.195/u)).toBeTruthy();
  });

  it("p = (1, 1) is inside: no constraint is active", () => {
    render(<ConvexQpProjection />);

    fireEvent.change(screen.getByRole("slider", { name: /目標の x₁ 座標/u }), { target: { value: "1" } });
    fireEvent.change(screen.getByRole("slider", { name: /目標の x₂ 座標/u }), { target: { value: "1" } });
    settle();

    expect(screen.getAllByText(/目標が領域の内部にあるので、目標そのものが答え/u).length).toBeGreaterThan(0);
  });

  it("p = (5, 0) lands on the vertex (3, 0) with two active constraints", () => {
    render(<ConvexQpProjection />);

    fireEvent.change(screen.getByRole("slider", { name: /目標の x₁ 座標/u }), { target: { value: "5" } });
    fireEvent.change(screen.getByRole("slider", { name: /目標の x₂ 座標/u }), { target: { value: "0" } });
    settle();

    expect(
      screen.getAllByText(/最も近い点は \(3\.00, 0\.00\)、目的値は 4\.00 です。2本の制約（合計の上限 x₁\+x₂ ≤ b、x₂ ≥ 0）が同時に効く頂点/u).length,
    ).toBeGreaterThan(0);
  });

  it("b = 5 puts the target (3, 2) on the boundary with multiplier 0", () => {
    render(<ConvexQpProjection />);

    fireEvent.change(screen.getByRole("slider", { name: /合計の上限 b/u }), { target: { value: "5" } });
    settle();

    expect(screen.getAllByText("境界上だが λ = 0").length).toBeGreaterThan(0);
  });
});
