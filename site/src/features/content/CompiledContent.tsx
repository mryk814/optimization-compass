import type { AtlasContentPage } from "../../contracts/atlas-content";
import { useLayoutEffect, useRef, type MouseEvent } from "react";

export function CompiledContent({ page }: { page: Pick<AtlasContentPage, "html" | "toc"> }) {
  const contentRef = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => {
    contentRef.current?.querySelectorAll("pre").forEach((region) => {
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
  return (
    <div className="compiled-content-layout">
      {page.toc.length > 1 && (
        <nav aria-label="この教材の目次" className="content-toc">
          <strong>このページの項目</strong>
          <ol>
            {page.toc.map((heading) => (
              <li className={`toc-level-${heading.level}`} key={heading.heading_id}>
                <button onClick={() => goToHeading(heading.heading_id)} type="button">{heading.label}</button>
              </li>
            ))}
          </ol>
        </nav>
      )}
      <div ref={contentRef} className="markdown-body" dangerouslySetInnerHTML={{ __html: page.html }} onClick={followContentAnchor} />
    </div>
  );
}
