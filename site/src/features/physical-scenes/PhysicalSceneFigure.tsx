import { Link } from "react-router-dom";
import { PHYSICAL_SCENES, physicalSceneRoute, type PhysicalSceneId } from "./catalog";
import { ScenePlayer, useLoadedScene } from "./ScenePlayer";

/** An article illustration; the surrounding prose supplies its learning context. */
export default function PhysicalSceneFigure({ id, restoreFocus = false }: { id: PhysicalSceneId; restoreFocus?: boolean }) {
  const meta = PHYSICAL_SCENES.find(scene => scene.id === id)!;
  const { loaded, error } = useLoadedScene(id);
  const ref = useRef<HTMLElement>(null);
  useEffect(() => {
    if (!restoreFocus || loaded?.id !== id) return;
    ref.current?.scrollIntoView({ block: "start", behavior: "auto" });
    ref.current?.querySelector<HTMLElement>(".physical-viewport")?.focus({ preventScroll: true });
  }, [restoreFocus, loaded, id]);
  return <section ref={ref} className="physical-page physical-embedded" aria-label={meta.title}>
    <div className="physical-figure-heading">
      <strong>{meta.question}</strong>
      <Link to={physicalSceneRoute(id)}>大きく見る →</Link>
    </div>
    {error && <p role="alert">{error}</p>}
    {loaded?.id === id ? <ScenePlayer scene={loaded} embedded /> : !error && <p role="status">図を読み込んでいます…</p>}
  </section>;
}
import { useEffect, useRef } from "react";
