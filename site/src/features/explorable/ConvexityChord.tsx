import { useMemo, useRef, useState, type KeyboardEvent } from "react";

import { Choice, PlayerBar, Slider } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import { fmt } from "./format";
import type { Bounds } from "./math/contours";
import {
  CURVE_DOMAIN,
  CURVE_FUNCTIONS,
  chordReading,
  descendFrom,
  globalMinimum,
  slackTrace,
  SWEEP_STEPS,
  sweepReach,
  sweepTheta,
  violationIntervals,
  type CurveFunction,
} from "./math/convexity";
import { LiveMath, mi, mn, mo, paren, row, signed, tint } from "./mathml";
import { clamp, makeScale, polylinePath, useDomainDrag, useStageViewport, type Scale } from "./svg";
import { useReplayOnChange, useTimeline } from "./useTimeline";

const BOUNDS: Bounds = { xMin: -3, xMax: 3, yMin: -0.6, yMax: 4.7 };
const ASPECT = 0.58;
const TRACE_ASPECT = 0.3;
const SWEEP_STEPS_PER_SECOND = 4;

export default function ConvexityChord() {
  const [functionId, setFunctionId] = useState<CurveFunction["id"]>("quadratic");
  const fn = CURVE_FUNCTIONS.find((item) => item.id === functionId) ?? CURVE_FUNCTIONS[0];
  const [a, setA] = useState(fn.defaultA);
  const [b, setB] = useState(fn.defaultB);
  const [sliderTheta, setSliderTheta] = useState(0.5);
  const [sweeping, setSweeping] = useState(false);
  const [descending, setDescending] = useState(false);
  const svgRef = useRef<SVGSVGElement>(null);
  const { ref: stageRef, viewport } = useStageViewport(BOUNDS, ASPECT);
  const scale = useMemo(() => makeScale(viewport), [viewport]);
  const sweep = useTimeline(SWEEP_STEPS, SWEEP_STEPS_PER_SECOND);
  // While the sweep is on, theta follows the clock; otherwise it is the slider's value.
  const theta = sweeping ? sweepTheta(sweep.position) : sliderTheta;
  const reach = sweeping ? sweepReach(sweep.position) : 1;

  const switchFunction = (id: CurveFunction["id"]) => {
    const next = CURVE_FUNCTIONS.find((item) => item.id === id) ?? CURVE_FUNCTIONS[0];
    setFunctionId(id);
    setA(next.defaultA);
    setB(next.defaultB);
    setDescending(false);
    if (sweeping) sweep.restart();
  };
  const startSweep = () => {
    setDescending(false);
    setSweeping(true);
    sweep.restart();
  };
  const moveSlider = (value: number) => {
    setSweeping(false);
    setSliderTheta(value);
  };

  const graph = useMemo(() => {
    const points: Array<readonly [number, number]> = [];
    for (let index = 0; index <= 240; index += 1) {
      const x = CURVE_DOMAIN[0] + ((CURVE_DOMAIN[1] - CURVE_DOMAIN[0]) * index) / 240;
      points.push([x, fn.f(x)]);
    }
    return points;
  }, [fn]);
  const reading = chordReading(fn.f, a, b, theta);
  const violations = useMemo(() => violationIntervals(fn.f, a, b), [fn, a, b]);
  const violated = violations.length > 0;
  const downhill = useMemo(() => (descending ? descendFrom(fn, a) : [a]), [descending, fn, a]);
  const minimum = useMemo(() => globalMinimum(fn), [fn]);
  const timeline = useTimeline(downhill.length - 1, 8);

  // The gap between chord and graph for every theta: the curve the sweep draws.
  const trace = useMemo(() => slackTrace(fn.f, a, b), [fn, a, b]);
  const traceBounds = useMemo<Bounds>(() => {
    const slacks = trace.map((sample) => sample.slack);
    const low = Math.min(0, ...slacks);
    const high = Math.max(0, ...slacks);
    const pad = Math.max(0.15 * (high - low), 0.2);
    return { xMin: -0.12, xMax: 1.08, yMin: low - pad, yMax: high + pad };
  }, [trace]);
  const { ref: traceRef, viewport: traceViewport } = useStageViewport(traceBounds, TRACE_ASPECT, {
    below: 520,
    aspect: 0.42,
    bounds: traceBounds,
  });
  const traceScale = useMemo(() => makeScale(traceViewport), [traceViewport]);

  useReplayOnChange(timeline, `${descending}|${a}|${functionId}`);

  const dragA = useDomainDrag({
    svgRef,
    viewport,
    onDrag: (x) => { setA(clamp(x, CURVE_DOMAIN[0], CURVE_DOMAIN[1])); setDescending(false); },
  });
  const dragB = useDomainDrag({
    svgRef,
    viewport,
    onDrag: (x) => setB(clamp(x, CURVE_DOMAIN[0], CURVE_DOMAIN[1])),
  });
  const nudge = (set: (value: number) => void, value: number, resetDescent: boolean) => (
    (event: KeyboardEvent<SVGGElement>) => {
      const amount = event.shiftKey ? 0.5 : 0.1;
      const delta = event.key === "ArrowLeft" ? -amount : event.key === "ArrowRight" ? amount : 0;
      if (delta === 0) return;
      event.preventDefault();
      set(clamp(value + delta, CURVE_DOMAIN[0], CURVE_DOMAIN[1]));
      if (resetDescent) setDescending(false);
    }
  );

  const step = Math.min(timeline.step, downhill.length - 1);
  const fraction = timeline.position - step;
  const ballX = step < downhill.length - 1
    ? downhill[step] + (downhill[step + 1] - downhill[step]) * fraction
    : downhill[step];
  const trail = [...downhill.slice(0, step + 1), ...(fraction > 0 && step < downhill.length - 1 ? [ballX] : [])]
    .map((x) => [x, fn.f(x)] as const);
  const stopped = downhill[downhill.length - 1];
  const reachedGlobal = Math.abs(fn.f(stopped) - minimum.value) < 0.02;

  const chordPoints = (from: number, to: number): Array<readonly [number, number]> => {
    const lo = Math.min(from, to);
    const hi = Math.max(from, to);
    return [[lo, thetaChord(fn, a, b, lo)], [hi, thetaChord(fn, a, b, hi)]];
  };

  const verdictText = violated
    ? `点a・bの間で、線分がグラフより下に入る区間があります（θ が ${plainDecimal(violations[0][0])} から ${plainDecimal(violations[violations.length - 1][1])} のあたり）。定義の不等式が破れるので、この関数は凸ではありません。`
    : fn.convex
      ? "どの混合比θでも、線分はグラフの上か同じ高さにあります。この関数は凸なので、どの2点を選んでもこうなります。"
      : "この2点の間では違反は見つかりません。ただし、一組の点で破れなかったことは凸性の証明になりません。aとbを谷の両側へ動かしてください。";
  const descentText = descending
    ? reachedGlobal
      ? `aから下ると x=${fmt(stopped)} で止まり、これが全体の最小点です。`
      : `aから下ると x=${fmt(stopped)}（f=${fmt(fn.f(stopped))}）で止まりますが、全体の最小値は f=${fmt(minimum.value)}（x=${fmt(minimum.x)}）です。局所的に下れなくなっても、全体の最小とは限りません。`
    : "";
  const summary = `${fn.label}。a=${fmt(a)}、b=${fmt(b)}、混合比θ=${fmt(sliderTheta)}。${verdictText}${descentText}`;

  return (
    <ExplorableFrame
      controls={
        <>
          <Choice
            legend="関数"
            onChange={switchFunction}
            options={CURVE_FUNCTIONS.map((item) => ({ value: item.id, label: item.label }))}
            value={functionId}
          />
          <Slider
            display={fmt(theta)}
            hint="線分の上で、点aに近いほど θ が1に近づきます。"
            label="混合比 θ"
            max={1}
            min={0}
            onChange={moveSlider}
            step={0.01}
            value={theta}
          />
          <div className="ex-button-row cvx-actions">
            <button className="ex-action" onClick={startSweep} type="button">
              ▶ θを0から1へ動かして再生
            </button>
            <button
              className="ex-action"
              onClick={() => {
                setSweeping(false);
                sweep.pause();
                setDescending(true);
                if (descending) timeline.restart();
              }}
              type="button"
            >
              aから勾配降下で下ってみる
            </button>
          </div>
        </>
      }
      id="convexity-chord"
      player={sweeping
        ? (
            <PlayerBar
              positionText={`θ = ${fmt(theta)}（${sweep.position < SWEEP_STEPS / 2 ? "0から1へ" : "1から0へ"}）`}
              stepLabel="θの動き"
              timeline={sweep}
            />
          )
        : descending
          ? (
              <PlayerBar
                positionText={`${step} / ${downhill.length - 1} 回`}
                stepLabel="下る回数"
                timeline={timeline}
              />
            )
          : undefined}
      readout={
        <>
          <section aria-label="定義の不等式を数値で確かめる" className="ex-equation">
            <p className="ex-eyebrow">定義の不等式（θ = {fmt(theta)}）</p>
            <LiveMath
              block
              label="凸性の定義。θaと(1-θ)bを混ぜた入力での関数値は、関数値をθと(1-θ)で混ぜた値以下"
              markup={definitionMarkup()}
            />
            <LiveMath
              block
              label={`左辺 ${fmt(reading.atMix)}、右辺 ${fmt(reading.chord)}。${reading.slack < 0 ? "左辺が大きく、定義に反します" : "左辺は右辺以下です"}`}
              markup={numericMarkup(fn, a, b, theta, reading.atMix, reading.chord, reading.slack < 0)}
            />
          </section>
          {fn.id === "quadratic" && (
            <p className="ex-hint">
              この関数では、差は 0.35 × θ(1−θ) × (a−b)² = 0.35 × {fmt(theta * (1 - theta))} × {fmt((a - b) ** 2)} = {fmt(reading.slack)} です。θ(1−θ) は θ=0.5 で最大になるので、差の記録は山になります。
            </p>
          )}
          <p className={`ex-verdict ${violated ? "ex-tone-bad" : "ex-tone-good"}`}>{verdictText}</p>
          {descentText && <p className="ex-verdict ex-tone-slow">{descentText}</p>}
        </>
      }
      stage={
        <>
        <div className={sweeping && reading.slack < 0 ? "ex-canvas cvx-flash" : "ex-canvas"} ref={stageRef}>
        <svg className="ex-svg" ref={svgRef} viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
          <rect className="ex-ground" height={viewport.height} width={viewport.width} />
          <g className="ex-axes">
            <line x1={scale.px(0)} x2={scale.px(0)} y1={0} y2={viewport.height} />
            <line x1={0} x2={viewport.width} y1={scale.py(0)} y2={scale.py(0)} />
            {[-2, -1, 1, 2].map((x) => (
              <text key={x} textAnchor="middle" x={scale.px(x)} y={scale.py(0) + 18}>{x}</text>
            ))}
            <text textAnchor="end" x={viewport.width - 8} y={scale.py(0) - 6}>x</text>
            <text x={scale.px(0) + 6} y={16}>f(x)</text>
          </g>
          <path className="ex-curve" d={polylinePath(graph, scale)} />
          <path className="ex-chord" d={polylinePath(chordPoints(a, b), scale)} />
          {violations.map(([from, to]) => (
            <path
              className="ex-chord-violation"
              d={polylinePath(chordPoints(from * a + (1 - from) * b, to * a + (1 - to) * b), scale)}
              key={from}
            />
          ))}
          <line
            className={reading.slack < 0 ? "ex-gap ex-gap-bad" : "ex-gap"}
            x1={scale.px(reading.mix)}
            x2={scale.px(reading.mix)}
            y1={scale.py(reading.atMix)}
            y2={scale.py(reading.chord)}
          />
          <circle className="ex-on-graph" cx={scale.px(reading.mix)} cy={scale.py(reading.atMix)} r={7} />
          <circle
            className={reading.slack < 0 ? "ex-on-chord ex-on-chord-bad" : "ex-on-chord"}
            cx={scale.px(reading.mix)}
            cy={scale.py(reading.chord)}
            r={7}
          />
          {descending && (
            <g>
              <path className="ex-descent-trail" d={polylinePath(trail, scale)} />
              <circle className="ex-ball" cx={scale.px(ballX)} cy={scale.py(fn.f(ballX))} r={8} />
              <circle className="ex-minimum-mark" cx={scale.px(minimum.x)} cy={scale.py(minimum.value)} r={5} />
              <text className="ex-label" textAnchor="middle" x={scale.px(minimum.x)} y={scale.py(minimum.value) + 26}>
                全体の最小
              </text>
            </g>
          )}
          <Handle
            drag={dragA}
            label="a"
            onKeyDown={nudge(setA, a, true)}
            scale={scale}
            value={a}
            y={fn.f(a)}
          />
          <Handle
            drag={dragB}
            label="b"
            onKeyDown={nudge(setB, b, false)}
            scale={scale}
            value={b}
            y={fn.f(b)}
          />
        </svg>
        </div>
        <section aria-label="差の記録" className="ex-panel cvx-trace">
          <p className="ex-panel-title">差の記録（弦の高さ − 曲線の高さ）を θ ごとに描く</p>
          <div className="ex-canvas" ref={traceRef}>
            <TraceSvg
              reach={reach}
              scale={traceScale}
              slack={reading.slack}
              sweeping={sweeping}
              theta={theta}
              trace={trace}
              viewport={traceViewport}
            />
          </div>
        </section>
        </>
      }
      summary={summary}
    />
  );
}

/** A ratio in [0, 1] as a plain decimal such as 0.004, never in exponent form. */
export function plainDecimal(value: number): string {
  return value.toFixed(3).replace(/(\.\d*?)0+$/, "$1").replace(/\.$/, "");
}

interface TraceSvgProps {
  trace: ReturnType<typeof slackTrace>;
  viewport: ReturnType<typeof useStageViewport>["viewport"];
  scale: Scale;
  theta: number;
  slack: number;
  reach: number;
  sweeping: boolean;
}

/** The record of "chord minus graph" against theta; it is drawn as the sweep reaches each theta. */
function TraceSvg({ trace, viewport, scale, theta, slack, reach, sweeping }: TraceSvgProps) {
  const built = trace.filter((sample) => sample.theta <= reach + 1e-9);
  const pieces: Array<{ bad: boolean; points: Array<readonly [number, number]> }> = [];
  built.forEach((sample, index) => {
    if (index === 0) return;
    const previous = built[index - 1];
    const bad = (sample.slack + previous.slack) / 2 < -1e-9;
    const tail = pieces[pieces.length - 1];
    if (tail && tail.bad === bad) tail.points.push([sample.theta, sample.slack]);
    else pieces.push({ bad, points: [[previous.theta, previous.slack], [sample.theta, sample.slack]] });
  });
  const current = slack;
  const below = current < -1e-9;
  const zeroY = scale.py(0);
  return (
    <svg aria-hidden="true" className="ex-svg" viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
      <rect className="ex-ground" height={viewport.height} width={viewport.width} />
      <g className="ex-axes">
        <line x1={scale.px(0)} x2={scale.px(1)} y1={zeroY} y2={zeroY} />
        {[0, 0.5, 1].map((value) => (
          <text key={value} textAnchor="middle" x={scale.px(value)} y={viewport.height - 6}>{value === 0.5 ? "θ=0.5" : value}</text>
        ))}
        <text textAnchor="end" x={scale.px(0) - 8} y={zeroY + 5}>0</text>
      </g>
      <path className="cvx-ghost" d={polylinePath(trace.map((sample) => [sample.theta, sample.slack] as const), scale)} />
      {pieces.map((piece, index) => (
        <path
          className={piece.bad ? "cvx-trace-line cvx-trace-bad" : "cvx-trace-line"}
          d={polylinePath(piece.points, scale)}
          key={index}
        />
      ))}
      <line className={below ? "ex-gap ex-gap-bad" : "ex-gap"} x1={scale.px(theta)} x2={scale.px(theta)} y1={zeroY} y2={scale.py(current)} />
      {below && sweeping && (
        <circle className="cvx-pulse" cx={scale.px(theta)} cy={scale.py(current)} r={10} />
      )}
      <circle className={below ? "ex-on-chord ex-on-chord-bad" : "ex-on-chord"} cx={scale.px(theta)} cy={scale.py(current)} r={7} />
      {below && (
        <text className="cvx-warning" textAnchor="middle" x={clamp(scale.px(theta), 90, viewport.width - 90)} y={Math.max(20, zeroY - 14)}>
          0を下回った: 弦が曲線より下
        </text>
      )}
    </svg>
  );
}

function thetaChord(fn: CurveFunction, a: number, b: number, x: number): number {
  if (a === b) return fn.f(a);
  const theta = (x - b) / (a - b);
  return theta * fn.f(a) + (1 - theta) * fn.f(b);
}

function definitionMarkup(): string {
  const point = row(mi("θ"), mi("a"), mo("+"), paren(mn("1"), mo("−"), mi("θ")), mi("b"));
  const rhs = row(
    mi("θ"), mi("f"), paren(mi("a")), mo("+"), paren(mn("1"), mo("−"), mi("θ")), mi("f"), paren(mi("b")),
  );
  return row(mi("f"), paren(point), mo("≤"), rhs);
}

function numericMarkup(
  fn: CurveFunction,
  a: number,
  b: number,
  theta: number,
  atMix: number,
  chord: number,
  violated: boolean,
): string {
  const operand = (value: number, digits = 2) => (
    fmt(value, digits).startsWith("−") ? paren(signed(fmt(value, digits))) : mn(fmt(value, digits))
  );
  const mix = theta * a + (1 - theta) * b;
  const left = row(mi("f"), paren(signed(fmt(mix))), mo("="), signed(fmt(atMix)));
  const relation = tint(violated ? "red" : "teal", mo(violated ? ">" : "≤"));
  const right = row(
    operand(theta), mo("·"), operand(fn.f(a)), mo("+"), operand(1 - theta), mo("·"), operand(fn.f(b)),
    mo("="), signed(fmt(chord)),
  );
  return row(left, relation, right);
}

interface HandleProps {
  label: string;
  value: number;
  y: number;
  scale: Scale;
  drag: ReturnType<typeof useDomainDrag>;
  onKeyDown(event: KeyboardEvent<SVGGElement>): void;
}

function Handle({ label, value, y, scale, drag, onKeyDown }: HandleProps) {
  return (
    <g
      aria-label={`点${label}の位置`}
      aria-valuemax={CURVE_DOMAIN[1]}
      aria-valuemin={CURVE_DOMAIN[0]}
      aria-valuenow={Number(value.toFixed(2))}
      aria-valuetext={`x=${fmt(value)}`}
      className="ex-handle"
      onKeyDown={onKeyDown}
      role="slider"
      tabIndex={0}
      {...drag}
    >
      <circle className="ex-handle-hit" cx={scale.px(value)} cy={scale.py(y)} r={20} />
      <circle className="ex-handle-ring" cx={scale.px(value)} cy={scale.py(y)} r={10} />
      <text className="ex-label ex-label-strong" textAnchor="middle" x={scale.px(value)} y={scale.py(y) - 18}>{label}</text>
    </g>
  );
}
