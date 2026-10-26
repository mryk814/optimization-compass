import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import GaussNewtonLm from "./GaussNewtonLm";

afterEach(cleanup);

describe("GaussNewtonLm", () => {
  it("shows the Gauss–Newton overshoot at trial 2 from the far start", () => {
    render(<GaussNewtonLm />);
    fireEvent.click(screen.getByRole("button", { name: "1つ進む" }));
    fireEvent.click(screen.getByRole("button", { name: "1つ進む" }));

    expect(screen.getAllByText(/Gauss–Newton法の試行2。λ=0、予測した減少 2\.589 に対して実際の減少は −26\.451、ρ=−10\.22/u).length).toBeGreaterThan(0);
  });

  it("Levenberg–Marquardt rejects trial 2 and raises λ tenfold", () => {
    render(<GaussNewtonLm />);
    fireEvent.click(screen.getByRole("radio", { name: "Levenberg–Marquardt法" }));
    fireEvent.click(screen.getByRole("button", { name: "1つ進む" }));
    fireEvent.click(screen.getByRole("button", { name: "1つ進む" }));

    expect(screen.getAllByText(/Levenberg–Marquardt法の試行2。λ=0\.0033.*ρ=−9\.42。捨てました/u).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/次は λ=0\.033 で試します/u).length).toBeGreaterThan(0);
  });

  it("keeps the Gauss–Newton path as a ghost only in Levenberg–Marquardt mode", () => {
    const { container } = render(<GaussNewtonLm />);
    const toggle = screen.getByRole("checkbox", { name: "GNの軌跡を残す" });
    expect((toggle as HTMLInputElement).disabled).toBe(true);
    fireEvent.click(screen.getByRole("radio", { name: "Levenberg–Marquardt法" }));
    expect((toggle as HTMLInputElement).disabled).toBe(false);
    expect(container.querySelector(".gl-ghost")).toBeNull();
    fireEvent.click(toggle);
    expect(container.querySelectorAll(".gl-ghost").length).toBe(2);
    expect(screen.getByText("GNの軌跡")).toBeTruthy();
  });

  it("draws rejected trials as ✕ in the cost history while the accepted line stays flat", async () => {
    const { container } = render(<GaussNewtonLm />);
    fireEvent.click(screen.getByRole("radio", { name: "Levenberg–Marquardt法" }));
    for (let i = 0; i < 4; i += 1) fireEvent.click(screen.getByRole("button", { name: "1つ進む" }));
    const figure = screen.getByText("費用の履歴（対数目盛り）").closest("figure")!;
    await waitFor(() => expect(figure.querySelectorAll(".gl-reject").length).toBe(3), { timeout: 8000 });
    expect(container.querySelectorAll(".gl-hist-dot").length).toBeGreaterThan(0);
  }, 10000);
});
