import type { BeatSettings, SceneBeat } from "./scene";

/**
 * A lesson as the article compiler wrote it (`_render_lesson` in content_markdown.py):
 *
 *   <section class="lesson" data-lesson-figure="<id>">
 *     <div class="lesson-stage"><figure data-explorable-id><div data-explorable-mount/></figure>
 *       <div data-lesson-nav/></div>
 *     <ol class="lesson-steps">
 *       <li data-lesson-step data-seconds data-settings data-caption [data-predict data-answer]>…
 *
 * The step's prose stays where the compiler put it; the site only adds behaviour around it.
 */
export interface LessonStep {
  node: HTMLElement;
  beat: SceneBeat;
  /** The step's first sentence as written (emphasis and math kept), for the bar under the figure. */
  captionHtml: string;
  /** Set on a predict step: where the choice buttons go, the choices' HTML, and the right one. */
  predict?: { slot: HTMLElement; choices: readonly string[]; answer: number };
}

export interface LessonMarkup {
  figureId: string;
  root: HTMLElement;
  mount: HTMLElement;
  nav: HTMLElement;
  steps: readonly LessonStep[];
}

function choiceHtml(item: Element): string {
  // The compiler wraps a list item's text in one paragraph; a button cannot hold a paragraph.
  const only = item.children.length === 1 ? item.children[0] : null;
  return only?.tagName === "P" ? only.innerHTML : item.innerHTML;
}

/** The first paragraph up to its first 「。」, the same sentence the compiler put in data-caption. */
function firstSentenceHtml(node: HTMLElement): string {
  const paragraph = Array.from(node.children).find((child) => child.tagName === "P");
  if (!paragraph) return "";
  const walker = document.createTreeWalker(paragraph, NodeFilter.SHOW_TEXT);
  for (let text = walker.nextNode(); text; text = walker.nextNode()) {
    const end = (text.nodeValue ?? "").indexOf("。");
    if (end === -1) continue;
    const range = document.createRange();
    range.setStart(paragraph, 0);
    range.setEnd(text, end + 1);
    const holder = document.createElement("span");
    holder.append(range.cloneContents());
    return holder.innerHTML;
  }
  return paragraph.innerHTML;
}

function readStep(node: HTMLElement): LessonStep | null {
  const durationS = Number(node.dataset.seconds);
  const caption = node.dataset.caption ?? "";
  let settings: BeatSettings;
  try {
    settings = JSON.parse(node.dataset.settings ?? "") as BeatSettings;
  } catch {
    return null;
  }
  if (!(durationS > 0) || typeof settings !== "object" || settings === null) return null;
  const step: LessonStep = {
    node,
    beat: { settings, durationS, captionJa: caption, narrationJa: caption },
    captionHtml: firstSentenceHtml(node),
  };
  if (node.dataset.predict === undefined) return step;
  const list = node.querySelector<HTMLElement>("[data-lesson-choices]");
  const answer = Number(node.dataset.answer) - 1;
  if (!list) return null;
  const choices = Array.from(list.children, choiceHtml);
  if (!(answer >= 0 && answer < choices.length)) return null;
  // The buttons go beside the authored list, which stays in the page (hidden by CSS while live),
  // so reading the same markup again finds the same choices.
  const next = list.nextElementSibling;
  const slot = next instanceof HTMLElement && next.dataset.lessonChoiceSlot !== undefined
    ? next
    : document.createElement("div");
  slot.dataset.lessonChoiceSlot = "";
  slot.className = "lesson-choice-slot";
  list.after(slot);
  return { ...step, predict: { slot, choices, answer } };
}

/** Reads one lesson section; null when it is not the markup above, which then stays static. */
export function readLesson(root: HTMLElement): LessonMarkup | null {
  const figureId = root.dataset.lessonFigure ?? "";
  const mount = root.querySelector<HTMLElement>("[data-explorable-mount]");
  const nav = root.querySelector<HTMLElement>("[data-lesson-nav]");
  const steps = Array.from(root.querySelectorAll<HTMLElement>("[data-lesson-step]"), readStep);
  if (!figureId || !mount || !nav || steps.length === 0 || steps.some((step) => step === null)) return null;
  return { figureId, root, mount, nav, steps: steps as LessonStep[] };
}

/** What automation (article shots, e2e) may do with a lesson on the page. */
export interface LessonHandle {
  steps: ReadonlyArray<{ seconds: number; caption: string; predict: boolean }>;
  /**
   * Shows step `index` held at `local` seconds (default: its finished state), brings it on
   * screen, and resolves once that frame has been painted.
   */
  show(index: number, local?: number): Promise<void>;
}

declare global {
  interface Window {
    __ocLessons?: Record<string, LessonHandle>;
  }
}
