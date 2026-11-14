import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";

import type { LessonMarkup } from "./lessonMarkup";
import { LessonContext, type LessonDrive } from "./lessonContext";
import { usePrefersReducedMotion } from "./useTimeline";

/** Two columns need this much room; below it the figure sits above one step at a time. */
const WIDE_QUERY = "(min-width: 64rem)";
/** How long a programmatic scroll may take before scroll position decides the step again. */
const SCROLL_SETTLE_MS = 900;

function useWide(): boolean {
  const [wide, setWide] = useState(
    () => typeof window.matchMedia === "function" && window.matchMedia(WIDE_QUERY).matches,
  );
  useEffect(() => {
    if (typeof window.matchMedia !== "function") return undefined;
    const query = window.matchMedia(WIDE_QUERY);
    const update = () => setWide(query.matches);
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);
  return wide;
}

/**
 * One lesson in an article: the figure, and the steps of prose that drive it.
 *
 * Wide screens pin the figure beside the steps and the step crossing the middle of the viewport
 * is the one shown. Narrow screens show the figure, then one step at a time under it. Either way
 * entering a step replays its beat, so the prose and the motion cannot drift apart.
 */
export function Lesson({ markup, children }: { markup: LessonMarkup; children: ReactNode }) {
  const { figureId, root, mount, nav, steps } = markup;
  const reducedMotion = usePrefersReducedMotion();
  const wide = useWide();
  const beats = useMemo(() => steps.map((step) => step.beat), [steps]);
  const [index, setIndex] = useState(0);
  const [local, setLocal] = useState(0);
  // Bumped to restart the clock on the step that is already showing.
  const [run, setRun] = useState(0);
  const [auto, setAuto] = useState(false);
  const [free, setFree] = useState(false);
  // Held by automation: the clock is stopped and `local` is whatever `show` asked for.
  const [held, setHeld] = useState(false);
  // The lesson starts its first beat when the reader reaches it, not at page load.
  const [seen, setSeen] = useState(typeof IntersectionObserver !== "function");
  const [chosen, setChosen] = useState<Readonly<Record<number, number>>>({});
  const indexRef = useRef(index);
  indexRef.current = index;
  const freeRef = useRef(free);
  freeRef.current = free;
  const suppressUntil = useRef(0);
  const painted = useRef<Array<() => void>>([]);
  const last = steps.length - 1;
  const duration = beats[index].durationS;

  const enter = useCallback((target: number) => {
    setHeld(false);
    setFree(false);
    setIndex(target);
    setLocal(0);
    setRun((value) => value + 1);
  }, []);

  /** Brings a step to the middle of the screen without that scroll choosing the step again. */
  const reveal = useCallback((target: number, smooth: boolean) => {
    const node = wide ? steps[target].node : root;
    if (typeof node.scrollIntoView !== "function") return;
    suppressUntil.current = performance.now() + SCROLL_SETTLE_MS;
    node.scrollIntoView({ behavior: smooth ? "smooth" : "instant", block: wide ? "center" : "nearest" });
  }, [root, steps, wide]);

  const goTo = useCallback((target: number) => {
    if (target < 0 || target > last) return;
    enter(target);
    if (wide) reveal(target, !reducedMotion);
  }, [enter, last, reducedMotion, reveal, wide]);

  // Handing over the controls: they open at the top of the figure, so the reader is taken there.
  const takeOver = useCallback(() => {
    setAuto(false);
    setFree(true);
    const figure = mount.closest<HTMLElement>(".lesson-figure") ?? mount;
    figure.scrollTop = 0;
    if (!wide && typeof figure.scrollIntoView === "function") {
      figure.scrollIntoView({ behavior: reducedMotion ? "instant" : "smooth", block: "start" });
    }
  }, [mount, reducedMotion, wide]);

  // The clock of the current step. Reduced motion shows each step finished instead.
  const stopped = reducedMotion || held || free || !seen;
  useEffect(() => {
    if (stopped) return undefined;
    let frame = 0;
    let previous: number | undefined;
    let elapsed = 0;
    const tick = (now: number) => {
      elapsed += previous === undefined ? 0 : Math.max(0, (now - previous) / 1000);
      previous = now;
      setLocal(Math.min(duration, elapsed));
      if (elapsed < duration) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [duration, index, run, stopped]);

  const shownLocal = reducedMotion && !held ? duration : local;
  const finished = shownLocal >= duration;

  // Auto mode: move on when a step has played out. A predict step waits for the reader's choice.
  const waiting = steps[index].predict !== undefined && chosen[index] === undefined;
  useEffect(() => {
    if (!auto || !finished || waiting || free) return;
    if (index === last) setAuto(false);
    else goTo(index + 1);
  }, [auto, finished, free, goTo, index, last, waiting]);
  useEffect(() => {
    if (reducedMotion) setAuto(false);
  }, [reducedMotion]);

  // Start when the lesson first comes on screen.
  useEffect(() => {
    if (seen) return undefined;
    const observer = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting)) setSeen(true);
    });
    observer.observe(mount);
    return () => observer.disconnect();
  }, [mount, seen]);

  // Wide: the step crossing the middle of the viewport is the active one.
  useEffect(() => {
    if (!wide || typeof IntersectionObserver !== "function") return undefined;
    const observer = new IntersectionObserver((entries) => {
      if (performance.now() < suppressUntil.current) return;
      const crossing = entries.filter((entry) => entry.isIntersecting).at(-1);
      if (!crossing) return;
      const target = steps.findIndex((step) => step.node === crossing.target);
      if (target !== -1 && (target !== indexRef.current || freeRef.current)) enter(target);
    }, { rootMargin: "-50% 0px -50% 0px" });
    for (const step of steps) observer.observe(step.node);
    return () => observer.disconnect();
  }, [enter, steps, wide]);

  // Narrow: tapping the step's text moves on, except where the tap has its own meaning.
  useEffect(() => {
    if (wide) return undefined;
    const node = steps[index].node;
    if (steps[index].predict || index === last || free) return undefined;
    const onClick = (event: MouseEvent) => {
      if ((event.target as Element).closest("a, button, summary, input, pre, table")) return;
      if (window.getSelection()?.toString()) return;
      goTo(index + 1);
    };
    node.addEventListener("click", onClick);
    node.classList.add("is-tappable");
    return () => {
      node.removeEventListener("click", onClick);
      node.classList.remove("is-tappable");
    };
  }, [free, goTo, index, last, steps, wide]);

  // The compiled HTML is not React's to render, so its state is written onto it directly.
  useLayoutEffect(() => {
    root.classList.add("is-live");
    root.classList.toggle("is-wide", wide);
    root.classList.toggle("is-free", free);
    steps.forEach((step, position) => {
      // Written out because a CSS counter skips the steps a narrow screen hides.
      step.node.dataset.lessonNumber = String(position + 1);
      step.node.classList.toggle("is-active", position === index);
      if (position === index) step.node.setAttribute("aria-current", "step");
      else step.node.removeAttribute("aria-current");
    });
  }, [free, index, root, steps, wide]);
  useLayoutEffect(() => () => {
    root.classList.remove("is-live", "is-wide", "is-free");
    for (const step of steps) {
      step.node.classList.remove("is-active");
      step.node.removeAttribute("aria-current");
    }
  }, [root, steps]);
  // Automation: article shots and e2e ask for one step at a time and wait for its frame.
  useEffect(() => {
    const waitingForPaint = painted.current;
    if (waitingForPaint.length === 0) return;
    painted.current = [];
    requestAnimationFrame(() => requestAnimationFrame(() => waitingForPaint.forEach((resolve) => resolve())));
  });
  useEffect(() => {
    const lessons = (window.__ocLessons ??= {});
    lessons[figureId] = {
      steps: steps.map((step) => ({
        seconds: step.beat.durationS,
        caption: step.beat.captionJa,
        predict: step.predict !== undefined,
      })),
      show: (target, at) => new Promise<void>((resolve, reject) => {
        if (!Number.isInteger(target) || target < 0 || target > last) {
          reject(new RangeError(`lesson ${figureId} has no step ${target}`));
          return;
        }
        const length = beats[target].durationS;
        painted.current.push(resolve);
        setAuto(false);
        setFree(false);
        setHeld(true);
        setIndex(target);
        setLocal(Math.min(Math.max(at ?? length, 0), length));
        setRun((value) => value + 1);
        reveal(target, false);
      }),
    };
    return () => {
      delete lessons[figureId];
    };
  }, [beats, figureId, last, reveal, steps]);

  const drive: LessonDrive = useMemo(
    () => ({ beats, index, local: shownLocal, free }),
    [beats, free, index, shownLocal],
  );

  return (
    <>
      {createPortal(<LessonContext.Provider value={drive}>{children}</LessonContext.Provider>, mount)}
      {createPortal(
        free ? (
          <div aria-label="解説の操作" className="lesson-bar" role="group">
            <button className="lesson-back" onClick={() => goTo(index)} type="button">◀ 解説に戻る</button>
            <p className="lesson-count">自分で動かしています</p>
          </div>
        ) : (
          <div aria-label="解説の操作" className="lesson-bar" role="group">
            <button className="lesson-prev" disabled={index === 0} onClick={() => goTo(index - 1)} type="button">
              ◀ 前へ
            </button>
            <p className="lesson-count">
              <span className="lesson-sr">解説 </span><strong>{index + 1}</strong> / {steps.length}
            </p>
            {index === last ? (
              <button className="lesson-free" onClick={takeOver} type="button">
                自分で動かす
              </button>
            ) : (
              <button className="lesson-next" onClick={() => goTo(index + 1)} type="button">次へ ▶</button>
            )}
            <div aria-hidden="true" className="lesson-progress">
              {steps.map((step, position) => (
                <span
                  className={position < index ? "is-done" : position === index ? "is-current" : undefined}
                  key={position}
                  style={position === index
                    ? { ["--lesson-progress" as string]: String(shownLocal / step.beat.durationS) }
                    : undefined}
                />
              ))}
            </div>
            {/* Narrow screens keep this bar on screen under a tall figure; the caption says what to watch. */}
            <p className="lesson-caption" dangerouslySetInnerHTML={{ __html: steps[index].captionHtml }} />
          </div>
        ),
        nav,
        "bar",
      )}
      {createPortal(
        !free && !reducedMotion && (
          <div aria-label="再生の操作" className="lesson-more" role="group">
            <button className="lesson-replay" onClick={() => enter(index)} type="button">↻ もう一度</button>
            <button aria-pressed={auto} className="lesson-auto" onClick={() => setAuto((value) => !value)} type="button">
              {auto ? "⏸ 自動を止める" : "▶ 自動で見る"}
            </button>
          </div>
        ),
        nav,
        "more",
      )}
      {steps.map((step, position) => step.predict && createPortal(
        <Choices
          answer={step.predict.answer}
          choices={step.predict.choices}
          chosen={chosen[position]}
          onChoose={(choice) => setChosen((value) => ({ ...value, [position]: choice }))}
        />,
        step.predict.slot,
        `choices-${position}`,
      ))}
    </>
  );
}

interface ChoicesProps {
  choices: readonly string[];
  answer: number;
  chosen: number | undefined;
  onChoose(choice: number): void;
}

/** A prediction is made once: the reader's pick and the answer are then both marked. */
function Choices({ choices, answer, chosen, onChoose }: ChoicesProps) {
  const decided = chosen !== undefined;
  return (
    <>
      {choices.map((html, choice) => {
        const classes = [
          "lesson-choice",
          decided && choice === chosen ? "is-chosen" : "",
          decided && choice === answer ? "is-answer" : "",
        ].filter(Boolean).join(" ");
        return (
          <button
            aria-disabled={decided}
            aria-pressed={choice === chosen}
            className={classes}
            key={choice}
            onClick={decided ? undefined : () => onChoose(choice)}
            type="button"
          >
            <span dangerouslySetInnerHTML={{ __html: html }} />
            {decided && choice === chosen && <em className="lesson-mark">あなたの予想</em>}
            {decided && choice === answer && <em className="lesson-mark lesson-mark-answer">答え</em>}
          </button>
        );
      })}
      <p aria-live="polite" className="lesson-verdict">
        {decided && (chosen === answer
          ? "予想どおりです。次の段で、図で確かめます。"
          : "予想とは違いました。次の段で、図で確かめます。")}
      </p>
    </>
  );
}
