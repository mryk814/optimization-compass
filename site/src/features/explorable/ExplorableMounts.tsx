import { Component, Suspense, useLayoutEffect, useState, type ReactNode, type RefObject } from "react";
import { createPortal } from "react-dom";

import { EXPLORABLE_COMPONENTS } from "./registry";

import "./explorable.css";

interface Mount {
  id: string;
  node: HTMLElement;
}

/**
 * Finds the mount points the article compiler left in the HTML (`data-explorable-id`) and
 * renders the matching interactive figure into each one. Unknown ids keep the static fallback.
 */
export function ExplorableMounts({ container, html }: { container: RefObject<HTMLElement | null>; html: string }) {
  const [mounts, setMounts] = useState<Mount[]>([]);

  useLayoutEffect(() => {
    const root = container.current;
    if (!root) return;
    const found = Array.from(root.querySelectorAll<HTMLElement>("[data-explorable-id]")).flatMap((figure) => {
      const id = figure.dataset.explorableId ?? "";
      const node = figure.querySelector<HTMLElement>("[data-explorable-mount]");
      if (!node || !(id in EXPLORABLE_COMPONENTS)) return [];
      return [{ id, node }];
    });
    // The static fallback text is replaced by the live figure; unknown ids keep it.
    for (const mount of found) mount.node.replaceChildren();
    setMounts(found);
  }, [container, html]);

  return (
    <>
      {mounts.map(({ id, node }) => {
        const Figure = EXPLORABLE_COMPONENTS[id];
        return createPortal(
          <ExplorableBoundary>
            <Suspense fallback={<p className="ex-loading">図を読み込んでいます…</p>}>
              <Figure />
            </Suspense>
          </ExplorableBoundary>,
          node,
          id,
        );
      })}
    </>
  );
}

class ExplorableBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  render() {
    if (this.state.failed) {
      return <p className="explorable-fallback">図を表示できませんでした。下の説明で内容を確認してください。</p>;
    }
    return this.props.children;
  }
}
