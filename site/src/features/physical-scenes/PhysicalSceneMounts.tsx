import { Component, lazy, Suspense, useEffect, useLayoutEffect, useRef, useState, type ReactNode, type RefObject } from "react";
import { createPortal } from "react-dom";
import { PHYSICAL_SCENES, physicalSceneRoute, type PhysicalSceneId } from "./catalog";

const Figure = lazy(() => import("./PhysicalSceneFigure"));
interface Mount { id: PhysicalSceneId; node: HTMLElement }

/** Article links own placement. No content-id-to-figure mapping lives in the UI. */
export function PhysicalSceneMounts({ container, html, focusScene }: { container: RefObject<HTMLElement | null>; html: string; focusScene?: string }) {
  const [mounts, setMounts] = useState<Mount[]>([]);
  useLayoutEffect(() => {
    const found: Mount[] = [];
    const seen = new Set<PhysicalSceneId>();
    container.current?.querySelectorAll<HTMLAnchorElement>("p > a[href]").forEach(anchor => {
      const scene = PHYSICAL_SCENES.find(item => anchor.getAttribute("href") === `#${physicalSceneRoute(item.id)}`);
      const paragraph = anchor.parentElement;
      if (!scene || seen.has(scene.id) || !paragraph) return;
      seen.add(scene.id);
      const node = document.createElement("div");
      node.className = "physical-article-mount";
      paragraph.after(node);
      found.push({ id: scene.id, node });
    });
    setMounts(found);
    return () => { found.forEach(mount => mount.node.remove()); };
  }, [container, html]);
  return <>{mounts.map(({ id, node }) => createPortal(<ArticleFigure id={id} restoreFocus={focusScene === id} />, node, id))}</>;
}

function ArticleFigure({ id, restoreFocus }: { id: PhysicalSceneId; restoreFocus: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    if (!ref.current) return;
    if (restoreFocus) { setVisible(true); return; }
    if (!("IntersectionObserver" in window)) { setVisible(true); return; }
    const observer = new IntersectionObserver(entries => {
      if (entries.some(entry => entry.isIntersecting)) { setVisible(true); observer.disconnect(); }
    }, { rootMargin: "200px" });
    observer.observe(ref.current);
    return () => observer.disconnect();
  }, [restoreFocus]);
  return <div ref={ref}>
    {visible ? <FigureBoundary><Suspense fallback={<p role="status">図を読み込んでいます…</p>}><Figure id={id} restoreFocus={restoreFocus} /></Suspense></FigureBoundary>
      : <p>この説明の図は、ここまで読み進めると表示されます。</p>}
  </div>;
}

class FigureBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() {
    return this.state.failed ? <p>図を表示できませんでした。記事の説明、またはリンク先で確認してください。</p> : this.props.children;
  }
}
