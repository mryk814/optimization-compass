import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { useRef } from "react";
import { afterEach, expect, it, vi } from "vitest";

import { useDomainDrag } from "./svg";

afterEach(cleanup);

it("ends a cancelled drag and accepts a later gesture", () => {
  const onDrag = vi.fn();
  function Handle() {
    const svgRef = useRef<SVGSVGElement>(null);
    const drag = useDomainDrag({
      svgRef,
      viewport: { width: 100, height: 100, bounds: { xMin: 0, xMax: 1, yMin: 0, yMax: 1 } },
      onDrag,
    });
    return <svg ref={svgRef}><g data-testid="handle" {...drag}><circle r={10} /></g></svg>;
  }
  const { container } = render(<Handle />);
  vi.spyOn(container.querySelector("svg")!, "getBoundingClientRect").mockReturnValue(new DOMRect(0, 0, 100, 100));
  const handle = screen.getByTestId("handle");
  const pointer = (type: string, x = 10, y = 20) => fireEvent(handle, new MouseEvent(type, { bubbles: true, clientX: x, clientY: y }));
  pointer("pointerdown");
  pointer("pointermove");
  expect(onDrag).toHaveBeenLastCalledWith(0.1, 0.8);
  pointer("pointercancel");
  pointer("pointermove", 20, 30);
  expect(onDrag).toHaveBeenCalledTimes(1);
  pointer("pointerdown");
  pointer("pointermove", 20, 30);
  expect(onDrag).toHaveBeenCalledTimes(2);
  expect(onDrag).toHaveBeenLastCalledWith(0.2, 0.7);
});
