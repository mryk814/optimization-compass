import type { AtlasContentPage } from "../../contracts/atlas-content";
import type { MouseEvent } from "react";

export function CompiledContent({ page }: { page: Pick<AtlasContentPage, "html" | "toc"> }) {
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
          <strong>On this page</strong>
          <ol>
            {page.toc.map((heading) => (
              <li className={`toc-level-${heading.level}`} key={heading.heading_id}>
                <button onClick={() => goToHeading(heading.heading_id)} type="button">{heading.label}</button>
              </li>
            ))}
          </ol>
        </nav>
      )}
      <div className="markdown-body" dangerouslySetInnerHTML={{ __html: page.html }} onClick={followContentAnchor} />
    </div>
  );
}
