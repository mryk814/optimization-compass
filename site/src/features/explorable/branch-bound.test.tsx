import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import BranchBound from "./BranchBound";

afterEach(cleanup);
const click = (name: string) => fireEvent.click(screen.getByRole("button", { name }));
const select = (title: string) => {
  fireEvent.click(screen.getByRole("button", { name: new RegExp(`^${title}、この枝の上限`) }));
  return within(screen.getByRole("article", { name: `${title}の候補` }));
};
// The first action splits the root on its fractional item, whose name the button carries.
const beginName = /を入れる／入れないで比べる$/;
const seed = (names: string[]) => {
  for (const name of names) fireEvent.click(screen.getByRole("checkbox", { name: new RegExp(`^${name} `) }));
  fireEvent.click(screen.getByRole("button", { name: beginName }));
};
it("names the first split after the root's fractional item and shrinks the bound at once", () => {
  const { container } = render(<BranchBound />); seed(["A", "B"]);
  expect(screen.getByText("13 ≤ 最適値 ≤ 15")).toBeVisible();
  expect(container.querySelector(".bnb-change")).toHaveTextContent("端数のBで二つに分けました。");
  expect(container.querySelector(".bnb-change")).toHaveTextContent("上限 15.34 → 15");
  expect(container.querySelector(".bnb-split-result")).toHaveTextContent("分けた品 B");
  expect(container.querySelector(".bnb-split-result")).toHaveTextContent("親の上限 15.34 点は 15 点まで下がりました");
  expect(container.querySelector(".bnb-range-ghost")).not.toBeNull();
  expect(container.querySelector(".bnb-dropped")).toHaveTextContent("15");
});
it("shows one detailed bag, keeps all candidates selectable, and preserves the bound explanation", () => {
  const { container } = render(<BranchBound />); seed(["A", "B"]);
  expect(screen.getAllByRole("article")).toHaveLength(1);
  expect(container.querySelectorAll(".bnb-candidate-summary")).toHaveLength(2);
  expect(container.querySelectorAll(".bnb-candidate .bnb-packing .bnb-object")).toHaveLength(1);
  expect(container.querySelector(".bnb-decisions")).toBeNull();
  const withB = select("Bあり");
  expect(withB.getByRole("progressbar", { name: "袋の重量" })).toHaveAttribute("value", "3");
  expect(container.querySelector(".bnb-candidate .bnb-bag-value")).toHaveTextContent("固定品の得点5点");
  expect(withB.getByText("未決定 3品")).toBeVisible();
  fireEvent.click(withB.getByText("上限の根拠"));
  fireEvent.click(withB.getByRole("button", { name: "この枝は終了できる？" }));
  expect(withB.getByRole("status")).toHaveTextContent("まだ調べ終えられません");
  const withoutB = select("Bなし");
  expect(withoutB.getByRole("progressbar", { name: "Cの詰めた割合" })).toHaveAttribute("value", "0.4");
  click("C 入れる／入れない");
  const withC = select("Bなし・Cあり");
  expect(withC.getByRole("progressbar", { name: "Aの詰めた割合" })).toHaveAttribute("value", "0.75");
  fireEvent.click(withC.getByRole("button", { name: "この枝を終える" }));
  expect(container.querySelector('[data-summary-id="2:0,3:1"]')).toBeNull();
  expect(container.querySelector('[data-branch-id="2:0,3:1"]')).toHaveTextContent("終了：記録以下");
  expect(container.querySelector(".bnb-finished")).toHaveTextContent("上限 12 ≤ 記録 13");
  click("一手戻す");
  expect(screen.getByRole("article", { name: "Bなし・Cありの候補" })).toBeVisible();
  expect(container.querySelector('[data-summary-id="2:0,3:1"]')).toHaveAttribute("aria-pressed", "true");
  click("同じ組合せで再実行");
  expect(container.querySelectorAll(".bnb-candidate-summary")).toHaveLength(2);
  click("品選びからやり直す");
  expect(screen.getAllByRole("checkbox").every((box) => !(box as HTMLInputElement).checked)).toBe(true);
});
it("retains inherited conditions and routes diagram selection to the shared detailed card", () => {
  const { container } = render(<BranchBound />); seed(["A", "B"]);
  const diagram = () => container.querySelector(".bnb-branch-focus")!;
  expect(diagram().querySelectorAll(".bnb-branch-node")).toHaveLength(3);
  expect(diagram().querySelector(".bnb-bag")).toBeNull();
  const jump = within(diagram() as HTMLElement).getByRole("button", { name: "Bなし：未決定 3品の候補へ" });
  expect(jump).toHaveAttribute("aria-controls", "bnb-selected-candidate");
  fireEvent.click(jump);
  expect(document.activeElement).toBe(screen.getByRole("article", { name: "Bなしの候補" }));
  click("C 入れる／入れない");
  select("Bなし・Cあり"); click("この枝を終える");
  expect(diagram().querySelector('[data-branch-id="2:0,3:1"]')).toHaveTextContent("終了：記録以下");
  select("Bあり"); click("D 入れる／入れない");
  expect(diagram().querySelectorAll(".bnb-branch-node")).toHaveLength(5);
  select("Bあり・Dあり"); click("A 入れる／入れない");
  expect(diagram().querySelector(".bnb-branch-parent")).toHaveTextContent("B✓分けた");
  select("Bあり・Dあり・Aあり");
  expect(container.querySelector(".bnb-candidate .bnb-capacity")).toHaveTextContent("容量超過 1");
  click("この枝を終える");
  expect(diagram().querySelector('[data-branch-id="0:1,1:1,2:1"]')).toHaveTextContent("終了：容量超過");
  click("一手戻す");
  expect(screen.getByRole("article", { name: "Bあり・Dあり・Aありの候補" })).toBeVisible();
  expect(diagram().querySelector('[data-branch-id="0:1,1:1,2:1"]')).toHaveAttribute("data-branch-state", "pending");
});
it("separates a partial bag's value from the incumbent and shares the eight-item catalog", () => {
  const { container } = render(<BranchBound />);
  fireEvent.click(screen.getByRole("radio", { name: "発展・8品" }));
  expect(screen.getByRole("button", { name: "Eを入れる／入れないで比べる" })).toBeVisible();
  seed(["A", "B", "G"]);
  const detailed = select("Eあり");
  expect(container.querySelectorAll(".bnb-candidate-summary")).toHaveLength(2);
  expect(screen.getAllByRole("article")).toHaveLength(1);
  expect(container.querySelector(".bnb-candidate .bnb-bag-value")).toHaveTextContent("固定品の得点6点");
  expect(container.querySelector(".bnb-candidate .bnb-capacity")).toHaveTextContent("容量使用 4 / 10残り 6");
  expect(detailed.getByRole("progressbar", { name: "袋の重量" })).toHaveAttribute("value", "4");
  expect(container.querySelector(".bnb-candidate .bnb-ceiling")).toHaveTextContent("この枝の上限18点> 全体最高記録 16点");
  expect(container.querySelectorAll(".bnb-candidate .bnb-packing .bnb-object")).toHaveLength(1);
  fireEvent.click(screen.getByText("品の重さと得点（8品）"));
  expect(container.querySelectorAll(".bnb-catalog-items > div")).toHaveLength(8);
  expect(container.querySelector(".bnb-candidate")).not.toHaveTextContent("重さ4");
  fireEvent.click(detailed.getByText("未決定 7品"));
  expect(container.querySelectorAll(".bnb-undecided .bnb-object")).toHaveLength(7);
  click("A・D・Eを記録（18点）");
  expect(container.querySelector(".bnb-recorded .bnb-packed")).toHaveTextContent("ADE");
  expect(container.querySelector(".bnb-recorded .bnb-bag-value")).toHaveTextContent("袋の得点18点");
  expect(container.querySelector('[data-branch-id="3:1"]')).toHaveTextContent("終了：記録更新");
});
it("proves both optima, restores selected branches on undo, and clears selections on reset and mode changes", () => {
  const { container } = render(<BranchBound />);
  for (const [mode, names, optimum] of [["入門・4品", ["A", "B"], 13], ["発展・8品", ["A", "D", "B"], 18]] as const) {
    fireEvent.click(screen.getByRole("radio", { name: mode }));
    seed([...names]);
    let steps = 0;
    while (container.querySelector(".bnb-candidate")) {
      fireEvent.click(container.querySelector(".bnb-candidate .ex-action")!);
      expect(++steps).toBeLessThan(80);
      expect(container.querySelectorAll(".bnb-candidate").length).toBeLessThanOrEqual(1);
    }
    expect(screen.getByText(`${optimum} ≤ 最適値 ≤ ${optimum}`)).toBeVisible();
    click("一手戻す");
    expect(screen.getAllByRole("article")).toHaveLength(1);
    expect(container.querySelectorAll('[data-summary-id][aria-pressed="true"]')).toHaveLength(1);
    click("同じ組合せで再実行");
    expect(container.querySelectorAll(".bnb-candidate-summary")).toHaveLength(2);
    click("品選びからやり直す");
    expect(container.querySelector(".bnb-branch-focus")).toBeNull();
    expect(container.querySelector(".bnb-candidate")).toBeNull();
  }
  fireEvent.click(screen.getByRole("radio", { name: "入門・4品" }));
  expect(screen.getAllByRole("checkbox")).toHaveLength(4);
  expect(screen.getByRole("progressbar", { name: "袋の重量" })).toHaveAttribute("max", "8");
});
it("blocks an overweight seed", () => {
  render(<BranchBound />);
  for (const box of screen.getAllByRole("checkbox")) fireEvent.click(box);
  expect(screen.getByRole("button", { name: beginName })).toBeDisabled();
  expect(screen.getByText(/容量超過です/)).toBeVisible();
});

it("separates an already optimal seed from the remaining proof", () => {
  const { container } = render(<BranchBound />);
  for (const [mode, names, optimum] of [["入門・4品", ["A", "B"], 13], ["発展・8品", ["A", "D", "E"], 18]] as const) {
    fireEvent.click(screen.getByRole("radio", { name: mode }));
    seed([...names]);
    expect(screen.getByText(new RegExp(`選んだ袋の${optimum}点は記録です`))).toBeVisible();
    expect(container.querySelector(".bnb-candidate")).not.toBeNull();
    let steps = 0;
    while (container.querySelector(".bnb-candidate")) {
      fireEvent.click(container.querySelector(".bnb-candidate .ex-action")!);
      expect(++steps).toBeLessThan(80);
    }
    expect(screen.getByText(`${optimum} ≤ 最適値 ≤ ${optimum}`)).toBeVisible();
    expect(screen.getByText(/最初に選んだ袋が最適でした/)).toBeVisible();
  }
});
it("proves the four-item example with four presses of the selected card after the first split", () => {
  const { container } = render(<BranchBound />); seed(["A", "B"]);
  for (let press = 0; press < 4; press += 1) fireEvent.click(container.querySelector(".bnb-candidate .ex-action")!);
  expect(screen.getByText("13 ≤ 最適値 ≤ 13")).toBeVisible();
  expect(screen.getAllByText(/最適性を証明できました/).length).toBeGreaterThan(0);
});
it("shows the fractional item inline, then lowers the upper bound step by step", () => {
  const { container } = render(<BranchBound />); seed(["A", "B"]);
  const withB = select("Bあり");
  expect(withB.getByText("端数")).toBeVisible();
  expect(withB.getByText("次に分ける")).toBeVisible();
  expect(container.querySelector(".bnb-fill .is-fractional")).toHaveTextContent("D");
  expect(container.querySelector(".bnb-split-preview")).toHaveTextContent("下がりません");
  click("D 入れる／入れない");
  expect(container.querySelector(".bnb-split-result")).toHaveTextContent("分けた品 D");
  expect(container.querySelector(".bnb-split-result")).toHaveTextContent("親と同じ 15 点のまま");
  expect(container.querySelector(".bnb-range-ghost")).toBeNull();

  select("Bあり・Dあり");
  expect(container.querySelector(".bnb-split-preview")).toHaveTextContent("入れるなら 容量超過、入れないなら 上限 12.6 点");
  expect(container.querySelector(".bnb-split-preview")).toHaveTextContent("15 点から 12.6 点へ下がります");
  click("A 入れる／入れない");
  expect(container.querySelector(".bnb-split-result")).toHaveTextContent("端数だった品 A");
  expect(container.querySelector(".bnb-split-result")).toHaveTextContent("下がりました");
  expect(container.querySelector(".bnb-range-ghost")).not.toBeNull();
  expect(container.querySelector(".bnb-dropped")).toHaveTextContent("14.4");
});
