import {
  useCallback,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
  type PointerEvent as ReactPointerEvent,
  type ReactNode,
  type RefObject,
} from "react";

import { Choice, PlayerBar } from "../../controls";
import { ExplorableFrame } from "../../ExplorableFrame";
import { EXPLORABLE_META } from "../../figureMeta";
import { fmt } from "../../format";
import { LiveMath, mi, mn, mo, paren, row, signed, sub } from "../../mathml";
import { numberSetting, stringSetting, type BeatSettings, type ResolvedSettings } from "../../scene";
import { clamp, useStageViewport } from "../../svg";
import { useSceneTour } from "../../useSceneTour";
import { useTimeline } from "../../useTimeline";
import {
  H0, H_TARGET, KAPPA, LAST_ITERATION, LITRES_PER_METRE, OUTFLOW, SEGMENTS, SUBSTEP_CHOICES, TOLERANCE,
  blendPlans, cost, cutFlow, defectNorms, defects, fineLevels, planAt, pumpedLitres, segmentLevels,
  type Plan, type Substeps,
} from "./math";
import "./style.css";

const ID = "tank-shooting-defect";
const MINUTES = 30;
const LEVEL_MAX = 1.1;
const FLOW_MAX = 2;
const KNOT_RANGE = [0.02, 1.08] as const;
/** The residual panel shows 10^-13 to 1 m; anything smaller sits on its floor. */
const LOG_FLOOR = -13;
const LOG_TOP = 0;
const UNUSED_BOUNDS = { xMin: 0, xMax: 1, yMin: 0, yMax: 1 };

/** What the figure draws at one instant, whether a lesson step or the reader's controls set it. */
interface View {
  plan: Plan;
  substeps: Substeps;
  /** How far the model's lines have been drawn from each knot, 0 to 1. */
  flow: number;
  /** How much of the 30 minutes of the finely solved level is drawn, 0 to 1. */
  fine: number;
  /** Segment (1-based) whose pump is turned down by 1 L/s; 0 for none. */
  cut: number;
}

interface Settings {
  iter: number;
  flow: number;
  cut: number;
  fine: number;
  substeps: Substeps;
  /** 0 = the plan solved with one Euler step, 1 = the plan re-solved with `substeps`. */
  resolve: number;
}

function readSettings(values: BeatSettings | ResolvedSettings): Settings {
  return {
    iter: numberSetting(values, "iter", 0),
    flow: numberSetting(values, "flow", 1),
    // Segment 1 pumps less than 1 L/s, so turning it down by 1 would be a negative flow.
    cut: Math.round(numberSetting(values, "cut", 0)) >= 2 ? Math.round(numberSetting(values, "cut", 0)) : 0,
    fine: numberSetting(values, "fine", 0),
    substeps: stringSetting(values, "substeps", SUBSTEP_CHOICES, "1"),
    resolve: clamp(numberSetting(values, "resolve", 1), 0, 1),
  };
}

/**
 * The view of a guided step. `resolve` below 1 keeps part of the plan that was solved with one
 * Euler step while the defects are already measured against the chosen discretisation: at 0 the
 * reader sees the old plan fail the new formula, and the sweep to 1 is the re-solve.
 */
function guidedView(values: ResolvedSettings): View {
  const now = readSettings(values);
  const solved = planAt(now.substeps, now.iter);
  const plan = now.resolve < 1 ? blendPlans(planAt("1", now.iter), solved, now.resolve) : solved;
  return { plan: cutFlow(plan, now.cut), substeps: now.substeps, flow: now.flow, fine: now.fine, cut: now.cut };
}

interface Chosen {
  substeps: Substeps;
  fine: boolean;
  /** A plan the reader dragged, kept only while the iteration and discretisation it started from stay. */
  custom: { at: string; plan: Plan } | null;
}

const INITIAL: Chosen = { substeps: "1", fine: false, custom: null };

export default function TankShootingDefect() {
  const [chosen, setChosen] = useState<Chosen>(INITIAL);
  const timeline = useTimeline(LAST_ITERATION, 0.5);
  const seek = timeline.seek;
  const tour = useSceneTour(
    ID,
    EXPLORABLE_META[ID].beats,
    useCallback((settings: BeatSettings) => {
      const last = readSettings(settings);
      setChosen({ substeps: last.substeps, fine: last.fine >= 0.5, custom: null });
      seek(last.iter);
    }, [seek]),
  );

  const key = `${chosen.substeps}|${timeline.position}`;
  const custom = chosen.custom?.at === key ? chosen.custom.plan : null;
  const view: View = tour.active
    ? guidedView(tour.values)
    : {
        plan: custom ?? planAt(chosen.substeps, timeline.position),
        substeps: chosen.substeps,
        flow: 1,
        fine: chosen.fine ? 1 : 0,
        cut: 0,
      };
  const { plan, substeps } = view;
  const steps = Number(substeps);

  const setPlan = (update: (plan: Plan) => Plan) => {
    const base = plan;
    setChosen((value) => ({
      ...value,
      custom: { at: key, plan: update(value.custom?.at === key ? value.custom.plan : base) },
    }));
  };
  const setKnot = (knot: number, level: number) => setPlan((current) => ({
    s: current.s.map((value, k) => (k === knot ? clamp(level, KNOT_RANGE[0], KNOT_RANGE[1]) : value)),
    q: current.q,
  }));
  const setFlow = (segment: number, flow: number) => setPlan((current) => ({
    s: current.s,
    q: current.q.map((value, k) => (k === segment ? clamp(flow, 0, FLOW_MAX) : value)),
  }));

  const d = useMemo(() => defects(plan, steps), [plan, steps]);
  const norms = defectNorms(d);
  const price = cost(plan);
  const pumped = pumpedLitres(plan);
  const fine = useMemo(() => (view.fine > 0 ? fineLevels(plan.q) : null), [plan.q, view.fine]);
  // The gaps and everything measured from them appear once the model's lines have arrived.
  const reveal = clamp((view.flow - 0.9) / 0.1, 0, 1);
  const measured = reveal > 0;
  const within = norms.max <= TOLERANCE;

  const summary = [
    `区間1つをオイラー法${steps}歩で進めた式との比較です。`,
    `費用は${fmt(price.total)}（目標からのずれ${fmt(price.track)}、ポンプ${fmt(price.pump)}）、ポンプが入れる水は${Math.round(pumped)} Lです。`,
    measured
      ? `最大残差は結び目${norms.argmax}の${small(norms.max)} mで、許容値${small(TOLERANCE)} mの${within ? "内側" : "外側"}です。継ぎ目で湧いた水は合計${litres(norms.total)} Lです。`
      : "残差はまだ測っていません。",
    view.fine >= 1 ? `同じ流量でタンクの式を細かく解くと、5分の水位は${fmt(fine?.[300] ?? H0, 3)} mで、結び目は${fmt(plan.s[1], 3)} mです。` : "",
  ].join("");

  return (
    <ExplorableFrame
      controls={
        <>
          <Choice<Substeps>
            legend="区間1つをオイラー法の何歩で進めるか"
            onChange={(value) => setChosen((current) => ({ ...current, substeps: value, custom: null }))}
            options={[
              { value: "1", label: "1歩" },
              { value: "2", label: "2歩" },
              { value: "5", label: "5歩" },
            ]}
            value={chosen.substeps}
          />
          <div className="tsd-options">
            <label className="tsd-toggle">
              <input
                checked={chosen.fine}
                onChange={(event) => setChosen((current) => ({ ...current, fine: event.target.checked }))}
                type="checkbox"
              />
              細かく解いた水位を重ねる
            </label>
            <button
              className="ex-action"
              onClick={() => {
                setChosen((current) => ({ ...current, custom: null }));
                seek(0);
              }}
              type="button"
            >
              初期推定に戻す
            </button>
          </div>
          <p className="ex-hint tsd-drag-hint">
            橙の丸と流量の棒は、上下にドラッグできます（矢印キーでも動きます）。反復を動かすと、ソルバーの計画に戻ります。
          </p>
        </>
      }
      id={ID}
      player={
        <PlayerBar
          positionText={custom ? "手で動かした計画" : `反復 ${fmt(timeline.position, 1)} / ${LAST_ITERATION}`}
          stepLabel="反復"
          timeline={timeline}
        />
      }
      readout={
        <Readout
          d={d}
          guided={tour.active}
          measured={measured}
          plan={plan}
          steps={steps}
        />
      }
      stage={
        <>
          <Stage
            d={d}
            fine={fine}
            onFlow={tour.active ? undefined : setFlow}
            onKnot={tour.active ? undefined : setKnot}
            reveal={reveal}
            view={view}
          />
          <Legend fine={view.fine > 0} />
        </>
      }
      summary={summary}
      tour={tour}
    />
  );
}

/** A small value as a number with a power of ten (6.5×10⁻⁵), or three decimals from 0.001 up. */
function small(value: number): string {
  const size = Math.abs(value);
  if (size === 0) return "0";
  if (size >= 0.001) return fmt(value, 3);
  if (size < 10 ** LOG_FLOOR) return "10⁻¹³未満";
  const [mantissa, exponent] = size.toExponential(1).split("e");
  const digits = "⁰¹²³⁴⁵⁶⁷⁸⁹";
  const power = String(Math.abs(Number(exponent))).split("").map((digit) => digits[Number(digit)]).join("");
  return `${value < 0 ? "−" : ""}${mantissa}×10⁻${power}`;
}

/** Metres of level as litres of water (area 1 m²), with a sign. */
function litres(metres: number): string {
  const value = Math.round(metres * LITRES_PER_METRE);
  if (value === 0) return "0";
  return `${value > 0 ? "+" : "−"}${Math.abs(value)}`;
}

interface Geometry {
  width: number;
  height: number;
  /** True when a segment is wide enough for a label with its unit. */
  roomy: boolean;
  segment: number;
  x(minutes: number): number;
  level: { top: number; bottom: number; y(h: number): number; value(py: number): number };
  pump: { top: number; bottom: number; y(q: number): number; value(py: number): number };
  residual: { top: number; bottom: number; y(log: number): number };
}

function geometry(width: number): Geometry {
  const roomy = width >= 440;
  const left = 46;
  const right = roomy ? 30 : 18;
  const plot = width - left - right;
  const title = 20;
  // The three panels together stay within one screen beside a lesson's steps (docs/explorables.md).
  const levelHeight = clamp(Math.round(width * 0.36), 165, 240);
  const levelTop = title;
  const levelBottom = levelTop + levelHeight;
  const pumpTop = levelBottom + 22 + title;
  const pumpBottom = pumpTop + 52;
  const residualTop = pumpBottom + 8 + title;
  const residualBottom = residualTop + 78;
  return {
    width,
    height: residualBottom + 22,
    roomy,
    segment: plot / SEGMENTS,
    x: (minutes) => left + (minutes / MINUTES) * plot,
    level: {
      top: levelTop,
      bottom: levelBottom,
      y: (h) => levelBottom - (h / LEVEL_MAX) * levelHeight,
      value: (py) => ((levelBottom - py) / levelHeight) * LEVEL_MAX,
    },
    pump: {
      top: pumpTop,
      bottom: pumpBottom,
      y: (q) => pumpBottom - (q / FLOW_MAX) * (pumpBottom - pumpTop),
      value: (py) => ((pumpBottom - py) / (pumpBottom - pumpTop)) * FLOW_MAX,
    },
    residual: {
      top: residualTop,
      bottom: residualBottom,
      y: (log) => residualBottom - ((clamp(log, LOG_FLOOR, LOG_TOP) - LOG_FLOOR) / (LOG_TOP - LOG_FLOOR)) * (residualBottom - residualTop),
    },
  };
}

interface StageProps {
  view: View;
  d: readonly number[];
  fine: readonly number[] | null;
  reveal: number;
  /** Present while the reader may drag; absent while a guided step drives the figure. */
  onKnot?(knot: number, level: number): void;
  onFlow?(segment: number, flow: number): void;
}

function Stage({ view, d, fine, reveal, onKnot, onFlow }: StageProps) {
  const { plan, flow, cut } = view;
  const steps = Number(view.substeps);
  const svgRef = useRef<SVGSVGElement>(null);
  const { ref, viewport } = useStageViewport(UNUSED_BOUNDS, 1);
  const g = useMemo(() => geometry(viewport.width), [viewport.width]);
  const { level, pump, residual } = g;
  const knotX = (k: number) => g.x((k * MINUTES) / SEGMENTS);
  const point = (x: number, y: number) => `${x.toFixed(1)} ${y.toFixed(1)}`;

  // Where the model carries each knot: one polyline per segment, drawn as far as `flow` says.
  const carried = plan.q.map((q, k) => {
    const levels = segmentLevels(plan.s[k], q, steps);
    const reach = clamp(flow, 0, 1) * steps;
    const whole = Math.floor(reach + 1e-9);
    const points = levels.slice(0, whole + 1).map((h, j) => [k + j / steps, h] as const);
    if (whole < steps && reach > whole) {
      const t = reach - whole;
      points.push([k + reach / steps, levels[whole] + (levels[whole + 1] - levels[whole]) * t]);
    }
    return { end: levels[steps], points };
  });

  const finePath = fine && view.fine > 0
    ? fine
        .slice(0, Math.floor(clamp(view.fine, 0, 1) * (fine.length - 1)) + 1)
        .filter((_, second) => second % 10 === 0)
        .map((h, i) => `${i === 0 ? "M" : "L"}${point(g.x((i * 10) / 60), level.y(h))}`)
        .join("")
    : "";

  const barWidth = Math.min(18, g.segment * 0.4);
  const within = Math.max(...d.map(Math.abs)) <= TOLERANCE;
  const flowDigits = g.segment >= 42 ? 3 : 2;

  return (
    <div className="ex-canvas" ref={ref}>
      <svg className="ex-svg tsd-svg" ref={svgRef} viewBox={`0 0 ${g.width} ${g.height}`}>
        <rect className="ex-ground" height={g.height} width={g.width} />

        {/* Segment boundaries run through the level and the pump panels: one segment, one flow. */}
        {Array.from({ length: SEGMENTS + 1 }, (_, k) => (
          <g key={k}>
            <line className="tsd-boundary" x1={knotX(k)} x2={knotX(k)} y1={level.top} y2={level.bottom} />
            <line className="tsd-boundary" x1={knotX(k)} x2={knotX(k)} y1={pump.top} y2={pump.bottom} />
            <text className="ex-axes-text" textAnchor="middle" x={knotX(k)} y={level.bottom + 15}>
              {k * 5}{k === SEGMENTS ? "分" : ""}
            </text>
          </g>
        ))}

        {/* 水位 */}
        <text className="tsd-title" x={g.x(0)} y={14}>水位（m）</text>
        <g className="ex-axes">
          {[0, 0.5, 1].map((h) => (
            <g key={h}>
              <line x1={g.x(0)} x2={g.x(MINUTES)} y1={level.y(h)} y2={level.y(h)} />
              <text textAnchor="end" x={g.x(0) - 7} y={level.y(h) + 4}>{h === 0 ? "0" : fmt(h, 1)}</text>
            </g>
          ))}
        </g>
        <line className="tsd-target" x1={g.x(0)} x2={g.x(MINUTES)} y1={level.y(H_TARGET)} y2={level.y(H_TARGET)} />
        <text className="ex-label tsd-target-label" x={g.x(0) + 5} y={level.y(H_TARGET) + 16}>目標</text>
        <path
          className="tsd-knot-link"
          d={plan.s.map((h, k) => `${k === 0 ? "M" : "L"}${point(knotX(k), level.y(h))}`).join("")}
        />
        {finePath && <path className="tsd-fine" d={finePath} />}
        {flow > 0 && carried.map(({ points }, k) => (
          <path
            className="tsd-carry"
            d={points.map(([segment, h], i) => `${i === 0 ? "M" : "L"}${point(knotX(segment), level.y(h))}`).join("")}
            key={k}
          />
        ))}
        {reveal > 0 && carried.map(({ end }, k) => {
          const x = knotX(k + 1);
          const yEnd = level.y(end);
          const yKnot = level.y(plan.s[k + 1]);
          const open = Math.abs(yEnd - yKnot) >= 1;
          const label = litres(d[k]);
          return (
            <g key={k} opacity={reveal}>
              {open && <line className="tsd-gap" x1={x} x2={x} y1={yEnd} y2={yKnot} />}
              <circle className="tsd-end" cx={x} cy={yEnd} r={4.5} />
              {open && label !== "0" && (
                <text className="ex-label tsd-gap-label" textAnchor="middle" x={x} y={Math.min(yEnd, yKnot) - 11}>
                  {label}{g.roomy ? " L" : ""}
                </text>
              )}
            </g>
          );
        })}
        <rect className="tsd-start" height={11} width={11} x={knotX(0) - 5.5} y={level.y(H0) - 5.5} />
        <text className="ex-label" x={knotX(0) + 12} y={level.y(H0) + 4}>最初の水位</text>
        {plan.s.slice(1).map((h, index) => {
          const knot = index + 1;
          return (
            <Handle
              className="tsd-knot-handle"
              key={knot}
              label={`結び目${knot}の水位 ${fmt(h, 3)} m`}
              max={KNOT_RANGE[1]}
              min={KNOT_RANGE[0]}
              onChange={onKnot && ((value) => onKnot(knot, value))}
              step={0.01}
              svgHeight={g.height}
              svgRef={svgRef}
              toValue={level.value}
              value={h}
            >
              <circle className="ex-handle-hit" cx={knotX(knot)} cy={level.y(h)} r={Math.min(20, g.segment / 2)} />
              <circle className="tsd-knot" cx={knotX(knot)} cy={level.y(h)} r={6.5} />
            </Handle>
          );
        })}

        {/* ポンプの流量 */}
        <text className="tsd-title" x={g.x(0)} y={pump.top - 7}>ポンプの流量（L/s）</text>
        <g className="ex-axes">
          {[0, 1, 2].map((q) => (
            <g key={q}>
              <line x1={g.x(0)} x2={g.x(MINUTES)} y1={pump.y(q)} y2={pump.y(q)} />
              <text textAnchor="end" x={g.x(0) - 7} y={pump.y(q) + 4}>{q}</text>
            </g>
          ))}
        </g>
        {plan.q.map((q, k) => {
          const x0 = knotX(k) + 3;
          const widthPx = g.segment - 6;
          const shown = clamp(q, 0, FLOW_MAX);
          const top = pump.y(shown);
          const turnedDown = cut === k + 1;
          return (
            <Handle
              className="tsd-flow-handle"
              key={k}
              label={`区間${k + 1}の流量 ${fmt(q, 3)} L/s`}
              max={FLOW_MAX}
              min={0}
              onChange={onFlow && ((value) => onFlow(k, value))}
              step={0.05}
              svgHeight={g.height}
              svgRef={svgRef}
              toValue={pump.value}
              value={q}
            >
              <rect className="ex-handle-hit" height={pump.bottom - pump.top + 8} width={g.segment} x={knotX(k)} y={pump.top - 8} />
              {turnedDown && (
                <rect className="tsd-flow-ghost" height={pump.bottom - pump.y(shown + 1)} width={widthPx} x={x0} y={pump.y(shown + 1)} />
              )}
              <rect className="tsd-flow-bar" height={Math.max(pump.bottom - top, 0)} width={widthPx} x={x0} y={top} />
              <line className="tsd-flow-top" x1={x0} x2={x0 + widthPx} y1={top} y2={top} />
              <text
                className={turnedDown ? "ex-label tsd-flow-value is-cut" : "ex-label tsd-flow-value"}
                textAnchor="middle"
                x={x0 + widthPx / 2}
                y={Math.max(top - 5, pump.top + 11)}
              >
                {fmt(q, flowDigits)}
              </text>
            </Handle>
          );
        })}

        {/* 結び目ごとの残差 */}
        <text className="tsd-title" x={g.x(0)} y={residual.top - 7}>結び目ごとの残差（m・対数）</text>
        {reveal > 0 && (
          <text
            className={within ? "tsd-verdict is-in" : "tsd-verdict is-out"}
            opacity={reveal}
            textAnchor="end"
            x={g.x(MINUTES)}
            y={residual.top - 7}
          >
            {within ? "許容値の内" : "許容値の外"}
          </text>
        )}
        <g className="ex-axes">
          {[0, -6, -12].map((power) => (
            <g key={power}>
              <line x1={g.x(0)} x2={g.x(MINUTES)} y1={residual.y(power)} y2={residual.y(power)} />
              <text textAnchor="end" x={g.x(0) - 7} y={residual.y(power) + (power === -6 ? 13 : 4)}>
                {power === 0 ? "1" : <>10<tspan dy={-5} fontSize="0.8em">{power === -6 ? "−6" : "−12"}</tspan></>}
              </text>
            </g>
          ))}
        </g>
        <line className="tsd-tolerance" x1={g.x(0) - 6} x2={g.x(MINUTES)} y1={residual.y(-6)} y2={residual.y(-6)} />
        <text className="tsd-tolerance-label" textAnchor="end" x={g.x(0) - 7} y={residual.y(-6) - 4}>許容値</text>
        {d.map((value, k) => {
          const size = Math.abs(value);
          const top = residual.y(size > 0 ? Math.log10(size) : LOG_FLOOR);
          return (
            <g key={k}>
              {reveal > 0 && (
                <rect
                  className={size > TOLERANCE ? "tsd-residual is-out" : "tsd-residual is-in"}
                  height={Math.max(residual.bottom - top, 2)}
                  opacity={reveal}
                  width={barWidth}
                  x={knotX(k + 1) - barWidth / 2}
                  y={Math.min(top, residual.bottom - 2)}
                />
              )}
              <text className="ex-axes-text" textAnchor="middle" x={knotX(k + 1)} y={residual.bottom + 15}>{k + 1}</text>
            </g>
          );
        })}
        <text className="ex-axes-text" textAnchor="end" x={g.x(0) - 7} y={residual.bottom + 15}>結び目</text>
      </svg>
    </div>
  );
}

interface HandleProps {
  className: string;
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  svgRef: RefObject<SVGSVGElement | null>;
  svgHeight: number;
  /** Value at a height of the SVG, in its own units. */
  toValue(py: number): number;
  /** Absent while a guided step drives the figure: the mark is then only a mark. */
  onChange?: (value: number) => void;
  children: ReactNode;
}

/** A mark that moves up and down: dragged with a pointer, nudged with the arrow keys. */
function Handle({ className, label, value, min, max, step, svgRef, svgHeight, toValue, onChange, children }: HandleProps) {
  const dragging = useRef(false);
  if (!onChange) return <g className={`${className} ex-handle is-fixed`}>{children}</g>;
  const move = (event: ReactPointerEvent<SVGGElement>) => {
    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect || rect.height === 0) return;
    onChange(clamp(toValue(((event.clientY - rect.top) / rect.height) * svgHeight), min, max));
  };
  const nudge = (event: KeyboardEvent<SVGGElement>) => {
    const direction = event.key === "ArrowUp" || event.key === "ArrowRight"
      ? 1
      : event.key === "ArrowDown" || event.key === "ArrowLeft" ? -1 : 0;
    if (direction === 0) return;
    event.preventDefault();
    onChange(clamp(value + direction * step * (event.shiftKey ? 5 : 1), min, max));
  };
  return (
    <g
      aria-label={label}
      aria-orientation="vertical"
      aria-valuemax={max}
      aria-valuemin={min}
      aria-valuenow={Number(value.toFixed(3))}
      className={`${className} ex-handle`}
      onKeyDown={nudge}
      onPointerCancel={() => { dragging.current = false; }}
      onPointerDown={(event) => {
        dragging.current = true;
        event.currentTarget.setPointerCapture?.(event.pointerId);
        event.preventDefault();
      }}
      onPointerMove={(event) => { if (dragging.current) move(event); }}
      onPointerUp={(event) => {
        dragging.current = false;
        event.currentTarget.releasePointerCapture?.(event.pointerId);
      }}
      role="slider"
      tabIndex={0}
    >
      {children}
    </g>
  );
}

/** Colour is never the only carrier: each mark is named once, next to a sample of it. */
function Legend({ fine }: { fine: boolean }) {
  return (
    <ul className="tsd-legend">
      <li><svg aria-hidden="true" height="12" viewBox="0 0 16 12" width="16"><circle className="tsd-knot" cx="8" cy="6" r="5" /></svg>置いた水位</li>
      <li><svg aria-hidden="true" height="12" viewBox="0 0 26 12" width="26"><path className="tsd-carry" d="M2 3L20 9" /><circle className="tsd-end" cx="21" cy="9" r="3" /></svg>式が運ぶ先</li>
      <li><svg aria-hidden="true" height="12" viewBox="0 0 10 12" width="10"><path className="tsd-gap" d="M5 1V11" /></svg>すき間（残差）</li>
      {fine && <li><svg aria-hidden="true" height="12" viewBox="0 0 26 12" width="26"><path className="tsd-fine" d="M1 6H25" /></svg>細かく解いた水位</li>}
    </ul>
  );
}

interface ReadoutProps {
  plan: Plan;
  d: readonly number[];
  steps: number;
  measured: boolean;
  guided: boolean;
}

function Readout({ plan, d, steps, measured, guided }: ReadoutProps) {
  const norms = defectNorms(d);
  const price = cost(plan);
  const within = norms.max <= TOLERANCE;
  // The cost bar is scaled to a little over the converged cost, 7.56.
  const share = (value: number) => `${clamp((value / 9) * 100, 0, 100)}%`;
  const water = litres(norms.total);
  return (
    <>
      <div className="tsd-readout">
        <p className="tsd-cost">
          <span className="tsd-cost-name">費用 J</span>
          <strong>{fmt(price.total)}</strong>
          <span aria-hidden="true" className="tsd-cost-bar">
            <span className="tsd-cost-track" style={{ width: share(price.track) }} />
            <span className="tsd-cost-pump" style={{ width: share(price.pump) }} />
          </span>
          <span className="tsd-cost-parts">ずれ {fmt(price.track)} ＋ ポンプ {fmt(price.pump)}</span>
        </p>
        <dl className="tsd-stats">
          <div>
            <dt>ポンプが入れる水</dt>
            <dd>{Math.round(pumpedLitres(plan))} L</dd>
          </div>
          <div>
            <dt>継ぎ目で湧いた水</dt>
            <dd className={measured && water !== "0" ? "tsd-out" : undefined}>{measured ? `${water} L` : "—"}</dd>
          </div>
          <div>
            <dt>最大残差</dt>
            <dd className={measured ? (within ? "tsd-in" : "tsd-out") : undefined}>
              {measured ? `${small(norms.max)} m` : "—"}
            </dd>
          </div>
          <div>
            <dt>二乗和の平方根</dt>
            <dd>{measured ? `${small(norms.l2)} m` : "—"}</dd>
          </div>
        </dl>
      </div>
      {!guided && <Equation d={d} knot={norms.argmax} plan={plan} steps={steps} />}
    </>
  );
}

/** The defect of one knot with the current numbers put in, short lines so a phone never scrolls. */
function Equation({ plan, d, knot, steps }: { plan: Plan; d: readonly number[]; knot: number; steps: number }) {
  const from = plan.s[knot - 1];
  const flow = plan.q[knot - 1];
  const end = plan.s[knot] - d[knot - 1];
  const s = (k: number) => sub(mi("s"), mn(String(k)));
  const q = (k: number) => sub(mi("q"), mn(String(k)));
  const fd = sub(mi("f"), mi("d"));
  const out = OUTFLOW * Math.sqrt(Math.max(from, 0));
  return (
    <section aria-label="いちばん大きい残差" className="ex-equation">
      <p className="ex-eyebrow">いちばん大きい残差（結び目{knot}）</p>
      <LiveMath
        block
        label={`結び目${knot}の残差は、置いた水位から、手前の結び目をタンクの式で5分進めた水位を引いたもの`}
        markup={row(sub(mi("d"), mn(String(knot))), mo("="), s(knot), mo("−"), fd, paren(s(knot - 1), mo(","), q(knot - 1)))}
      />
      {steps === 1 ? (
        <>
          <LiveMath
            block
            label={`5分進めた水位は、手前の水位に、流入から流出を引いた量の ${fmt(KAPPA, 1)} 倍を足したもの`}
            markup={row(
              fd, mo("="), s(knot - 1), mo("+"), mn(fmt(KAPPA, 1)),
              paren(q(knot - 1), mo("−"), mn(fmt(OUTFLOW, 3)), `<msqrt>${s(knot - 1)}</msqrt>`),
            )}
          />
          <LiveMath
            block
            label={`${fmt(from, 3)} に、${fmt(KAPPA, 1)} 掛ける、流入 ${fmt(flow, 3)} 引く流出 ${fmt(out, 3)} を足して ${fmt(end, 3)}`}
            markup={row(
              mo("="), mn(fmt(from, 3)), mo("+"), mn(fmt(KAPPA, 1)),
              paren(mn(fmt(flow, 3)), mo("−"), mn(fmt(out, 3))), mo("="), signed(fmt(end, 3)),
            )}
          />
        </>
      ) : (
        <LiveMath
          block
          label={`5分をオイラー法${steps}歩で進めた水位は ${fmt(end, 3)}`}
          markup={row(fd, mo("="), signed(fmt(end, 3)))}
        />
      )}
      <LiveMath
        block
        label={`残差は ${fmt(plan.s[knot], 3)} 引く ${fmt(end, 3)} で ${small(d[knot - 1])} メートル`}
        markup={row(
          sub(mi("d"), mn(String(knot))), mo("="), mn(fmt(plan.s[knot], 3)), mo("−"), signed(fmt(end, 3)),
          mo("="), mn(small(d[knot - 1])), "<mtext>&#160;m</mtext>",
        )}
      />
      {steps > 1 && <p className="ex-hint">5分を{steps}歩に刻んで、同じ式を{steps}回使います。</p>}
    </section>
  );
}
