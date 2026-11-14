import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { LessonContext, type LessonDrive } from "../../lessonContext";
import type { BeatSettings } from "../../scene";
import TankShootingDefect from "./Figure";

afterEach(cleanup);

const DEFAULTS: BeatSettings = { iter: 0, flow: 1, cut: 0, fine: 0, substeps: "1", resolve: 1 };

function renderStep(settings: BeatSettings) {
  const drive: LessonDrive = {
    beats: [{ settings: { ...DEFAULTS, ...settings }, durationS: 6, captionJa: "", narrationJa: "" }],
    index: 0,
    local: 6,
    free: false,
  };
  return render(<LessonContext.Provider value={drive}><TankShootingDefect /></LessonContext.Provider>);
}

const statOf = (name: string) => screen.getByText(name).parentElement?.querySelector("dd")?.textContent;

describe("TankShootingDefect in free play", () => {
  it("opens on the initial guess: zero cost and five gaps of 376 L", () => {
    render(<TankShootingDefect />);
    expect(screen.getAllByText("+376 L")).toHaveLength(5);
    expect(screen.getByText("+32 L")).toBeInTheDocument();
    expect(statOf("継ぎ目で増えた水")).toBe("+1911 L");
    expect(statOf("最大残差")).toBe("0.376 m");
    expect(screen.getByText("許容値の外")).toBeInTheDocument();
  });

  it("measures a knot moved with the keyboard, and returns to the solver's plan on reset", () => {
    render(<TankShootingDefect />);
    const knot = screen.getByRole("slider", { name: /^結び目3の水位/ });
    fireEvent.keyDown(knot, { key: "ArrowUp", shiftKey: true });
    // Raising knot 3 by 5 cm widens its own gap and narrows the next one.
    expect(screen.getByRole("slider", { name: /^結び目3の水位/ })).toHaveAttribute("aria-valuenow", "0.55");
    expect(screen.getByText("+426 L")).toBeInTheDocument();
    expect(screen.getAllByText("+376 L")).toHaveLength(3);
    fireEvent.click(screen.getByRole("button", { name: "初期推定に戻す" }));
    expect(screen.getAllByText("+376 L")).toHaveLength(5);
  });

  it("raises a flow with the keyboard and counts the water the pump brings", () => {
    render(<TankShootingDefect />);
    fireEvent.keyDown(screen.getByRole("slider", { name: /^区間2の流量/ }), { key: "ArrowUp", shiftKey: true });
    expect(statOf("ポンプが入れる水")).toBe("75 L");
  });
});

describe("TankShootingDefect driven by a lesson step", () => {
  it("shows no gaps and no measured residual before the model's lines are drawn", () => {
    renderStep({ flow: 0 });
    expect(screen.queryByText("+376 L")).toBeNull();
    expect(statOf("最大残差")).toBe("—");
    expect(screen.queryByRole("slider")).toBeNull();
  });

  it("reports the numbers the steps of the article say", () => {
    renderStep({ iter: 1 });
    expect(screen.getByText("7.56")).toBeInTheDocument();
    expect(statOf("ポンプが入れる水")).toBe("1856 L");
    expect(statOf("最大残差")).toBe("6.5×10⁻⁵ m");
    expect(screen.getByText("許容値の外")).toBeInTheDocument();
    cleanup();

    renderStep({ iter: 3 });
    expect(screen.getByText("許容値の内")).toBeInTheDocument();
    expect(statOf("最大残差")).toMatch(/×10⁻¹² m$/);
    cleanup();

    renderStep({ iter: 3, cut: 4 });
    // Once on the level panel, at knot 4, and once as the total of the water that appeared.
    expect(screen.getAllByText("+300 L")).toHaveLength(2);
    expect(statOf("最大残差")).toBe("0.300 m");
    expect(statOf("二乗和の平方根")).toBe("0.300 m");
  });

  it("opens gaps when the one-step plan meets the five-step formula, and closes them on the re-solve", () => {
    renderStep({ iter: 4, substeps: "5", resolve: 0 });
    expect(screen.getByText("許容値の外")).toBeInTheDocument();
    expect(screen.getByText("0.168")).toBeInTheDocument();
    cleanup();

    renderStep({ iter: 4, substeps: "5", resolve: 1 });
    expect(screen.getByText("許容値の内")).toBeInTheDocument();
    expect(screen.getByText("0.010")).toBeInTheDocument();
  });
});
