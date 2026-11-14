import { Component, Suspense, useLayoutEffect, useState, type ReactNode, type RefObject } from "react";
import { createPortal } from "react-dom";

import { Lesson } from "./Lesson";
import { readLesson, type LessonMarkup } from "./lessonMarkup";
import { EXPLORABLE_COMPONENTS } from "./registry";

import "./explorable.css";

interface Mount {
  id: string;
  node: HTMLElement;
}

/**
 * Finds the mount points the article compiler left in the HTML and renders the matching
 * interactive figure into each one: a plain figure (`data-explorable-id`), or a lesson
 * (`data-lesson-figure`), whose steps then drive the figure. Unknown ids keep the static fallback.
 */
export function ExplorableMounts({ container, html }: { container: RefObject<HTMLElement | null>; html: string }) {
  const [mounts, setMounts] = useState<Mount[]>([]);
  const [lessons, setLessons] = useState<LessonMarkup[]>([]);

  useLayoutEffect(() => {
    const root = container.current;
    if (!root) return;
    const foundLessons = Array.from(root.querySelectorAll<HTMLElement>("[data-lesson-figure]")).flatMap((section) => {
      const markup = readLesson(section);
      return markup && markup.figureId in EXPLORABLE_COMPONENTS ? [markup] : [];
    });
    const found = Array.from(root.querySelectorAll<HTMLElement>("[data-explorable-id]")).flatMap((figure) => {
      // A lesson's figure is mounted by the lesson, which also drives it.
      if (figure.closest("[data-lesson-figure]")) return [];
      const id = figure.dataset.explorableId ?? "";
      const node = figure.querySelector<HTMLElement>("[data-explorable-mount]");
      if (!node || !(id in EXPLORABLE_COMPONENTS)) return [];
      return [{ id, node }];
    });
    // The static fallback text is replaced by the live figure; unknown ids keep it.
    for (const mount of found) mount.node.replaceChildren();
    for (const lesson of foundLessons) lesson.mount.replaceChildren();
    setMounts(found);
    setLessons(foundLessons);
  }, [container, html]);

  return (
    <>
      {mounts.map(({ id, node }) => createPortal(<LiveFigure id={id} />, node, id))}
      {lessons.map((markup) => (
        <Lesson key={markup.figureId} markup={markup}>
          <LiveFigure id={markup.figureId} />
        </Lesson>
      ))}
    </>
  );
}

function LiveFigure({ id }: { id: string }) {
  const Figure = EXPLORABLE_COMPONENTS[id];
  return (
    <ExplorableBoundary>
      <Suspense fallback={<p className="ex-loading">図を読み込んでいます…</p>}>
        <Figure />
      </Suspense>
    </ExplorableBoundary>
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
