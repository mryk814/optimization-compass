import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { EXPLORABLE_META } from "../../figureMeta";
import { numberSetting } from "../../scene";
import LeastSquaresBowl from "./Figure";
import { evaluateLine, fitLine } from "./math";

afterEach(cleanup);

const ARTICLE_POINTS = [{ t: 0, y: 1 }, { t: 1, y: 2 }, { t: 2, y: 2 }, { t: 3, y: 4 }];

describe("LeastSquaresBowl guided scene", () => {
  const beats = EXPLORABLE_META["least-squares-bowl"].beats;
  const pointsOf = (index: number) => ARTICLE_POINTS.map((p, i) => ({ ...p, y: numberSetting(beats[index].settings, `y${i}`, p.y) }));

  it("says only what each beat's computation shows", () => {
    const manual = evaluateLine(ARTICLE_POINTS, {
      a: numberSetting(beats[0].settings, "a", 0),
      b: numberSetting(beats[0].settings, "b", 0),
    });
    expect(manual.sse).toBeCloseTo(1.66, 10);

    const best = fitLine(pointsOf(1))!;
    expect([best.a, best.b].map((v) => Number(v.toFixed(10)))).toEqual([0.9, 0.9]);

    const pulled = fitLine(pointsOf(2))!;
    expect(numberSetting(beats[2].settings, "y3", 0)).toBe(8);
    expect([pulled.a, pulled.b].map((v) => Number(v.toFixed(10)))).toEqual([0.1, 2.1]);
  });
});

describe("LeastSquaresBowl", () => {
  it("starts with a hand-drawn line that is not the bottom of the bowl", () => {
    render(<LeastSquaresBowl />);
    expect(screen.getAllByText(/まだ底ではありません/).length).toBeGreaterThan(0);
  });

  it("snaps to the least-squares line and reports zero residual sums", () => {
    render(<LeastSquaresBowl />);
    fireEvent.click(screen.getByRole("radio", { name: "二乗和が最小の直線" }));
    expect(screen.getAllByText(/お椀の底です/).length).toBeGreaterThan(0);
    expect(screen.getAllByText("0.700").length).toBeGreaterThan(0);
    const totals = screen.getByRole("rowheader", { name: "合計" }).closest("tr");
    expect(totals?.querySelectorAll("td")).toHaveLength(2);
    expect(totals?.textContent).toBe("合計0.000.00");
  });

  it("moves a data point with the keyboard and refits", () => {
    render(<LeastSquaresBowl />);
    fireEvent.click(screen.getByRole("radio", { name: "二乗和が最小の直線" }));
    const fourth = screen.getByRole("slider", { name: /^点4（/ });
    for (let press = 0; press < 4; press += 1) fireEvent.keyDown(fourth, { key: "ArrowUp", shiftKey: true });
    expect(screen.getAllByText(/y = 0\.10 \+ 2\.10 t/).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: "点と直線を最初に戻す" }));
    expect(screen.getByRole("slider", { name: /^点4（/ })).toHaveAttribute("aria-valuenow", "4");
    expect(screen.getByRole("radio", { name: "自分で動かす" })).toBeChecked();
  });
});
