import { useCallback, useMemo, useRef, useState, type KeyboardEvent } from "react";

import { Slider } from "../../controls";
import { ExplorableFrame } from "../../ExplorableFrame";
import { EXPLORABLE_META } from "../../figureMeta";
import { fmt } from "../../format";
import type { Bounds } from "../../math/contours";
import {
  ARTICLE_LP,
  ARTICLE_REVENUE,
  feasibleVertices,
  levelLine,
  objectiveValue,
  optimalVertices,
  type HalfPlane,
  type Vec2,
} from "../../math/lp2d";
import { LiveMath, mn, mo, row } from "../../mathml";
import {
  numberSetting,
  resolveSettings,
  stringSetting,
  type BeatSettings,
  type ResolvedSettings,
} from "../../scene";
import { clamp, makeScale, polylinePath, useDomainDrag, useStageViewport, type Scale, type Viewport } from "../../svg";
import { useSceneTour } from "../../useSceneTour";
import { STOCKS, followPlan, levelChord, shortages, stockUsage, usesUp, violated } from "./math";
import "./style.css";

const ID = "lp-vertex-walk";
/** How far the plan may go: past the stock on purpose, so the reader can ask "can I bake this?". */
const PLAN_MAX: Vec2 = [8, 4.5];
/** The plane shows this many breads and croissants, a little past what a plan may reach. */
const SPAN: Vec2 = [8.3, 4.7];
/**
 * Room for the tick labels and axis names, in pixels. Margins given in loaves would shrink with
 * the screen; these keep the labels whole on a phone and give the rest of the width to the plane.
 */
const MARGIN = { left: 42, right: 10, top: 24, bottom: 40 };
/** `useStageViewport` is only asked for the width; the plane's shape comes from `planeViewport`. */
const MEASURE: Bounds = { xMin: 0, xMax: 1, yMin: 0, yMax: 1 };

/** One loaf is as wide as one croissant is tall, whatever the width. */
function planeViewport(width: number): Viewport {
  const unit = (width - MARGIN.left - MARGIN.right) / SPAN[0];
  const height = Math.round(MARGIN.top + SPAN[1] * unit + MARGIN.bottom);
  const yMin = -MARGIN.bottom / unit;
  return {
    width,
    height,
    bounds: { xMin: -MARGIN.left / unit, xMax: SPAN[0] + MARGIN.right / unit, yMin, yMax: yMin + height / unit },
  };
}

const PRICE_MAX = 6;
const VERTICES = feasibleVertices(ARTICLE_LP);
const CENTROID: Vec2 = [
  VERTICES.reduce((sum, vertex) => sum + vertex[0], 0) / VERTICES.length,
  VERTICES.reduce((sum, vertex) => sum + vertex[1], 0) / VERTICES.length,
];
/** What is drawn, each adding to the one before. A lesson reveals them in this order. */
const LAYERS = ["plan", "stock", "revenue", "answer"] as const;
const [, STOCK, REVENUE, ANSWER] = [0, 1, 2, 3];
const FOLLOW = ["off", "best"] as const;
/** A plan that follows the best corner takes this long to slide to a new one, so the jump can be traced. */
const SLIDE_S = 0.45;
/**
 * A usage bar's box is exactly the stock, so a stock used up is a box filled to its end. The row is
 * this many stocks wide: the rest, to the right of the box, is where a shortage is drawn in red.
 */
const BAR_SPAN = 1.4;

interface Chosen {
  plan: Vec2;
  cost: Vec2;
}

interface Shown extends Chosen {
  layer: number;
  follow: boolean;
}

const INITIAL: Chosen = { plan: [2, 1.5], cost: ARTICLE_REVENUE };

/** What a lesson step or the reader's own controls ask for, as the figure draws it. */
function fromValues(values: BeatSettings | ResolvedSettings, base: Chosen): Shown {
  const cost: Vec2 = [numberSetting(values, "c1", base.cost[0]), numberSetting(values, "c2", base.cost[1])];
  const asked: Vec2 = [numberSetting(values, "x1", base.plan[0]), numberSetting(values, "x2", base.plan[1])];
  const follow = stringSetting(values, "follow", FOLLOW, "off") === "best";
  return {
    layer: LAYERS.indexOf(stringSetting(values, "layers", LAYERS, "answer")),
    cost,
    plan: follow ? followPlan(VERTICES, cost, asked) : asked,
    follow,
  };
}

const apart = (a: Vec2, b: Vec2) => Math.hypot(a[0] - b[0], a[1] - b[1]);
const snap = (value: number) => Math.round(value * 10) / 10;

/** A count or an amount as the article prints it: one decimal, and none when it is whole. */
function num(value: number): string {
  const text = fmt(Math.round(value * 10) / 10, 1);
  return text.endsWith(".0") ? text.slice(0, -2) : text;
}

const planWords = (plan: Vec2) => `食パン ${num(plan[0])}個・クロワッサン ${num(plan[1])}個`;

export default function LpVertexWalk() {
  const [chosen, setChosen] = useState<Chosen>(INITIAL);
  // Leaving the lesson keeps what its last step was showing, so the reader continues from there.
  const tour = useSceneTour(
    ID,
    EXPLORABLE_META[ID].beats,
    useCallback((settings: BeatSettings) => setChosen((value) => {
      const { plan, cost } = fromValues(settings, value);
      return { plan, cost };
    }), []),
  );
  const svgRef = useRef<SVGSVGElement>(null);
  const { ref: stageRef, viewport: measured } = useStageViewport(MEASURE, 1);
  const viewport = useMemo(() => planeViewport(measured.width), [measured.width]);
  const scale = useMemo(() => makeScale(viewport), [viewport]);

  const beat = tour.active ? tour.beat : undefined;
  const free: Shown = { ...chosen, layer: ANSWER, follow: false };
  const at = (seconds: number): Shown => (
    beat ? fromValues(resolveSettings(beat.settings, seconds, beat.durationS), chosen) : free
  );
  const now = at(tour.local);
  // Where the step began stays on screen, faint, so what the step changed can be seen.
  const began = beat ? at(0) : undefined;
  // What a reader who cannot see the figure is told: the step's outcome, not every frame of it.
  const settled = beat ? at(beat.durationS) : now;

  const { layer, cost } = now;
  const plan = slidingPlan(now, at, tour.local);
  const usage = stockUsage(plan);
  const short = shortages(plan);
  const out = violated(plan);
  const revenue = objectiveValue(cost, plan);
  const zeroPrice = cost[0] === 0 && cost[1] === 0;
  const best = optimalVertices(VERTICES, cost);
  const tie = best.length > 1 && !zeroPrice;
  const chord = levelChord(VERTICES, cost, revenue);
  const beganLine = began && began.layer >= REVENUE && !sameLine(began, now) ? began : undefined;

  const movePlan = (update: (plan: Vec2) => Vec2) => setChosen((value) => {
    const next = update(value.plan);
    return { ...value, plan: [clamp(snap(next[0]), 0, PLAN_MAX[0]), clamp(snap(next[1]), 0, PLAN_MAX[1])] };
  });
  const drag = useDomainDrag({ svgRef, viewport, onDrag: (x, y) => movePlan(() => [x, y]) });
  const nudgePlan = (event: KeyboardEvent<SVGGElement>) => {
    const amount = event.shiftKey ? 0.5 : 0.1;
    const delta: Record<string, Vec2> = {
      ArrowLeft: [-amount, 0],
      ArrowRight: [amount, 0],
      ArrowUp: [0, amount],
      ArrowDown: [0, -amount],
    };
    const move = delta[event.key];
    if (!move) return;
    event.preventDefault();
    movePlan((point) => [point[0] + move[0], point[1] + move[1]]);
  };
  const setCost = (index: 0 | 1, price: number) => setChosen((value) => ({
    ...value,
    cost: index === 0 ? [price, value.cost[1]] : [value.cost[0], price],
  }));

  const verdictText = verdict(cost);
  const summary = describe(settled);

  return (
    <ExplorableFrame
      controls={
        <>
          <Slider
            display={fmt(cost[0], 1)}
            hint="食パンを1個売ると入る金額（百円）。記事の値は 3。"
            label="食パン1個の売上"
            max={PRICE_MAX}
            min={0}
            onChange={(price) => setCost(0, price)}
            step={0.5}
            value={cost[0]}
          />
          <Slider
            display={fmt(cost[1], 1)}
            hint="クロワッサンを1個売ると入る金額（百円）。記事の値は 4。"
            label="クロワッサン1個の売上"
            max={PRICE_MAX}
            min={0}
            onChange={(price) => setCost(1, price)}
            step={0.5}
            value={cost[1]}
          />
          <div className="ex-button-row">
            <button
              className="ex-action"
              disabled={zeroPrice}
              onClick={() => setChosen((value) => ({ ...value, plan: VERTICES[best[0]] }))}
              type="button"
            >
              いちばん良い角へ
            </button>
          </div>
        </>
      }
      id={ID}
      readout={
        <>
          {layer >= STOCK && (
            <section aria-label="材料の使用量と売上" className="ex-equation lpw-usage">
              <div className="lpw-usage-head">
                <span className="ex-eyebrow">材料の使用量</span>
                <span className={out ? "lpw-status is-over" : "lpw-status is-ok"}>{stockStatus(plan)}</span>
              </div>
              {STOCKS.map((stock, index) => (
                <UsageBar
                  full={usesUp(plan, index)}
                  key={stock.name}
                  limit={stock.limit}
                  name={stock.name}
                  short={short[index]}
                  used={usage[index]}
                />
              ))}
              {layer >= REVENUE && (
                <div className="lpw-revenue">
                  <span className="lpw-revenue-name">売上（百円）</span>
                  <LiveMath
                    block
                    label={`売上は ${num(cost[0])} × ${num(plan[0])} + ${num(cost[1])} × ${num(plan[1])} = ${num(revenue)}`}
                    markup={row(
                      mn(num(cost[0])), mo("×"), mn(num(plan[0])), mo("+"),
                      mn(num(cost[1])), mo("×"), mn(num(plan[1])), mo("="), mn(num(revenue)),
                    )}
                  />
                </div>
              )}
            </section>
          )}
          {!tour.active && (
            <>
              <section aria-label="角ごとの売上">
                <p className="ex-eyebrow">焼ける範囲の角と、その売上</p>
                <table className="ex-table">
                  <thead>
                    <tr><th scope="col">角の焼き方</th><th scope="col">売上</th><th scope="col" /></tr>
                  </thead>
                  <tbody>
                    {VERTICES.map((vertex, index) => {
                      const isBest = best.includes(index) && !zeroPrice;
                      return (
                        <tr className={isBest ? "ex-row-best" : undefined} key={index}>
                          <th className="lpw-corner-name" scope="row">{planWords(vertex)}</th>
                          <td>{num(objectiveValue(cost, vertex))}</td>
                          <td>{isBest ? "最良" : ""}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </section>
              <p className={`ex-verdict ${zeroPrice ? "ex-tone-slow" : "ex-tone-good"}`}>{verdictText}</p>
            </>
          )}
        </>
      }
      stage={
        <figure className="ex-panel">
          <figcaption className="lpw-plan-text">
            <span>いまの計画：<strong>{planWords(plan)}</strong></span>
            {layer >= REVENUE && <span className="lpw-plan-revenue">売上 {num(revenue)}</span>}
          </figcaption>
          <div className="ex-canvas" ref={stageRef}>
            <svg className="ex-svg" ref={svgRef} viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
              <defs>
                {/* Lines stop at the axes and under the axis name: a negative count is not a plan. */}
                <clipPath id="lpw-plane">
                  <rect height={scale.py(0) - MARGIN.top} width={viewport.width - scale.px(0)} x={scale.px(0)} y={MARGIN.top} />
                </clipPath>
                <marker id="lpw-arrow-head" markerHeight="8" markerWidth="8" orient="auto-start-reverse" refX="6" refY="4">
                  <path className="ex-arrowhead" d="M0 0L8 4L0 8z" />
                </marker>
              </defs>
              <rect className="ex-ground" height={viewport.height} width={viewport.width} />
              <Axes plan={plan} scale={scale} viewport={viewport} />
              {layer >= STOCK && (
                <>
                  <path className="ex-feasible" d={polylinePath(VERTICES, scale) + "Z"} />
                  {/* Named until the corners' revenues take this place; by then the steps have used the name. */}
                  {layer < ANSWER && (
                    <text className="lpw-range-name" x={scale.px(0.5)} y={scale.py(2.9)}>焼ける範囲</text>
                  )}
                  <StockLine constraint={ARTICLE_LP[0]} scale={scale} viewport={viewport} />
                  <StockLine constraint={ARTICLE_LP[1]} scale={scale} viewport={viewport} />
                </>
              )}
              {beganLine && <LevelLine className="lpw-line-ghost" scale={scale} shown={beganLine} viewport={viewport} />}
              {layer >= REVENUE && !zeroPrice && (
                <>
                  <LevelLine className="lpw-line" scale={scale} shown={{ ...now, plan }} viewport={viewport} />
                  {chord.length > 0 && (
                    <line
                      className="lpw-chord"
                      x1={scale.px(chord[0][0])}
                      x2={scale.px(chord[chord.length - 1][0])}
                      y1={scale.py(chord[0][1])}
                      y2={scale.py(chord[chord.length - 1][1])}
                    />
                  )}
                </>
              )}
              {layer >= ANSWER && tie && (
                <line
                  className="lpw-chord"
                  x1={scale.px(VERTICES[best[0]][0])}
                  x2={scale.px(VERTICES[best[1]][0])}
                  y1={scale.py(VERTICES[best[0]][1])}
                  y2={scale.py(VERTICES[best[1]][1])}
                />
              )}
              {layer >= ANSWER && VERTICES.map((vertex, index) => {
                const isBest = best.includes(index) && !zeroPrice;
                // The plan standing on a corner already says that corner's revenue.
                const label = apart(vertex, plan) > 0.3 && cornerLabel(vertex, scale);
                return (
                  <g key={index}>
                    <circle className="ex-vertex" cx={scale.px(vertex[0])} cy={scale.py(vertex[1])} r={5} />
                    {isBest && <circle className="lpw-best-ring" cx={scale.px(vertex[0])} cy={scale.py(vertex[1])} r={13} />}
                    {label && (
                      <text className={isBest ? "ex-label lpw-corner-value is-best" : "ex-label lpw-corner-value"} {...label}>
                        売上 {num(objectiveValue(cost, vertex))}
                      </text>
                    )}
                  </g>
                );
              })}
              {layer <= STOCK && <DropLines plan={plan} scale={scale} />}
              {began && apart(began.plan, plan) > 0.05 && <Diamond className="lpw-plan-ghost" plan={began.plan} scale={scale} />}
              {/* A plan the stock cannot cover has nowhere better to be pushed to: it has to come back first. */}
              {layer >= REVENUE && !zeroPrice && !out && (
                <RevenueArrow cost={cost} named={layer === REVENUE} plan={plan} scale={scale} viewport={viewport} />
              )}
              {/* After the arrow and the lines, so a stock's name stays readable where they pass it. */}
              {layer >= STOCK && (
                <>
                  <StockName constraint={ARTICLE_LP[0]} scale={scale} viewport={viewport} />
                  <StockName constraint={ARTICLE_LP[1]} scale={scale} viewport={viewport} />
                </>
              )}
              <g
                aria-label={`いまの計画。${planWords(plan)}。${layer >= STOCK ? `${stockStatus(plan)}。` : ""}${
                  tour.active ? "" : "ドラッグか矢印キーで動かせます。"
                }`}
                aria-roledescription={tour.active ? undefined : "2次元のつまみ"}
                className={tour.active ? undefined : "ex-handle"}
                onKeyDown={tour.active ? undefined : nudgePlan}
                role="group"
                tabIndex={tour.active ? undefined : 0}
                {...(tour.active ? {} : drag)}
              >
                <circle className="ex-handle-hit" cx={scale.px(plan[0])} cy={scale.py(plan[1])} r={20} />
                <Diamond className={out && layer >= STOCK ? "lpw-plan is-out" : "lpw-plan"} plan={plan} scale={scale} />
              </g>
              <PlanCounts plan={plan} scale={scale} />
            </svg>
          </div>
          {!tour.active && (
            <p className="ex-hint lpw-legend">
              青緑は在庫の中で焼ける範囲、橙の線は売上がいまの計画と同じになる計画、矢印は売上が増える向きです。
            </p>
          )}
        </figure>
      }
      summary={summary}
      tour={tour}
    />
  );
}

/**
 * A plan that follows the best corner slides to a new corner over `SLIDE_S` instead of jumping.
 * The slide is a function of the step's own clock, so a still or a recording of second `local`
 * always shows the same frame.
 */
function slidingPlan(now: Shown, at: (seconds: number) => Shown, local: number): Vec2 {
  if (!now.follow) return now.plan;
  const from = Math.max(0, local - SLIDE_S);
  const before = at(from).plan;
  if (apart(before, now.plan) < 1e-9) return now.plan;
  // The corner changed between `from` and `local`; find when.
  let low = from;
  let high = local;
  for (let iteration = 0; iteration < 30; iteration += 1) {
    const middle = (low + high) / 2;
    if (apart(at(middle).plan, now.plan) < 1e-9) high = middle;
    else low = middle;
  }
  const progress = clamp((local - high) / SLIDE_S, 0, 1);
  const eased = progress * progress * (3 - 2 * progress);
  return [before[0] + (now.plan[0] - before[0]) * eased, before[1] + (now.plan[1] - before[1]) * eased];
}

/** True when both states draw the same equal-revenue line. */
function sameLine(a: Shown, b: Shown): boolean {
  return a.cost[0] === b.cost[0] && a.cost[1] === b.cost[1]
    && Math.abs(objectiveValue(a.cost, a.plan) - objectiveValue(b.cost, b.plan)) < 1e-6;
}

function stockStatus(plan: Vec2): string {
  const short = shortages(plan);
  if (short.some((amount) => amount > 0)) {
    const parts = STOCKS.flatMap((stock, index) => (short[index] > 0 ? [`${stock.name} ${num(short[index])}`] : []));
    return `不足：${parts.join("、")}`;
  }
  const full = STOCKS.filter((_, index) => usesUp(plan, index)).map((stock) => stock.name);
  if (full.length === STOCKS.length) return "小麦粉もバターも使い切りです";
  if (full.length === 1) return `${full[0]}を使い切りました`;
  return "在庫の中に収まっています";
}

function verdict(cost: Vec2): string {
  if (cost[0] === 0 && cost[1] === 0) return "売上がどちらも 0 なら、どの計画でも売上は 0 です。";
  const best = optimalVertices(VERTICES, cost);
  const value = num(objectiveValue(cost, VERTICES[best[0]]));
  if (best.length > 1) {
    return `${best.map((index) => planWords(VERTICES[index])).join(" と ")} を結ぶ辺のどこでも、売上は ${value} で最大です。`;
  }
  return `売上がいちばん大きい計画は ${planWords(VERTICES[best[0]])} で、売上は ${value} です。`;
}

function describe({ layer, plan, cost }: Shown): string {
  const parts = [`いまの計画は ${planWords(plan)} です。`];
  if (layer >= STOCK) parts.push(`${stockStatus(plan)}。`);
  if (layer >= REVENUE) {
    parts.push(`1個あたりの売上は食パン ${num(cost[0])}、クロワッサン ${num(cost[1])} で、この計画の売上は ${num(objectiveValue(cost, plan))} です。`);
  }
  if (layer >= ANSWER) parts.push(verdict(cost));
  return parts.join("");
}

interface BarProps {
  name: string;
  used: number;
  limit: number;
  short: number;
  full: boolean;
}

function UsageBar({ name, used, limit, short, full }: BarProps) {
  const percent = (share: number) => `${Math.min(Math.max(share, 0), 1) * 100}%`;
  const flag = short > 0 ? "超過" : full ? "使い切り" : "";
  return (
    <div className="lpw-bar">
      <span className="lpw-bar-name">{name}</span>
      <span
        aria-label={`${name}は ${limit} のうち ${num(used)} を使います。${flag}`}
        className="lpw-bar-track"
        role="img"
      >
        <span className="lpw-bar-box" style={{ width: percent(1 / BAR_SPAN) }}>
          <span className="lpw-bar-fill" style={{ width: percent(used / limit) }} />
        </span>
        {short > 0 && (
          <span
            className="lpw-bar-over"
            style={{ left: percent(1 / BAR_SPAN), width: percent(Math.min(short / limit, BAR_SPAN - 1) / BAR_SPAN) }}
          />
        )}
      </span>
      <span className="lpw-bar-text">
        {limit} のうち {num(used)}
        {flag && <span className={short > 0 ? "lpw-bar-flag is-over" : "lpw-bar-flag is-full"}>{flag}</span>}
      </span>
    </div>
  );
}

/** The tick numbers give way where the plan's own count is written over them. */
function Axes({ scale, viewport, plan }: { scale: Scale; viewport: Viewport; plan: Vec2 }) {
  const xs = Array.from({ length: Math.floor(SPAN[0]) + 1 }, (_, index) => index);
  const ys = Array.from({ length: Math.floor(SPAN[1]) + 1 }, (_, index) => index);
  return (
    <g>
      {xs.slice(1).map((x) => (
        <line className="lpw-grid" key={`x${x}`} x1={scale.px(x)} x2={scale.px(x)} y1={scale.py(0)} y2={0} />
      ))}
      {ys.slice(1).map((y) => (
        <line className="lpw-grid" key={`y${y}`} x1={scale.px(0)} x2={viewport.width} y1={scale.py(y)} y2={scale.py(y)} />
      ))}
      <line className="lpw-axis" x1={scale.px(0)} x2={scale.px(0)} y1={scale.py(0)} y2={0} />
      <line className="lpw-axis" x1={scale.px(0)} x2={viewport.width} y1={scale.py(0)} y2={scale.py(0)} />
      {xs.filter((x) => Math.abs(scale.px(x) - scale.px(plan[0])) > COUNT_WIDTH(num(plan[0])) / 2 + 5).map((x) => (
        <text className="lpw-tick" key={`tx${x}`} textAnchor="middle" x={scale.px(x)} y={scale.py(0) + 17}>{x}</text>
      ))}
      {ys.slice(1).filter((y) => Math.abs(scale.py(y) - scale.py(plan[1])) > 15).map((y) => (
        <text className="lpw-tick" key={`ty${y}`} textAnchor="end" x={scale.px(0) - 8} y={scale.py(y) + 4.5}>{y}</text>
      ))}
      <text className="lpw-axis-name" textAnchor="end" x={viewport.width - 6} y={scale.py(0) + 37}>食パンの個数 →</text>
      <text className="lpw-axis-name" x={scale.px(0) + 7} y={15}>↑ クロワッサン</text>
    </g>
  );
}

/** Width of the box a count is written in on an axis. */
const COUNT_WIDTH = (text: string) => text.length * 7 + 9;

/**
 * Dashed lines from the plan to the axes, drawn while the reader is still learning to read a point;
 * later the revenue line and the corners need the room.
 */
function DropLines({ plan, scale }: { plan: Vec2; scale: Scale }) {
  const [x, y] = [scale.px(plan[0]), scale.py(plan[1])];
  return (
    <g aria-hidden="true">
      <line className="lpw-drop" x1={x} x2={x} y1={y} y2={scale.py(0)} />
      <line className="lpw-drop" x1={x} x2={scale.px(0)} y1={y} y2={y} />
    </g>
  );
}

/**
 * The plan's two counts, written on the axes. Drawn over the plan and clear of the axis line, so a
 * plan that sits on an axis (bread only) does not cover its own count.
 */
function PlanCounts({ plan, scale }: { plan: Vec2; scale: Scale }) {
  const [x, y] = [scale.px(plan[0]), scale.py(plan[1])];
  const [x0, y0] = [scale.px(0), scale.py(0)];
  const [breads, croissants] = [num(plan[0]), num(plan[1])];
  const [wide, tall] = [COUNT_WIDTH(breads), COUNT_WIDTH(croissants)];
  return (
    <g aria-hidden="true" pointerEvents="none">
      <rect className="lpw-read-box" height={18} rx={3} width={wide} x={x - wide / 2} y={y0 + 5} />
      <text className="lpw-read" textAnchor="middle" x={x} y={y0 + 18}>{breads}</text>
      <rect className="lpw-read-box" height={18} rx={3} width={tall} x={x0 - 6 - tall} y={y - 9} />
      <text className="lpw-read" textAnchor="middle" x={x0 - 6 - tall / 2} y={y + 4.5}>{croissants}</text>
    </g>
  );
}

function Diamond({ plan, scale, className }: { plan: Vec2; scale: Scale; className: string }) {
  const [x, y] = [scale.px(plan[0]), scale.py(plan[1])];
  return <rect className={className} height={15} transform={`rotate(45 ${x} ${y})`} width={15} x={x - 7.5} y={y - 7.5} />;
}

/** The line of every plan that sells for as much as `shown.plan`, across the whole plane. */
function LevelLine({
  shown, scale, viewport, className,
}: { shown: Chosen; scale: Scale; viewport: Viewport; className: string }) {
  const line = levelLine(shown.cost, objectiveValue(shown.cost, shown.plan), viewport.bounds);
  if (!line) return null;
  return (
    <line
      className={className}
      clipPath="url(#lpw-plane)"
      x1={scale.px(line[0][0])}
      x2={scale.px(line[1][0])}
      y1={scale.py(line[0][1])}
      y2={scale.py(line[1][1])}
    />
  );
}

/** The arrow's name, whole and in the two halves used where the whole does not fit beside the tip. */
const ARROW_NAME = ["売上が", "増える向き"];
const ARROW_NAME_WIDTH = [108, 68];

/**
 * From the plan, the direction in which revenue grows fastest: square to the equal-revenue line.
 * It is named while it is new; once the corners' revenues are on the plane the name gives way.
 */
function RevenueArrow({
  plan, cost, scale, viewport, named,
}: { plan: Vec2; cost: Vec2; scale: Scale; viewport: Viewport; named: boolean }) {
  const norm = Math.hypot(cost[0], cost[1]);
  const [ux, uy] = [cost[0] / norm, -cost[1] / norm];
  const [x, y] = [scale.px(plan[0]), scale.py(plan[1])];
  // About one loaf long, so on a phone it stays clear of the names along the top of the plane.
  const length = clamp(scale.px(1.1) - scale.px(0), 34, 46);
  const tip: Vec2 = [x + ux * length, y + uy * length];
  // The name sits past the tip on one line when there is room. On a narrow plane it goes on two
  // lines below the arrow's foot, clear of the stock names along the top and the right edge, and
  // failing that above the tip, kept inside the plot.
  const roomRight = viewport.width - 6 - (tip[0] + 8);
  const whole = roomRight >= ARROW_NAME_WIDTH[0];
  const lines = whole ? [ARROW_NAME.join("")] : ARROW_NAME;
  const below = !whole && viewport.width - 6 - (x + 12) >= ARROW_NAME_WIDTH[1];
  const name = whole
    ? { x: tip[0] + 8, y: Math.max(14, (y + tip[1]) / 2 + 4), textAnchor: "start" as const }
    : below
      ? { x: x + 12, y: y + 22, textAnchor: "start" as const }
      : {
          x: Math.min(viewport.width - 6, tip[0] + ARROW_NAME_WIDTH[1] / 2),
          y: Math.max(14, tip[1] - 10 - 16 * (lines.length - 1)),
          textAnchor: "end" as const,
        };
  return (
    <g aria-hidden="true">
      <line className="lpw-arrow" markerEnd="url(#lpw-arrow-head)" x1={x + ux * 14} x2={tip[0]} y1={y + uy * 14} y2={tip[1]} />
      {named && (
        <text className="ex-label lpw-arrow-name" textAnchor={name.textAnchor} y={name.y}>
          {lines.map((line, index) => <tspan dy={index === 0 ? 0 : 16} key={line} x={name.x}>{line}</tspan>)}
        </text>
      )}
    </g>
  );
}

const STOCK_NAME_WIDTH = 64;
/** The bread count at which a stock line passes the croissant count `y`. */
const breadsOnLine = (constraint: HalfPlane, y: number) => (constraint.b - constraint.a[1] * y) / constraint.a[0];

/** A stock's limit line, cut at the axes. */
function StockLine({ constraint, scale, viewport }: { constraint: HalfPlane; scale: Scale; viewport: Viewport }) {
  const line = levelLine(constraint.a, constraint.b, viewport.bounds);
  if (!line) return null;
  return (
    <line
      className="ex-constraint"
      clipPath="url(#lpw-plane)"
      x1={scale.px(line[0][0])}
      x2={scale.px(line[1][0])}
      y1={scale.py(line[0][1])}
      y2={scale.py(line[1][1])}
    />
  );
}

/** A stock line's name, at the end of the line where no step of the lesson puts the plan. */
function StockName({ constraint, scale, viewport }: { constraint: HalfPlane; scale: Scale; viewport: Viewport }) {
  const onLine = (x: number) => (constraint.b - constraint.a[0] * x) / constraint.a[1];
  const flour = constraint === ARTICLE_LP[0];
  // Flour: right of the steep line where it leaves the top. Butter: above the line's low end at the right edge.
  const label = flour
    ? { x: scale.px(breadsOnLine(constraint, scale.iy(MARGIN.top + 14))) + 10, y: MARGIN.top + 18, textAnchor: "start" as const }
    : {
        x: viewport.width - 6,
        y: scale.py(onLine(scale.ix(viewport.width - 6 - STOCK_NAME_WIDTH))) - 7,
        textAnchor: "end" as const,
      };
  return <text className="ex-label ex-label-strong" {...label}>{STOCKS[flour ? 0 : 1].name} {constraint.b}</text>;
}

/** A corner's revenue is written inside the range, toward its middle, clear of the lines that meet there. */
function cornerLabel(vertex: Vec2, scale: Scale) {
  const [dx, dy] = [CENTROID[0] - vertex[0], CENTROID[1] - vertex[1]];
  const length = Math.hypot(dx, dy);
  const [ux, uy] = [dx / length, dy / length];
  return {
    x: scale.px(vertex[0]) + ux * 34,
    y: scale.py(vertex[1]) - uy * 34 + (uy < 0 ? 12 : 0),
    textAnchor: ux < 0 ? ("end" as const) : ("start" as const),
  };
}
