import { cleanup, fireEvent, render, screen } from "@testing-library/react";
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
});
