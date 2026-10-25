import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import VariableDomain from "./VariableDomain";

afterEach(cleanup);

function pick(legend: RegExp, label: string) {
  const group = screen.getByRole("group", { name: legend });
  const radio = Array.from(group.querySelectorAll("label")).find((item) => item.textContent === label);
  if (!radio) throw new Error(`no option ${label}`);
  fireEvent.click(radio.querySelector("input") as HTMLInputElement);
}

describe("VariableDomain", () => {
  it("starts continuous: vertex (3, 1.5), profit 21", () => {
    render(<VariableDomain />);
    expect(screen.getAllByText(/頂点 \(3\.00, 1\.50\)、利益 21\.00/u).length).toBeGreaterThan(0);
  });

  it("integer x integer: (4, 0)=20 against the relaxation 21, gap 1", () => {
    render(<VariableDomain />);
    pick(/x₁ の定義域/u, "整数");
    pick(/x₂ の定義域/u, "整数");
    expect(screen.getAllByText(/最適解は \(4, 0\)、利益 20。連続に戻した緩和の最適値は 21\.00 で、差は 1\.00/u).length).toBeGreaterThan(0);
    expect(screen.getByText("候補は 13 点。全部調べた")).toBeTruthy();
  });

  it("0/1 x 0/1: (1, 1)=9 and the relaxation agrees", () => {
    render(<VariableDomain />);
    pick(/x₁ の定義域/u, "0か1");
    pick(/x₂ の定義域/u, "0か1");
    expect(screen.getAllByText(/最適解は \(1, 1\)、利益 9。連続に戻した緩和の最適値 9\.00 と同じ/u).length).toBeGreaterThan(0);
    expect(screen.getByText("候補は 4 点。全部調べた")).toBeTruthy();
  });

  it("x1 integer, x2 continuous: the optimum (3, 1.5) is reachable, gap 0", () => {
    render(<VariableDomain />);
    pick(/x₁ の定義域/u, "整数");
    expect(screen.getAllByText(/最適解は \(3\.00, 1\.50\)、利益 21\.00。連続に戻した緩和の最適値 21\.00 と同じ/u).length).toBeGreaterThan(0);
  });
});
