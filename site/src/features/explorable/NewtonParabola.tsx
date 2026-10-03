import { useCallback, useMemo, useRef, useState, type KeyboardEvent } from "react";

import { Choice, PlayerBar, Slider } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import { fmt } from "./format";
import type { Bounds } from "./math/contours";
import {
  correctDigits,
  d2f,
  df,
  f,
  gradientRun,
  limitOf,
  model,
  newtonRun,
  type NewtonMethod,
  type NewtonStep,
} from "./math/newton1d";
import { EXPLORABLE_META } from "./meta";
import { numberSetting, stringSetting, type BeatSettings } from "./scene";
import { clamp, makeScale, polylinePath, useDomainDrag, useStageViewport, type Scale, type Viewport } from "./svg";
import { useSceneTour } from "./useSceneTour";
import { useReplayOnChange, useTimeline } from "./useTimeline";

const ID = "newton-parabola-jump";
const CURVE_BOUNDS: Bounds = { xMin: -2.4, xMax: 2.4, yMin: -0.8, yMax: 3.2 };
const X_RANGE: readonly [number, number] = [-2.3, 2.3];
const METHODS = ["newton", "safeguarded"] as const;
const DIGIT_MAX = 16;

interface Settings {
  x0: number;
  method: NewtonMethod;
}

const INITIAL: Settings = { x0: 2, method: "newton" };

function fromBeat(settings: BeatSettings, base: Settings): Settings {
  return {
    x0: numberSetting(settings, "x0", base.x0),
    method: stringSetting(settings, "method", METHODS, base.method),
  };
}

const LIMIT_NAMES: Record<number, string> = { [-1]: "谷 x=−1", 0: "山 x=0", 1: "谷 x=1" };

export default function NewtonParabola() {
  const [chosen, setChosen] = useState<Settings>(INITIAL);
  const tour = useSceneTour(
    ID,
    EXPLORABLE_META[ID].beats,
    useCallback((settings: BeatSettings) => setChosen((value) => fromBeat(settings, value)), []),
  );
  const shown = tour.beat ? fromBeat(tour.beat.settings, chosen) : chosen;
  const run = useMemo(() => newtonRun(shown.x0, shown.method), [shown.x0, shown.method]);
  const gradient = useMemo(() => gradientRun(shown.x0, 0.1, run.length - 1), [shown.x0, run.length]);
  const length = run.length - 1;
  const timeline = useTimeline(length, 1.2);
  useReplayOnChange(timeline, `${shown.x0}:${shown.method}`);
  const position = tour.beat
    ? Math.min(length, (tour.local / Math.max(tour.beat.durationS - 1.5, 1)) * length)
    : timeline.position;
  const step = Math.min(Math.floor(position + 1e-9), length);
  const xs = run.map((s) => s.x);
  const target = limitOf(xs);
  const setX0 = (x0: number) => setChosen((value) => ({ ...value, x0: clamp(Math.round(x0 * 20) / 20, X_RANGE[0], X_RANGE[1]) }));
  const last = run[length];
  const escaped = Math.abs(last.x) > CURVE_BOUNDS.xMax;
  const summary = `始点 x₀=${fmt(shown.x0)} から${shown.method === "newton" ? "Newton法" : "安全装置つきのNewton法"}で${length}回進み、${
    escaped ? `x=${fmt(last.x, 1)} にいます。` : `${LIMIT_NAMES[target]} に近づきました。`
  }`;

  return (
    <ExplorableFrame
      controls={
        <>
          <Slider
            display={fmt(shown.x0)}
            label="始点 x₀"
            max={X_RANGE[1]}
            min={X_RANGE[0]}
            onChange={setX0}
            step={0.05}
            value={shown.x0}
          />
          <Choice<NewtonMethod>
            legend="進み方"
            onChange={(method) => setChosen((value) => ({ ...value, method }))}
            options={[
              { value: "newton", label: "放物線の底へそのまま跳ぶ" },
              { value: "safeguarded", label: "曲がりを確かめ、一歩を縮める" },
            ]}
            value={shown.method}
          />
          <div className="ex-button-row">
            <button className="ex-action" onClick={() => setChosen(INITIAL)} type="button">始点を最初に戻す</button>
          </div>
        </>
      }
      id={ID}
      player={<PlayerBar positionText={`k = ${step} / ${length}`} stepLabel="反復 k" timeline={timeline} />}
      readout={<Readout run={run} step={step} target={target} />}
      stage={
        <div className="ex-twin">
          <CurvePanel fixed={tour.active} onMoveX0={setX0} run={run} step={step} x0={shown.x0} />
          <DigitsPanel gradient={gradient} newton={xs} step={step} target={target} />
        </div>
      }
      summary={summary}
      tour={tour}
    />
  );
}

interface CurvePanelProps {
  run: NewtonStep[];
  step: number;
  x0: number;
  fixed: boolean;
  onMoveX0(x: number): void;
}

function CurvePanel({ run, step, x0, fixed, onMoveX0 }: CurvePanelProps) {
  const { ref, viewport } = useStageViewport(CURVE_BOUNDS, 0.8);
  const scale = useMemo(() => makeScale(viewport), [viewport]);
  const svgRef = useRef<SVGSVGElement>(null);
  const drag = useDomainDrag({ svgRef, viewport, onDrag: (x) => onMoveX0(x) });
  const onKeyDown = (event: KeyboardEvent<SVGGElement>) => {
    const amount = event.shiftKey ? 0.5 : 0.05;
    const delta = event.key === "ArrowRight" ? amount : event.key === "ArrowLeft" ? -amount : 0;
    if (delta === 0) return;
    event.preventDefault();
    onMoveX0(x0 + delta);
  };
  const curve: Array<readonly [number, number]> = [];
  for (let i = 0; i <= 200; i += 1) {
    const x = CURVE_BOUNDS.xMin + ((CURVE_BOUNDS.xMax - CURVE_BOUNDS.xMin) * i) / 200;
    curve.push([x, f(x)]);
  }
  const here = run[step].x;
  const next = run[Math.min(step + 1, run.length - 1)];
  const hasNext = step < run.length - 1;
  const visible = (x: number) => x >= CURVE_BOUNDS.xMin && x <= CURVE_BOUNDS.xMax;
  // The fitted parabola, drawn across the plot and clipped to the visible band.
  const parabola: Array<readonly [number, number]> = [];
  if (visible(here)) {
    for (let i = 0; i <= 200; i += 1) {
      const x = CURVE_BOUNDS.xMin + ((CURVE_BOUNDS.xMax - CURVE_BOUNDS.xMin) * i) / 200;
      parabola.push([x, clamp(model(here, x), CURVE_BOUNDS.yMin - 1, CURVE_BOUNDS.yMax + 1)]);
    }
  }
  const vertex = d2f(here) !== 0 ? here - df(here) / d2f(here) : undefined;
  const handleProps = fixed
    ? { className: "ex-handle is-fixed" }
    : {
        "aria-label": `始点 x₀=${fmt(x0)}。左右にドラッグするか、左右の矢印キーで動かせます。`,
        "aria-orientation": "horizontal" as const,
        "aria-valuemax": X_RANGE[1],
        "aria-valuemin": X_RANGE[0],
        "aria-valuenow": x0,
        className: "ex-handle",
        onKeyDown,
        role: "slider",
        tabIndex: 0,
        ...drag,
      };
  return (
    <figure className="ex-panel">
      <figcaption className="ex-panel-title">関数と放物線 ↔ 始点を動かせます</figcaption>
      <div className="ex-canvas" ref={ref}>
        <svg className="ex-svg" ref={svgRef} viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
          <clipPath id="newton-plot"><rect height={viewport.height} width={viewport.width} /></clipPath>
          <rect className="ex-ground" height={viewport.height} width={viewport.width} />
          <CurveAxes scale={scale} viewport={viewport} />
          <path className="ex-fit-line" d={polylinePath(curve, scale)} fill="none" />
          <g clipPath="url(#newton-plot)">
            {parabola.length > 0 && <path className="newton-model" d={polylinePath(parabola, scale)} />}
          </g>
          {vertex !== undefined && visible(vertex) && hasNext && run[step + 1].t === 1 && !run[step + 1].fallback && (
            <g className="newton-vertex">
              <line x1={scale.px(vertex)} x2={scale.px(vertex)} y1={scale.py(model(here, vertex))} y2={scale.py(f(vertex))} />
              <circle cx={scale.px(vertex)} cy={scale.py(model(here, vertex))} r={5} />
            </g>
          )}
          {run.slice(0, step + 1).filter((s) => visible(s.x)).map((s, index) => (
            <circle className="ex-surface-dot" cx={scale.px(s.x)} cy={scale.py(f(s.x))} key={index} r={3.5} />
          ))}
          {hasNext && (visible(next.x)
            ? <line className="ex-next-step" markerEnd="url(#newton-arrow)" x1={scale.px(here)} x2={scale.px(next.x)} y1={scale.py(f(here))} y2={scale.py(f(next.x))} />
            : (
              <g className="newton-escape">
                <line markerEnd="url(#newton-arrow)" x1={scale.px(here)} x2={next.x > 0 ? viewport.width - 4 : 4} y1={scale.py(f(here))} y2={scale.py(f(here))} />
                <text textAnchor={next.x > 0 ? "end" : "start"} x={next.x > 0 ? viewport.width - 8 : 8} y={scale.py(f(here)) - 10}>x={fmt(next.x, 1)} へ</text>
              </g>
            ))}
          {visible(here)
            ? <circle className="ex-head" cx={scale.px(here)} cy={scale.py(f(here))} r={7} />
            : (
              <g className="newton-escape">
                <text textAnchor={here > 0 ? "end" : "start"} x={here > 0 ? viewport.width - 8 : 8} y={28}>
                  {here > 0 ? `いまは x=${fmt(here, 2)}（図の右の外）→` : `← いまは x=${fmt(here, 2)}（図の左の外）`}
                </text>
              </g>
            )}
          <g {...handleProps}>
            <circle className="ex-handle-hit" cx={scale.px(x0)} cy={scale.py(f(x0))} r={24} />
            <circle className="ex-handle-ring" cx={scale.px(x0)} cy={scale.py(f(x0))} r={11} />
          </g>
          <defs>
            <marker id="newton-arrow" markerHeight="8" markerWidth="8" orient="auto-start-reverse" refX="6" refY="4">
              <path className="ex-arrowhead" d="M0 0L8 4L0 8z" />
            </marker>
          </defs>
        </svg>
      </div>
    </figure>
  );
}

function CurveAxes({ scale, viewport }: { scale: Scale; viewport: Viewport }) {
  return (
    <g className="ex-axes">
      {[-2, -1, 0, 1, 2].map((x) => (
        <g key={`x${x}`}>
          <line x1={scale.px(x)} x2={scale.px(x)} y1={0} y2={viewport.height} />
          <text textAnchor="middle" x={scale.px(x)} y={viewport.height - 6}>{x}</text>
        </g>
      ))}
      {[0, 1, 2, 3].map((y) => (
        <g key={`y${y}`}>
          <line x1={0} x2={viewport.width} y1={scale.py(y)} y2={scale.py(y)} />
          <text x={6} y={scale.py(y) - 4}>{y}</text>
        </g>
      ))}
      <text className="ex-axis-name" textAnchor="end" x={viewport.width - 8} y={viewport.height - 22}>x</text>
      <text className="ex-axis-name" x={scale.px(0) + 8} y={16}>f(x)</text>
    </g>
  );
}

interface DigitsPanelProps {
  newton: readonly number[];
  gradient: readonly number[];
  step: number;
  target: number;
}

function DigitsPanel({ newton, gradient, step, target }: DigitsPanelProps) {
  const { ref, viewport } = useStageViewport({ xMin: 0, xMax: 1, yMin: 0, yMax: 1 }, 0.8);
  const left = 34;
  const bottom = viewport.height - 26;
  const top = 26;
  const count = Math.max(newton.length, 2);
  const slot = (viewport.width - left - 8) / count;
  const py = (digits: number) => bottom - ((bottom - top) * digits) / DIGIT_MAX;
  const gradientTarget = limitOf(gradient);
  return (
    <figure className="ex-panel">
      <figcaption className="ex-panel-title">正しい桁数</figcaption>
      <div className="ex-canvas" ref={ref}>
        <svg className="ex-svg" viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
          <rect className="ex-ground" height={viewport.height} width={viewport.width} />
          <g className="ex-axes">
            {[0, 4, 8, 12, 16].map((d) => (
              <g key={d}>
                <line x1={left} x2={viewport.width} y1={py(d)} y2={py(d)} />
                <text textAnchor="end" x={left - 4} y={py(d) + 5}>{d}</text>
              </g>
            ))}
            {newton.map((_, k) => (
              <text key={k} textAnchor="middle" x={left + slot * (k + 0.5)} y={viewport.height - 6}>{k}</text>
            ))}
            <text className="ex-axis-name" x={left + 4} y={16}>桁（16で倍精度の限界）</text>
          </g>
          {newton.slice(0, step + 1).map((x, k) => {
            const digits = Math.abs(x) > 50 ? 0 : correctDigits(x, target);
            const gd = correctDigits(gradient[k], gradientTarget);
            const width = Math.max(4, slot * 0.36);
            return (
              <g key={k}>
                <rect className="newton-bar-gd" height={bottom - py(gd)} width={width} x={left + slot * k + slot * 0.1} y={py(gd)} />
                <rect className={`newton-bar ${target === 0 ? "is-hill" : ""}`} height={bottom - py(digits)} width={width} x={left + slot * k + slot * 0.52} y={py(digits)} />
              </g>
            );
          })}
          <g className="newton-legend">
            <rect className="newton-bar" height={10} width={10} x={left + 8} y={top + 8} />
            <text x={left + 22} y={top + 18}>Newton法</text>
            <rect className="newton-bar-gd" height={10} width={10} x={left + 8} y={top + 26} />
            <text x={left + 22} y={top + 36}>勾配降下法 η=0.1</text>
          </g>
        </svg>
      </div>
    </figure>
  );
}

function Readout({ run, step, target }: { run: NewtonStep[]; step: number; target: number }) {
  const rows = run.slice(0, step + 1);
  const last = run[step];
  const next = run[step + 1];
  const escaped = Math.abs(last.x) > CURVE_BOUNDS.xMax;
  const leaps = next !== undefined && Math.abs(next.x) > CURVE_BOUNDS.xMax;
  const [tone, message] = next?.fallback
    ? ["ex-tone-swing", `f″=${fmt(d2f(last.x), 2)} は小さすぎるので、次の一歩は放物線の頂点ではなく下り坂の向き −f′ に進み、一歩を ${fmt(next.t, 2)} 倍に縮めます。`]
    : leaps
      ? ["ex-tone-bad", `f″=${fmt(d2f(last.x), 2)} とほとんど平らなので放物線の頂点がずっと遠くにあり、次の一歩で x=${fmt(next.x, 1)} へ跳びます。`]
      : escaped
        ? ["ex-tone-bad", `いまは図の外の x=${fmt(last.x, 1)} にいます。ここから放物線の頂点へ跳び直します。`]
        : target === 0
          ? ["ex-tone-bad", "f″ が負の点では放物線が下に開くので、その頂点は谷ではなく山です。Newton法は山 x=0 へ向かいます。"]
          : [next ? "ex-tone-swing" : "ex-tone-good", `${LIMIT_NAMES[target]} に向かっています。底の近くでは、反復ごとに正しい桁数がほぼ倍になります。`];
  return (
    <>
      <section aria-label="反復の記録">
        <table className="ex-table">
          <thead>
            <tr>
              <th scope="col">k</th><th scope="col">x</th><th scope="col">f′(x)</th><th scope="col">f″(x)</th>
              <th scope="col">{LIMIT_NAMES[target]}までの桁</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((s, k) => (
              <tr className={k === step ? "ex-row-best" : undefined} key={k}>
                <th scope="row">{k}</th>
                <td>{fmt(s.x, 6)}</td>
                <td>{fmt(df(s.x), 3)}</td>
                <td className={d2f(s.x) <= 0 ? "ex-tone-bad" : undefined}>{fmt(d2f(s.x), 3)}</td>
                <td>{Math.abs(s.x) > 50 ? "—" : fmt(correctDigits(s.x, target), 1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <p className={`ex-verdict ${tone}`}>{message}</p>
    </>
  );
}
