import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import InverseProblemAlpha from "./InverseProblemAlpha";
import { alphaText, sig } from "./format";

afterEach(cleanup);
const alphaSlider = () => screen.getByRole("slider", { name: /罰則の重み α/ });
const summary = () => document.querySelector(".ex-sr-only")?.textContent ?? "";

describe("inverse problem alpha figure", () => {
  it("formats numbers as the article prints them", () => {
    expect(sig(43.94)).toBe("43.9");
    expect(sig(0.0182)).toBe("0.0182");
    expect(sig(0.19)).toBe("0.190");
    expect(alphaText(1e-3)).toBe("1e−3");
    expect(alphaText(7.25e-4)).toBe("7.25e−4");
  });

  it("shows the article's error at the slider positions", () => {
    render(<InverseProblemAlpha />);
    fireEvent.change(alphaSlider(), { target: { value: "-10" } });
    expect(summary()).toContain("相対誤差は43.9");
    fireEvent.change(alphaSlider(), { target: { value: "-6" } });
    expect(summary()).toContain("相対誤差は0.612");
    fireEvent.change(alphaSlider(), { target: { value: "-3" } });
    expect(summary()).toContain("相対誤差は0.0182");
    expect(summary()).toContain("雑音の大きさ δ は0.00632");
    fireEvent.change(alphaSlider(), { target: { value: "-1" } });
    expect(summary()).toContain("相対誤差は0.190");
  });

  it("hides the truth and the error when the answer check is off", () => {
    render(<InverseProblemAlpha />);
    expect(document.querySelector(".ip-truth")).not.toBeNull();
    fireEvent.click(screen.getByRole("checkbox", { name: /真の分布を重ねる/ }));
    expect(document.querySelector(".ip-truth")).toBeNull();
    expect(summary()).toContain("誤差は表示しません");
    expect(screen.getByRole("img", { name: /相対誤差は非表示/ })).toBeInTheDocument();
  });

  it("names the side of the discrepancy level", () => {
    render(<InverseProblemAlpha />);
    fireEvent.change(alphaSlider(), { target: { value: "-6" } });
    expect(document.querySelector(".ex-verdict")?.textContent).toContain("雑音まで合わせすぎている側");
    fireEvent.change(alphaSlider(), { target: { value: "-1" } });
    expect(document.querySelector(".ex-verdict")?.textContent).toContain("観測の形まで削り始めている側");
  });
});
