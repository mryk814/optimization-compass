import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

afterEach(cleanup);

describe("RobustLossPull", () => {
  it("opens on the article's example: 2.5 for squared, 1/3 for Huber", async () => {
    const { default: RobustLossPull } = await import("./Figure");
    render(<RobustLossPull />);
    const summary = document.querySelector(".ex-sr-only")?.textContent ?? "";
    expect(summary).toContain("二乗損失の当てはめは2.500");
    expect(summary).toContain("Huber損失（尺度1.00）の当てはめは0.333");
    expect(screen.getByRole("slider", { name: /最後の観測の値/ })).toBeTruthy();
    expect(screen.getByRole("slider", { name: /Huberの尺度/ })).toBeTruthy();
  });
});
