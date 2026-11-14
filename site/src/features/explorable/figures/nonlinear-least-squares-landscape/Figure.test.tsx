import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import NonlinearFitLandscape from "./Figure";

afterEach(cleanup);

describe("NonlinearFitLandscape", () => {
  it("steps the descent and shows the bowl's promise against the real sum of squares", () => {
    render(<NonlinearFitLandscape />);
    fireEvent.click(screen.getByRole("button", { name: "1手進める" }));
    const scrub = screen.getByLabelText("反復 k");

    fireEvent.change(scrub, { target: { value: "1" } });
    const panel = within(screen.getByRole("region", { name: "1手の予測と実際" }));
    expect(panel.getByText("1手目：お椀の予測と、実際の二乗和")).toBeTruthy();
    expect(panel.getByText("5.420")).toBeTruthy();
    expect(panel.getByText("0.245")).toBeTruthy();
    expect(panel.getByText("2.234")).toBeTruthy();
  });

  it("shows plain Gauss–Newton overshoot on the far start (ω = 3)", () => {
    render(<NonlinearFitLandscape />);
    fireEvent.change(screen.getByRole("slider", { name: /周波数 ω/ }), { target: { value: "3" } });
    fireEvent.click(screen.getByRole("button", { name: "この点から下る" }));
    fireEvent.change(screen.getByLabelText("反復 k"), { target: { value: "3" } });

    const panel = within(screen.getByRole("region", { name: "1手の予測と実際" }));
    expect(panel.getByText("3手目：お椀の予測と、実際の二乗和")).toBeTruthy();
    expect(panel.getByText(/お椀は 1\.737 減ると予測しました。実際は 1\.3e9 増えました/)).toBeTruthy();
  });
});

describe("NonlinearFitLandscape extras", () => {
  it("labels the clipped bar with its real size and ghosts the destination curve", () => {
    const { container } = render(<NonlinearFitLandscape />);
    fireEvent.change(screen.getByRole("slider", { name: /周波数 ω/ }), { target: { value: "3" } });
    fireEvent.click(screen.getByRole("button", { name: "この点から下る" }));
    fireEvent.change(screen.getByLabelText("反復 k"), { target: { value: "3" } });

    expect(screen.getByText("▶ 1.3e9")).toBeTruthy();
    expect(container.querySelector(".nls-ghost-curve")).toBeTruthy();
  });

  it("adds a λ column for Levenberg–Marquardt only", () => {
    render(<NonlinearFitLandscape />);
    fireEvent.click(screen.getByRole("radio", { name: "Levenberg–Marquardt" }));
    fireEvent.click(screen.getByRole("button", { name: "この点から下る" }));
    fireEvent.change(screen.getByLabelText("反復 k"), { target: { value: "2" } });
    expect(within(screen.getByRole("region", { name: "反復の記録" })).getByRole("columnheader", { name: "λ" })).toBeTruthy();
  });

  it("overlays the ω + 4π curve on request", () => {
    const { container } = render(<NonlinearFitLandscape />);
    expect(container.querySelector(".nls-alias-curve")).toBeNull();
    fireEvent.click(screen.getByRole("radio", { name: /ω\+4π の曲線を出す/ }));
    expect(container.querySelector(".nls-alias-curve")).toBeTruthy();
    expect(screen.getByText(/ω\+4π=14\.37/)).toBeTruthy();
  });
});

describe("NonlinearFitLandscape ω-profile", () => {
  it("draws five valleys and moves the start marker with the ω slider", () => {
    const { container } = render(<NonlinearFitLandscape />);
    expect(screen.getByText("ω ごとの最小の二乗和（a は ω ごとに最良）")).toBeTruthy();
    expect(container.querySelectorAll(".nls-profile-valley").length).toBe(5);
    const before = container.querySelector(".nls-profile-start")!.getAttribute("x1");
    fireEvent.change(screen.getByRole("slider", { name: /周波数 ω/ }), { target: { value: "4" } });
    expect(container.querySelector(".nls-profile-start")!.getAttribute("x1")).not.toBe(before);
    expect(screen.getByText(/いま 4\.00、値 13\.66/)).toBeTruthy();
  });

  it("titles the iteration table visibly", () => {
    render(<NonlinearFitLandscape />);
    fireEvent.click(screen.getByRole("button", { name: "この点から下る" }));
    fireEvent.change(screen.getByLabelText("反復 k"), { target: { value: "1" } });
    const region = within(screen.getByRole("region", { name: "反復の記録" }));
    expect(region.getByText("反復の記録")).toBeTruthy();
  });
});
