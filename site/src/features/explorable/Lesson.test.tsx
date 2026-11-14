import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { CompiledContent } from "../content/CompiledContent";
import { Lesson } from "./Lesson";
import { readLesson } from "./lessonMarkup";
import type { BeatSettings, ResolvedSettings } from "./scene";
import { useSceneTour } from "./useSceneTour";

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
  document.body.replaceChildren();
});

// The markup `_render_lesson` in content_markdown.py writes (tests/test_lessons.py holds that side).
interface StepSpec {
  seconds?: number;
  settings: BeatSettings;
  body: string;
  answer?: number;
}

function stepHtml({ seconds = 6, settings, body, answer }: StepSpec): string {
  const caption = /<p>(?:<strong>)?([^<。]*。?)/u.exec(body)?.[1] ?? "";
  const predict = answer === undefined ? "" : ` data-predict="" data-answer="${answer}"`;
  const data = JSON.stringify(settings).replaceAll('"', "&quot;");
  return `<li class="lesson-step" data-lesson-step${predict} data-seconds="${seconds}" data-settings="${data}"`
    + ` data-caption="${caption}">\n${body}\n</li>`;
}

function lessonHtml(figureId: string, steps: StepSpec[]): string {
  return `<section class="lesson" data-lesson-figure="${figureId}"><div class="lesson-stage">`
    + `<figure class="explorable lesson-figure" role="group" data-explorable-id="${figureId}" aria-label="図">`
    + '<div class="explorable-mount" data-explorable-mount><p class="explorable-fallback">静的な代替</p></div></figure>'
    + '<div class="lesson-nav" data-lesson-nav></div></div>'
    + `<ol class="lesson-steps">\n${steps.map(stepHtml).join("\n")}\n</ol></section>`;
}

const STEPS: StepSpec[] = [
  { seconds: 6, settings: { eta: 0.02, iter: { from: 0, to: 90 } }, body: "<p><strong>一つ目の要点。</strong> 続きの説明。</p>" },
  { seconds: 4, settings: { eta: 0.045, iter: { from: 0, to: 40, rate: 5 } }, body: "<p>二つ目の要点。</p>" },
  {
    seconds: 3,
    settings: { eta: 0.045, iter: 0 },
    body: '<p>どうなるか。</p>\n<ul class="lesson-choices" data-lesson-choices="">\n<li><p>収束する</p>\n</li>\n<li><p>発散する</p>\n</li>\n</ul>',
    answer: 2,
  },
  { seconds: 5, settings: { eta: 0.053, iter: { from: 0, to: 100 } }, body: "<p>四つ目の要点。</p>" },
];

/** Animation frames run by hand, so a step's seconds pass only when the test says so. */
function stubFrames() {
  const pending = new Map<number, FrameRequestCallback>();
  let nextId = 1;
  let now = 1_000;
  vi.stubGlobal("requestAnimationFrame", (callback: FrameRequestCallback) => {
    pending.set(nextId, callback);
    return nextId++;
  });
  vi.stubGlobal("cancelAnimationFrame", (id: number) => pending.delete(id));
  const frame = () => act(() => {
    const due = [...pending.values()];
    pending.clear();
    due.forEach((callback) => callback(now));
  });
  return {
    /** Lets `seconds` pass in 0.1 s frames. */
    advance(seconds: number) {
      frame();
      for (let passed = 0; passed < seconds - 1e-9; passed += 0.1) {
        now += 100;
        frame();
      }
    },
  };
}

function stubMedia(matching: string) {
  vi.stubGlobal("matchMedia", (query: string) => ({
    matches: query.includes(matching),
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
  }));
}

/** A figure reduced to what the lesson tells it: the tour as `useSceneTour` reports it. */
function Probe({ onExit }: { onExit(settings: BeatSettings): void }) {
  const tour = useSceneTour("probe", [], onExit);
  return (
    <output data-testid="probe">
      {JSON.stringify({
        lesson: tour.lesson,
        active: tour.active,
        index: tour.index,
        values: tour.values,
        beatSettings: tour.beat?.settings,
      })}
    </output>
  );
}

function renderLesson(steps: StepSpec[] = STEPS) {
  document.body.innerHTML = lessonHtml("probe-figure", steps);
  const markup = readLesson(document.querySelector<HTMLElement>("[data-lesson-figure]")!)!;
  const onExit = vi.fn<(settings: BeatSettings) => void>();
  render(<Lesson markup={markup}><Probe onExit={onExit} /></Lesson>);
  const probe = () => JSON.parse(screen.getByTestId("probe").textContent ?? "{}") as {
    lesson: boolean;
    active: boolean;
    index: number;
    values: ResolvedSettings;
    beatSettings?: BeatSettings;
  };
  const stepNodes = markup.steps.map((step) => step.node);
  const active = () => stepNodes.findIndex((node) => node.getAttribute("aria-current") === "step");
  return { markup, onExit, probe, stepNodes, active };
}

describe("readLesson", () => {
  it("reads each step's beat, its first sentence as written, and a predict step's choices", () => {
    document.body.innerHTML = lessonHtml("probe-figure", STEPS);
    const markup = readLesson(document.querySelector<HTMLElement>("[data-lesson-figure]")!)!;

    expect(markup.figureId).toBe("probe-figure");
    expect(markup.steps.map((step) => step.beat.durationS)).toEqual([6, 4, 3, 5]);
    expect(markup.steps[0].beat.settings).toEqual({ eta: 0.02, iter: { from: 0, to: 90 } });
    expect(markup.steps[0].beat.captionJa).toBe("一つ目の要点。");
    expect(markup.steps[0].captionHtml).toBe("<strong>一つ目の要点。</strong>");
    expect(markup.steps[2].predict).toMatchObject({ choices: ["収束する", "発散する"], answer: 1 });
    // Reading the same markup again (React strict mode does) finds the same choices and slot.
    const again = readLesson(markup.root)!;
    expect(again.steps[2].predict?.choices).toEqual(["収束する", "発散する"]);
    expect(again.steps[2].predict?.slot).toBe(markup.steps[2].predict?.slot);
  });

  it("leaves markup it cannot read alone", () => {
    document.body.innerHTML = lessonHtml("probe-figure", STEPS).replace("data-settings=\"{", "data-settings=\"oops{");

    expect(readLesson(document.querySelector<HTMLElement>("[data-lesson-figure]")!)).toBeNull();
  });
});

describe("Lesson", () => {
  it("drives the figure from the first step and plays that step's beat", () => {
    const frames = stubFrames();
    const { probe, active } = renderLesson();

    expect(probe()).toMatchObject({ lesson: true, active: true, index: 0, values: { eta: 0.02, iter: 0 } });
    expect(active()).toBe(0);
    expect(screen.getByText("1", { selector: ".lesson-count strong" })).toBeInTheDocument();

    frames.advance(1.8); // a sweep is linear over the beat less its 1.5 s hold: 1.8 / 4.5 of 90
    expect(probe().values.iter).toBeCloseTo(36, 5);
    // A figure that still reads `tour.beat.settings` gets the same plain values, not the sweep.
    expect(probe().beatSettings).toEqual(probe().values);
    frames.advance(10);
    expect(probe().values.iter).toBe(90);
    expect(active()).toBe(0); // without auto mode a finished step waits for the reader
  });

  it("replays from the start of the step the reader moves to", () => {
    const frames = stubFrames();
    const { probe, active } = renderLesson();
    frames.advance(10);

    fireEvent.click(screen.getByRole("button", { name: "次へ ▶" }));
    expect(active()).toBe(1);
    expect(probe()).toMatchObject({ index: 1, values: { eta: 0.045, iter: 0 } });
    frames.advance(2);
    expect(probe().values.iter).toBeCloseTo(10, 5); // 5 per second
    frames.advance(10);
    expect(probe().values.iter).toBeCloseTo(20, 5); // a rate stops when the step's 4 s are over

    fireEvent.click(screen.getByRole("button", { name: "↻ もう一度" }));
    expect(probe().values.iter).toBe(0);

    fireEvent.click(screen.getByRole("button", { name: "◀ 前へ" }));
    expect(probe()).toMatchObject({ index: 0, values: { iter: 0 } });
    expect(screen.getByRole("button", { name: "◀ 前へ" })).toBeDisabled();
  });

  it("turns a predict step's list into buttons and marks the pick and the answer once chosen", () => {
    stubFrames();
    const { markup } = renderLesson();
    const step = within(markup.steps[2].node);

    const wrong = step.getByRole("button", { name: "収束する" });
    fireEvent.click(wrong);

    expect(wrong).toHaveAttribute("aria-pressed", "true");
    expect(wrong).toHaveTextContent("あなたの予想");
    expect(step.getByRole("button", { name: /発散する/ })).toHaveTextContent("答え");
    expect(step.getByText("予想とは違いました。次の段で、図で確かめます。")).toBeInTheDocument();
    // A prediction is made once.
    fireEvent.click(step.getByRole("button", { name: /発散する/ }));
    expect(step.getByRole("button", { name: /発散する/ })).toHaveAttribute("aria-pressed", "false");
  });

  it("advances by itself in auto mode, waits at a predict step, and stops at the end", () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
    const frames = stubFrames();
    const { markup, active } = renderLesson();

    fireEvent.click(screen.getByRole("button", { name: "▶ 自動で見る" }));
    frames.advance(5.5);
    expect(active()).toBe(0);
    frames.advance(1);
    expect(active()).toBe(1);
    frames.advance(4.5);
    expect(active()).toBe(2);
    frames.advance(20);
    expect(active()).toBe(2); // the predict step waits for a choice

    fireEvent.click(within(markup.steps[2].node).getByRole("button", { name: "発散する" }));
    // The marked answer stays up for a moment before the lesson moves on.
    frames.advance(0.2);
    act(() => { vi.advanceTimersByTime(1_000); });
    expect(active()).toBe(2);
    act(() => { vi.advanceTimersByTime(1_000); });
    expect(active()).toBe(3);
    frames.advance(6);
    expect(active()).toBe(3);
    expect(screen.getByRole("button", { name: "▶ 自動で見る" })).toHaveAttribute("aria-pressed", "false");
  });

  it("hands the last step's values to the figure when the reader takes over, and takes them back", () => {
    const frames = stubFrames();
    const { probe, onExit } = renderLesson();
    for (let step = 0; step < 3; step += 1) fireEvent.click(screen.getByRole("button", { name: "次へ ▶" }));
    frames.advance(10);

    fireEvent.click(screen.getByRole("button", { name: "自分で動かす" }));
    expect(onExit).toHaveBeenCalledExactlyOnceWith({ eta: 0.053, iter: 100 });
    expect(probe()).toMatchObject({ lesson: true, active: false, values: {} });
    expect(screen.queryByRole("button", { name: "▶ 自動で見る" })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "◀ 解説に戻る" }));
    expect(probe()).toMatchObject({ active: true, index: 3, values: { eta: 0.053, iter: 0 } });
  });

  it("shows every step finished and offers no playback when motion is reduced", () => {
    stubMedia("prefers-reduced-motion");
    stubFrames();
    const { probe } = renderLesson();

    expect(probe().values.iter).toBe(90);
    fireEvent.click(screen.getByRole("button", { name: "次へ ▶" }));
    expect(probe()).toMatchObject({ index: 1, values: { iter: 20 } });
    expect(screen.queryByRole("button", { name: /自動で見る/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /もう一度/ })).not.toBeInTheDocument();
  });

  it("moves to the next step when a narrow screen's step text is tapped, but not on a predict step", () => {
    stubFrames();
    const { stepNodes, active } = renderLesson();

    fireEvent.click(stepNodes[0].querySelector("p")!);
    expect(active()).toBe(1);
    fireEvent.click(stepNodes[1].querySelector("p")!);
    expect(active()).toBe(2);
    fireEvent.click(stepNodes[2].querySelector("p")!);
    expect(active()).toBe(2);
  });

  it("starts a narrow screen's first step once the figure has come up to the middle", () => {
    const frames = stubFrames();
    const observers: Array<{ callback: IntersectionObserverCallback; options?: IntersectionObserverInit }> = [];
    vi.stubGlobal("IntersectionObserver", class {
      constructor(callback: IntersectionObserverCallback, options?: IntersectionObserverInit) {
        observers.push({ callback, options });
      }
      observe() {}
      disconnect() {}
    });
    const { probe } = renderLesson();

    frames.advance(3);
    expect(probe().values.iter).toBe(0);
    expect(observers.map((observer) => observer.options?.rootMargin)).toEqual(["0px 0px -50% 0px"]);
    act(() => observers[0].callback([{ isIntersecting: true } as IntersectionObserverEntry], {} as IntersectionObserver));
    frames.advance(1.8);
    expect(probe().values.iter).toBeCloseTo(36, 5);
  });

  it("follows the step crossing the middle of a wide screen, except while it scrolls there itself", () => {
    stubMedia("min-width");
    const frames = stubFrames();
    const observers: Array<{ callback: IntersectionObserverCallback; options?: IntersectionObserverInit }> = [];
    vi.stubGlobal("IntersectionObserver", class {
      constructor(callback: IntersectionObserverCallback, options?: IntersectionObserverInit) {
        observers.push({ callback, options });
      }
      observe() {}
      disconnect() {}
    });
    const scrolled: Element[] = [];
    Element.prototype.scrollIntoView = function scrollIntoView(this: Element) {
      scrolled.push(this);
    };
    const { markup, stepNodes, active, probe, onExit } = renderLesson();
    const cross = (node: Element) => act(() => observers
      .filter((observer) => observer.options?.rootMargin === "-50% 0px -50% 0px")
      .forEach((observer) => observer.callback(
        [{ isIntersecting: true, target: node } as IntersectionObserverEntry],
        {} as IntersectionObserver,
      )));

    expect(markup.root).toHaveClass("is-live", "is-wide");
    // The first step waits until its text reaches the middle; the figure alone being on screen
    // is not enough, or its motion would be over before the reader gets to the text.
    frames.advance(3);
    expect(probe().values.iter).toBe(0);
    cross(stepNodes[0]);
    frames.advance(1.8);
    expect(probe().values.iter).toBeCloseTo(36, 5);

    cross(stepNodes[3]);
    expect(active()).toBe(3);
    expect(probe()).toMatchObject({ index: 3, values: { eta: 0.053, iter: 0 } });

    fireEvent.click(screen.getByRole("button", { name: "◀ 前へ" }));
    expect(scrolled.at(-1)).toBe(stepNodes[2]);
    cross(stepNodes[3]); // the scroll it started passes other steps; they must not take over
    expect(active()).toBe(2);

    // In free play the step already showing may cross the middle again without taking the
    // figure back; a different step does take it back.
    vi.spyOn(performance, "now").mockReturnValue(performance.now() + 5_000);
    cross(stepNodes[3]);
    fireEvent.click(screen.getByRole("button", { name: "自分で動かす" }));
    expect(onExit).toHaveBeenCalledTimes(1);
    cross(stepNodes[3]);
    expect(probe().active).toBe(false);
    cross(stepNodes[2]);
    expect(probe()).toMatchObject({ active: true, index: 2 });
    vi.restoreAllMocks();
    delete (Element.prototype as { scrollIntoView?: unknown }).scrollIntoView;
  });

  it("lets automation hold any step at any second through window.__ocLessons", async () => {
    stubFrames();
    const { probe, active } = renderLesson();
    const handle = window.__ocLessons!["probe-figure"];

    expect(handle.steps).toEqual([
      { seconds: 6, caption: "一つ目の要点。", predict: false },
      { seconds: 4, caption: "二つ目の要点。", predict: false },
      { seconds: 3, caption: "どうなるか。", predict: true },
      { seconds: 5, caption: "四つ目の要点。", predict: false },
    ]);
    let shown: Promise<void> = Promise.resolve();
    act(() => { shown = handle.show(1); });
    expect(active()).toBe(1);
    expect(probe().values.iter).toBeCloseTo(20, 5); // the finished state by default
    act(() => { void handle.show(0, 2.25); });
    expect(probe()).toMatchObject({ index: 0 });
    expect(probe().values.iter).toBeCloseTo(45, 5);
    await expect(handle.show(9)).rejects.toThrow("no step 9");
    void shown;
  });

  it("keeps a held step where automation put it when a frame of the running clock is still due", () => {
    const due: FrameRequestCallback[] = [];
    vi.stubGlobal("requestAnimationFrame", (callback: FrameRequestCallback) => due.push(callback));
    vi.stubGlobal("cancelAnimationFrame", () => undefined);
    const { probe } = renderLesson();
    const frame = (now: number) => due.splice(0).forEach((callback) => callback(now));
    act(() => frame(1_000));
    act(() => frame(2_000)); // the first step's clock is one second in
    expect(probe().values.iter).toBeCloseTo(20, 5);
    // The browser can run the clock's next frame after `show` and before React stops the clock.
    act(() => {
      void window.__ocLessons!["probe-figure"].show(0);
      frame(2_100);
    });
    expect(probe().values.iter).toBeCloseTo(90, 5);
  });
});

describe("a lesson inside compiled content", () => {
  const figure = (id: string) => `<figure class="explorable" role="group" data-explorable-id="${id}" aria-label="図">`
    + '<div class="explorable-mount" data-explorable-mount><p class="explorable-fallback">別の図の代替</p></div>'
    + '<figcaption class="explorable-caption"><p>説明</p></figcaption></figure>';
  const gradientSteps: StepSpec[] = [
    {
      settings: { method: "gd", eta: 0.02, kappa: 20, beta: 0.5, x0: 4, y0: 3, iter: { from: 0, to: 100 } },
      body: "<p>学習率が小さい段。</p>",
    },
    {
      settings: { method: "gd", eta: 0.045, kappa: 20, beta: 0.5, x0: 4, y0: 3, iter: { from: 0, to: 100 } },
      body: "<p>学習率を上げた段。</p>",
    },
  ];

  it("mounts the figure under the lesson's control, without its own tour or controls", async () => {
    stubFrames();
    const html = lessonHtml("gradient-descent-valley", gradientSteps) + figure("convexity-chord");
    render(<MemoryRouter><CompiledContent page={{ html, toc: [] }} /></MemoryRouter>);

    const lesson = document.querySelector<HTMLElement>("[data-lesson-figure]")!;
    expect(await within(lesson).findByText("見る問い")).toBeInTheDocument();
    expect(screen.queryByText("静的な代替")).not.toBeInTheDocument();
    expect(lesson).toHaveClass("is-live");
    // The steps are the captions and the navigation; the reader's controls come with free play.
    expect(within(lesson).queryByRole("button", { name: /解説付きで見る/ })).not.toBeInTheDocument();
    expect(within(lesson).queryByRole("slider", { name: /学習率/ })).not.toBeInTheDocument();
    expect(within(lesson).getByText(/学習率 0\.020、/)).toBeInTheDocument();
    // The lesson's figure is mounted once, by the lesson; other figures mount as before.
    expect(within(lesson).getAllByText("見る問い")).toHaveLength(1);
    expect(screen.queryByText("別の図の代替")).not.toBeInTheDocument();

    // The figure's summary changes with every frame of a sweep, so it is not announced while the
    // lesson drives it; the lesson announces each step once instead.
    const summary = within(lesson).getByText(/学習率 0\.020、/);
    expect(summary).toHaveAttribute("aria-live", "off");
    expect(within(lesson).getByText("解説 1 / 2。学習率が小さい段。")).toHaveAttribute("aria-live", "polite");

    fireEvent.click(within(lesson).getByRole("button", { name: "次へ ▶" }));
    expect(within(lesson).getByText(/学習率 0\.045、/)).toBeInTheDocument();
    expect(within(lesson).getByText("解説 2 / 2。学習率を上げた段。")).toBeInTheDocument();

    // Changing mode swaps the bar's buttons; focus goes where the reader acts next.
    const takeOver = within(lesson).getByRole("button", { name: "自分で動かす" });
    takeOver.focus();
    fireEvent.click(takeOver);
    const eta = within(lesson).getByRole("slider", { name: /学習率/ });
    expect(eta).toHaveValue("0.045");
    expect(eta).toHaveFocus();
    expect(within(lesson).getByText(/学習率 0\.045、/)).toHaveAttribute("aria-live", "polite");

    fireEvent.click(within(lesson).getByRole("button", { name: "◀ 解説に戻る" }));
    expect(within(lesson).getByRole("button", { name: "自分で動かす" })).toHaveFocus();
  });

  it("keeps the static steps and fallback for a figure the site does not know", () => {
    render(<MemoryRouter><CompiledContent page={{ html: lessonHtml("not-registered", STEPS), toc: [] }} /></MemoryRouter>);

    expect(screen.getByText("静的な代替")).toBeInTheDocument();
    expect(document.querySelector("[data-lesson-figure]")).not.toHaveClass("is-live");
    expect(screen.getByText("収束する")).toBeInTheDocument();
  });
});
