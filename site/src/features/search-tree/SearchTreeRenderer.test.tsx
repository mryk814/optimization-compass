import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, test } from "vitest";

import artifactFixture from "../../../public/data/search-trees/binary-knapsack-bnb-complete.json";
import { parseSearchTreeArtifact, parseSearchTreeFramePayload } from "../../contracts/search-tree";
import { SearchTreeRenderer } from "./SearchTreeRenderer";

describe("SearchTreeRenderer", () => {
  afterEach(cleanup);

  test("shows bounds, prune explanations, textual summary, and keyboard tree navigation", () => {
    const artifact = parseSearchTreeArtifact(artifactFixture);
    const payload = parseSearchTreeFramePayload(artifact.trace.frames.at(-1)!.payload);
    render(<SearchTreeRenderer payload={payload} />);

    expect(screen.getByLabelText("Best feasible")).toHaveTextContent("15");
    expect(screen.getByLabelText("Global bound")).toHaveTextContent("15.00");
    expect(screen.getByLabelText("Gap")).toHaveTextContent("0.00");
    expect(screen.getByText(/最適性証明済み/u)).toBeVisible();
    expect(screen.getByText("Textual tree summary")).toBeVisible();
    expect(screen.getAllByText(/このnode以下は探索しません/u).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/改善できず探索しません/u).length).toBeGreaterThan(0);

    const tree = screen.getByRole("tree");
    const items = within(tree).getAllByRole("treeitem");
    items[0].focus();
    fireEvent.keyDown(items[0], { key: "ArrowDown" });
    expect(items[1]).toHaveFocus();
  });

  test("accepts a unique heading identity when multiple trees share one page", () => {
    const artifact = parseSearchTreeArtifact(artifactFixture);
    const payload = parseSearchTreeFramePayload(artifact.trace.frames.at(-1)!.payload);
    render(
      <SearchTreeRenderer
        headingId="comparison-tree-reference"
        headingLabel="証明runの探索木"
        payload={payload}
      />,
    );

    const heading = screen.getByRole("heading", { level: 2, name: "証明runの探索木" });
    expect(heading).toHaveAttribute("id", "comparison-tree-reference");
    expect(heading.closest("section")).toHaveAttribute("aria-labelledby", "comparison-tree-reference");
    expect(document.querySelector("#search-tree-heading")).not.toBeInTheDocument();
  });
});
