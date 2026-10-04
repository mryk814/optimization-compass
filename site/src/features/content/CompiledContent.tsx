import type { AtlasContentPage } from "../../contracts/atlas-content";
import { useLayoutEffect, useMemo, useRef, type MouseEvent } from "react";
import { useLocation } from "react-router-dom";

import { ExplorableMounts } from "../explorable/ExplorableMounts";
import { PhysicalSceneMounts } from "../physical-scenes/PhysicalSceneMounts";

export function CompiledContent({ page }: { page: Pick<AtlasContentPage, "html" | "toc"> }) {
  const contentRef = useRef<HTMLDivElement>(null);
  // React reapplies innerHTML when this object changes, which detaches the figure portals.
  // Parent data loads must not replace an unchanged article after its figures have mounted.
  const compiledHtml = useMemo(() => ({ __html: page.html }), [page.html]);
  const { search } = useLocation();
  const focusScene = new URLSearchParams(search).get("figure") ?? undefined;
  useLayoutEffect(() => {
    // Code blocks and tables scroll inside themselves on narrow screens, so keyboard users need focus.
    contentRef.current?.querySelectorAll<HTMLElement>("pre, table").forEach((region) => {
      region.tabIndex = 0;
    });
  }, [page.html]);

  const goToHeading = (headingId: string) => {
    const heading = document.getElementById(headingId);
    heading?.scrollIntoView({ behavior: "smooth", block: "start" });
    heading?.focus({ preventScroll: true });
  };
  const followContentAnchor = (event: MouseEvent<HTMLDivElement>) => {
    const anchor = (event.target as Element).closest<HTMLAnchorElement>("a[data-heading-target]");
    if (!anchor?.dataset.headingTarget) return;
    event.preventDefault();
    goToHeading(anchor.dataset.headingTarget);
  };
  const headings = (
    <ol>
      {page.toc.map((heading) => (
        <li className={`toc-level-${heading.level}`} key={heading.heading_id}>
          <button onClick={() => goToHeading(heading.heading_id)} type="button">{heading.label}</button>
        </li>
      ))}
    </ol>
  );
  return (
    // Every article uses the linear-least-squares layout: a folded table of contents above a
    // 42rem reading column, with figures allowed to grow wider (docs/content-reading-principles.md §11).
    <div className="compiled-content-layout compiled-content-layout--lesson">
      {page.toc.length > 1 && (
        <nav aria-label="この教材の目次" className="content-toc">
          <details>
            <summary>このページの項目</summary>
            {headings}
          </details>
        </nav>
      )}
      <div ref={contentRef} className="markdown-body" dangerouslySetInnerHTML={compiledHtml} onClick={followContentAnchor} />
      <ExplorableMounts container={contentRef} html={page.html} />
      <PhysicalSceneMounts container={contentRef} html={page.html} focusScene={focusScene} />
    </div>
  );
}
