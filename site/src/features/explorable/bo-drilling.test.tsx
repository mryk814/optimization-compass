import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import BayesOptAcquisition from "./BayesOptAcquisition";

afterEach(cleanup);
const drill = () => fireEvent.click(screen.getByRole("button", { name: "ここを掘る" }));
const compare = () => fireEvent.click(screen.getByRole("button", { name: "同じ観測でBOと比べる" }));

describe("learner's oil drilling", () => {
  it("starts with observations, with no model, proposal or answer curve", () => {
    render(<BayesOptAcquisition />);
    expect(screen.getByRole("slider", { name: /掘る場所 x/ })).toHaveValue("0.75");
    expect(screen.queryByRole("slider", { name: /探索の重み/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("checkbox", { name: /答え合わせ/ })).not.toBeInTheDocument();
    expect(document.querySelector(".ex-truth")).toBeNull();
  });
  it("returns the chosen point's result before offering optional reflection and BO", () => {
    render(<BayesOptAcquisition />);
    fireEvent.change(screen.getByRole("slider", { name: /掘る場所 x/ }), { target: { value: "0.85" } });
    drill();
    expect(screen.getByText(/いま掘った x=0.850/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("radio", { name: "まだ分からない土地" }));
    compare();
    expect(screen.getByText(/未知の土地を試す気持ちは/)).toBeInTheDocument();
    const observations = screen.getByRole("img").textContent;
    fireEvent.change(screen.getByRole("slider", { name: /探索の重み/ }), { target: { value: "0" } });
    expect(screen.getByRole("img").textContent).toBe(observations);
    expect(document.querySelector(".ex-truth")).toBeNull();
  });
  it("can skip reflection, undo a dig, and reset assumptions", () => {
    render(<BayesOptAcquisition />);
    drill(); compare();
    fireEvent.change(screen.getByRole("slider", { name: /探索の重み/ }), { target: { value: "8" } });
    fireEvent.click(screen.getByRole("button", { name: "一手戻す" }));
    expect(screen.getByText(/自分で掘った本数 0/)).toBeInTheDocument();
    drill(); compare();
    fireEvent.click(screen.getByRole("button", { name: "同じ土地でやり直す" }));
    drill(); compare();
    expect(screen.getByRole("slider", { name: /探索の重み/ })).toHaveValue("2");
  });
  it("caps the budget, gates the answer, and hides it after undo", () => {
    render(<BayesOptAcquisition />);
    for (let i = 0; i < 5; i += 1) {
      drill();
      if (i < 4) fireEvent.click(screen.getByRole("button", { name: "もう一本、自分で選ぶ" }));
    }
    compare();
    expect(screen.queryByRole("button", { name: "ここを掘る" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("checkbox", { name: /答え合わせ/ }));
    expect(document.querySelector(".ex-truth")).not.toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "一手戻す" }));
    expect(document.querySelector(".ex-truth")).toBeNull();
    expect(screen.getByRole("button", { name: "ここを掘る" })).toBeInTheDocument();
  });
});
