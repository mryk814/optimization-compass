import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { CompiledContent } from "./CompiledContent";

describe("CompiledContent", () => {
  it("renders compiled content and keyboard-operable table of contents", () => {
    const scrollIntoView = vi.fn();
    const focus = vi.fn();
    render(<CompiledContent page={{
      html: '<h2 id="overview" tabindex="-1">Overview</h2><p>Compiled body.</p>',
      toc: [
        { heading_id: "overview", label: "Overview", level: 2 },
        { heading_id: "details", label: "Details", level: 2 },
      ],
    }} />);
    const heading = screen.getByRole("heading", { name: "Overview" });
    Object.defineProperties(heading, {
      scrollIntoView: { value: scrollIntoView },
      focus: { value: focus },
    });

    const button = screen.getByRole("button", { name: "Overview" });
    button.focus();
    fireEvent.keyDown(button, { key: "Enter" });
    fireEvent.click(button);

    expect(scrollIntoView).toHaveBeenCalledWith({ behavior: "smooth", block: "start" });
    expect(focus).toHaveBeenCalledWith({ preventScroll: true });
    expect(screen.getByText("Compiled body.")).toBeVisible();
  });
});
