import { useId, type ReactNode } from "react";

import { TourPanel, TourStart } from "./controls";
import { EXPLORABLE_META } from "./meta";
import type { SceneTour } from "./useSceneTour";

interface ExplorableFrameProps {
  /** Registry id; supplies the guiding question and the stated limits. */
  id: string;
  /** Sliders and choices that change the situation. */
  controls: ReactNode;
  /** The animated figure. */
  stage: ReactNode;
  /** Play / scrub bar, when the figure animates. */
  player?: ReactNode;
  /** What the current state means, in numbers and words. */
  readout: ReactNode;
  /**
   * Text for readers who cannot see the figure. It describes the outcome for the current
   * settings, so it changes when a control moves, not on every animation frame.
   */
  summary: string;
  /** Guided scene, when the registry gives this figure beats. It replaces the controls while on. */
  tour?: SceneTour;
}

/**
 * Shared chrome so every explorable answers the same three questions in the same place:
 * what am I looking at, what can I change, and what does the current state mean.
 */
export function ExplorableFrame({
  id, controls, stage, player, readout, summary, tour,
}: ExplorableFrameProps) {
  const guided = tour?.active ?? false;
  const meta = EXPLORABLE_META[id];
  const summaryId = useId();
  return (
    <div className={guided ? "ex-frame is-guided" : "ex-frame"}>
      <p className="ex-question">
        <span>見る問い</span>
        {meta.question}
      </p>
      {tour && <TourStart tour={tour} />}
      {guided && tour ? <TourPanel tour={tour} /> : <div className="ex-controls">{controls}</div>}
      <div aria-describedby={summaryId} aria-label="図" className="ex-stage" role="group">
        {stage}
      </div>
      <p aria-live="polite" className="ex-sr-only" id={summaryId}>{summary}</p>
      {!guided && player}
      <div className="ex-readout">{readout}</div>
      <details className="ex-limits">
        <summary>この図の前提と、読み取れないこと</summary>
        <dl>
          <dt>固定している条件</dt>
          <dd>{meta.fixedConditions}</dd>
          <dt>読み取れないこと</dt>
          <dd>{meta.notImplied}</dd>
        </dl>
      </details>
    </div>
  );
}
