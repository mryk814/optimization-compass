import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import SaddleNewton from "./SaddleNewton";

afterEach(cleanup);

describe("SaddleNewton", () => {
  it("follows the article: start A reaches the left valley in 6 steps with both curvatures positive", () => {
    render(<SaddleNewton />);

    expect(
      screen.getAllByText(/始点 \(0\.50, 1\.00\) から6回で谷底 \(−1\.031, 0\.258\)（f=−0\.129）.*3\.80 と 8\.95と二つとも正/u).length,
    ).toBeGreaterThan(0);
  });

  it("start B stops on the saddle, where the curvatures have mixed signs", () => {
    render(<SaddleNewton />);

    fireEvent.click(screen.getByRole("radio", { name: "始点B (0.2, 0.1)" }));

    expect(screen.getAllByText(/3回で峠 \(0\.000, 0\.000\)（f=1\.000）.*−4\.12 と 4\.12と符号が混ざる/u).length).toBeGreaterThan(0);
  });

  it("moves the start with the keyboard and offers it as a placed point", () => {
    render(<SaddleNewton />);
    const handle = screen.getByRole("group", { name: /始点 \(0\.50, 1\.00\)/u });

    fireEvent.keyDown(handle, { key: "ArrowRight", shiftKey: true });
    fireEvent.keyDown(handle, { key: "ArrowRight", shiftKey: true });
    fireEvent.keyDown(handle, { key: "ArrowDown", shiftKey: true });
    fireEvent.keyDown(handle, { key: "ArrowDown", shiftKey: true });
    fireEvent.keyDown(handle, { key: "ArrowDown", shiftKey: true });
    fireEvent.keyDown(handle, { key: "ArrowDown", shiftKey: true });
    fireEvent.keyDown(handle, { key: "ArrowDown", shiftKey: true });

    expect(screen.getByRole("radio", { name: /置いた点 \(0\.90, 0\.00\)/u })).toBeTruthy();
    expect(screen.getAllByText(/谷底 \(1\.031, −0\.258\)/u).length).toBeGreaterThan(0);
  });
});
