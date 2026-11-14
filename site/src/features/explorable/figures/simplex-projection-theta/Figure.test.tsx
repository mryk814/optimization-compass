import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import SimplexProjectionTheta from "./Figure";

afterEach(cleanup);

const slider = (name: RegExp) => screen.getByRole("slider", { name });

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
