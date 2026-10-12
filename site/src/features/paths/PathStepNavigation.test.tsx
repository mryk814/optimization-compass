import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, test, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { parseLearningPaths } from "../../contracts/learning-paths";
import rawPaths from "../../../public/data/learning-paths.json";
import { PathStepNavigation } from "./PathStepNavigation";

vi.mock("../formulations/formulation-data", () => ({
  loadLearningPaths: () => Promise.resolve(parseLearningPaths(rawPaths)),
}));

function Shell() {
  return (
    <>
      <PathStepNavigation placement="top" />
      <PathStepNavigation placement="bottom" />
    </>
  );
}

function renderAt(route: string) {
  render(
    <MemoryRouter initialEntries={[route]}>
      <Routes>
        <Route path="*" element={<Shell />} />
      </Routes>
    </MemoryRouter>,
  );
}

afterEach(() => {
  cleanup();
  window.localStorage.clear();
});

describe("PathStepNavigation stumbles (OC-EVOL-007)", () => {
  test("a step offers named ways back, and the page it leads to offers the return", async () => {
    window.localStorage.setItem("oc.active-path.v1", "what-is-optimization");
    renderAt("/formulations/PA017");

    expect(await screen.findByRole("heading", { name: "つまずいたら戻る" })).toBeTruthy();
    const back = screen.getByRole("link", { name: /「決めるもの」が、個数なのか割合なのか選択なのか分からない。/u });
    expect(back.getAttribute("href")).toBe("/learn/concept.variable-domain");
    expect(screen.getByText(/次の問い（2 \/ 4）/u)).toBeTruthy();

    fireEvent.click(back);

    const ret = await screen.findByRole("link", { name: /1 番目「線形計画」へ帰る/u });
    expect(ret.getAttribute("href")).toBe("/formulations/PA017");
    expect(screen.queryByRole("heading", { name: "つまずいたら戻る" })).toBeNull();
  });

  test("a page reached without a stumble shows no return link", async () => {
    renderAt("/learn/concept.variable-domain");
    expect(await screen.findByRole("navigation", { name: "学ぶ道筋での位置" })).toBeTruthy();
    expect(screen.queryByText(/へ帰る/u)).toBeNull();
  });
});
