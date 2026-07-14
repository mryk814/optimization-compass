import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { TheaterIndexPage } from "./TheaterIndexPage";

describe("TheaterIndexPage", () => {
  test("offers each visualization family before entering an individual run", () => {
    render(<MemoryRouter><TheaterIndexPage /></MemoryRouter>);

    expect(screen.getByRole("heading", { level: 1, name: "Method Theater" })).toBeVisible();
    expect(screen.getByRole("link", { name: /Nelder–Meadの幾何操作を開く/u })).toHaveAttribute(
      "href",
      "/traces/nelder-mead-quadratic",
    );
    expect(screen.getByRole("link", { name: /Search-tree Theaterを開く/u })).toHaveAttribute(
      "href",
      "/theater/search-tree/binary-knapsack-bnb-complete",
    );
    expect(screen.getByRole("link", { name: /BO Theaterを開く/u })).toHaveAttribute(
      "href",
      "/theater/bayesian-optimization",
    );
  });
});
