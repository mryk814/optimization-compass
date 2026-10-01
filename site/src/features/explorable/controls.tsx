import { useId, type ReactNode } from "react";

import { TIMELINE_SPEEDS, type Timeline, type TimelineSpeed } from "./useTimeline";

interface SliderProps {
  label: ReactNode;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange(value: number): void;
  /** Text shown beside the label, e.g. "0.040". */
  display: string;
  /** Plain-text value for assistive technology when `display` is not enough. */
  valueText?: string;
  hint?: ReactNode;
  disabled?: boolean;
}

export function Slider({
  label, value, min, max, step, onChange, display, valueText, hint, disabled,
}: SliderProps) {
  const id = useId();
  return (
    <div className="ex-slider">
      <label htmlFor={id}>
        <span className="ex-slider-label">{label}</span>
        <output className="ex-slider-value" htmlFor={id}>{display}</output>
      </label>
      <input
        aria-valuetext={valueText ?? display}
        disabled={disabled}
        id={id}
        max={max}
        min={min}
        onChange={(event) => onChange(Number(event.target.value))}
        step={step}
        type="range"
        value={value}
      />
      {hint && <p className="ex-hint">{hint}</p>}
    </div>
  );
}

interface ChoiceProps<T extends string> {
  legend: string;
  value: T;
  options: ReadonlyArray<{ value: T; label: string }>;
  onChange(value: T): void;
}

/** A small radio group drawn as connected buttons. */
export function Choice<T extends string>({ legend, value, options, onChange }: ChoiceProps<T>) {
  const name = useId();
  return (
    <fieldset className="ex-choice">
      <legend>{legend}</legend>
      <div>
        {options.map((option) => (
          <label className={option.value === value ? "is-selected" : undefined} key={option.value}>
            <input
              checked={option.value === value}
              name={name}
              onChange={() => onChange(option.value)}
              type="radio"
              value={option.value}
            />
            <span>{option.label}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

interface PlayerBarProps {
  timeline: Timeline;
  /** What one step is called, e.g. "反復 k". */
  stepLabel: string;
  /** Text for the current position, e.g. "k = 12 / 60". */
  positionText: string;
}

export function PlayerBar({ timeline, stepLabel, positionText }: PlayerBarProps) {
  const id = useId();
  const { playing, reducedMotion } = timeline;
  return (
    <div aria-label="再生の操作" className="ex-player" role="group">
      <div className="ex-player-buttons">
        <button
          aria-label="最初から"
          onClick={timeline.restart}
          title="最初から"
          type="button"
        >
          ⏮
        </button>
        <button
          aria-label="1つ戻る"
          disabled={timeline.atStart}
          onClick={timeline.stepBackward}
          title="1つ戻る"
          type="button"
        >
          ◀
        </button>
        <button
          aria-pressed={playing}
          className="ex-play"
          disabled={reducedMotion}
          onClick={timeline.toggle}
          type="button"
        >
          {playing ? "⏸ 一時停止" : "▶ 再生"}
        </button>
        <button
          aria-label="1つ進む"
          disabled={timeline.atEnd}
          onClick={timeline.stepForward}
          title="1つ進む"
          type="button"
        >
          ▶
        </button>
        <button
          aria-label="最後まで進める"
          disabled={timeline.atEnd}
          onClick={timeline.finish}
          title="最後まで進める"
          type="button"
        >
          ⏭
        </button>
        <label className="ex-speed">
          <span>速さ</span>
          <select
            onChange={(event) => timeline.setSpeed(Number(event.target.value) as TimelineSpeed)}
            value={timeline.speed}
          >
            {TIMELINE_SPEEDS.map((speed) => (
              <option key={speed} value={speed}>{speed}×</option>
            ))}
          </select>
        </label>
      </div>
      <div className="ex-scrub">
        <label htmlFor={id}>{stepLabel}</label>
        <input
          aria-valuetext={positionText}
          id={id}
          max={timeline.length}
          min={0}
          onChange={(event) => timeline.seek(Number(event.target.value))}
          step={1}
          type="range"
          value={timeline.step}
        />
        <output htmlFor={id}>{positionText}</output>
      </div>
      {reducedMotion && (
        <p className="ex-hint">
          OSの「視差効果を減らす」設定を尊重して、自動再生は止めています。1つ進む／戻るで確認できます。
        </p>
      )}
    </div>
  );
}
