import { useMemo, useRef, useState } from "react";

import { Choice, PlayerBar, Slider } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import { fmt, fmtPair } from "./format";
import {
  ARTICLE_QUADRATIC, COORDINATE_BUDGET, COORDINATE_TOLERANCE,
  coordinateEllipse, coordinateGeometry, coordinatePoint, coordinateUpdate,
  rotatedQuadratic, runCoordinateDescent,
  type Coordinate, type CoordinatePoint, type CoordinateQuadratic,
} from "./math/coordinateDescent";
import { frac, LiveMath, mi, mn, mo, row, signed, sub } from "./mathml";
import { makeScale, polylinePath, useStageViewport, type Viewport } from "./svg";
import { useReplayOnChange, useTimeline } from "./useTimeline";

type Preset = "aligned" | "article" | "slanted" | "custom";
type DetailView = "slice" | "loss";
const PRESETS: Record<Exclude<Preset, "custom">, CoordinateQuadratic> = {
  aligned: { a: 1, b: 0, d: 20 },
  article: ARTICLE_QUADRATIC,
  slanted: rotatedQuadratic(1, 100, 45),
};
const DEFAULT_START: readonly [number, number] = [4, 3];
const LEVELS = [0.5, 2, 8, 32, 128, 512];
const PLACEHOLDER = { xMin: -12, xMax: 6, yMin: -7, yMax: 5 };

export default function CoordinateDescentWalk() {
  const [q, setQ] = useState<CoordinateQuadratic>(ARTICLE_QUADRATIC);
  const [preset, setPreset] = useState<Preset>("article");
  const [start, setStart] = useState<readonly [number, number]>(DEFAULT_START);
  const [view, setView] = useState<DetailView>("slice");
  const [resetCount, setResetCount] = useState(0);
  const resetRequested = useRef(false);
  const geometry = coordinateGeometry(q);
  const run = useMemo(() => runCoordinateDescent(q, start), [q, start]);
  const timeline = useTimeline(run.points.length - 1, 3);
  useReplayOnChange({ ...timeline, restart: () => {
    if (resetRequested.current) {
      resetRequested.current = false;
      timeline.finish();
    } else timeline.restart();
  } }, [q.a, q.b, q.d, ...start, resetCount].join("|"));
  const step = Math.min(timeline.step, run.points.length - 1);
  const axis: Coordinate = step % 2 === 0 ? "x" : "y";
  const p = run.points[step];
  const target = coordinateUpdate(q, p, axis);
  const fraction = timeline.atEnd ? 0 : timeline.position - step;
  // The dot, slice, equation and diagnostics all use this same interpolated point.
  const current = coordinatePoint(q, p.x + (target.x - p.x) * fraction, p.y + (target.y - p.y) * fraction);
  const next = coordinateUpdate(q, current, axis);
  const choose = (value: Preset) => {
    if (value === "custom") return;
    setPreset(value);
    setQ(PRESETS[value]);
  };
  const adjust = (angle: number, kappa: number) => {
    setPreset("custom");
    setQ(rotatedQuadratic(geometry.gentle, kappa, angle));
  };
  const reset = () => {
    resetRequested.current = true;
    setResetCount(count => count + 1);
    setQ(ARTICLE_QUADRATIC);
    setPreset("article");
    setStart(DEFAULT_START);
    setView("slice");
  };
  const last = run.points[run.points.length - 1];
  const updates = run.points.length - 1;
  const outcome = updates === 0
    ? "初期点が最小点です。更新せずに停止します。"
    : run.outcome === "converged"
      ? `${updates}回の更新（${updates / 2}掃引）で、全体の勾配ノルムが10⁻⁶を下回りました。`
      : `${COORDINATE_BUDGET}回の更新（${COORDINATE_BUDGET / 2}掃引）で打ち切り。全体の勾配ノルムは${magnitude(last.gradNorm)}で、まだ収束していません。`;
  const summary = `初期点${fmtPair(...start)}、谷の向き${fmt(geometry.angle, 1)}度、曲率比${fmt(geometry.kappa, 1)}。x、yの順に厳密に最小化します。${outcome}`;
  const numericGradient = axis === "x" ? current.gx : current.gy;
  const numericCurvature = 2 * (axis === "x" ? q.a : q.d);
  const equation = !timeline.atEnd && <section className="ex-equation" aria-label="次の一手">
    <p className="ex-eyebrow">次は{axis}だけ動かす（{axis === "x" ? "y" : "x"}は固定）</p>
    <LiveMath block label={`${axis}の更新式。現在値から偏微分をその方向の曲率で割った分を引きます。`} markup={row(mi(axis), mo("←"), mi(axis), mo("−"), frac(row(sub(mo("∂"), mi(axis)), mi("f")), sub(mi("H"), mi(axis + axis))))} />
    <div className="cd-substitution">
      <LiveMath label={`現在の${axis}は${fmt(current[axis], 3)}`} markup={signed(fmt(current[axis], 3))} />
      <LiveMath label={`偏微分${fmt(numericGradient, 3)}を曲率${fmt(numericCurvature, 3)}で割った分を引く`} markup={row(mo("−"), frac(signed(fmt(numericGradient, 3)), mn(fmt(numericCurvature, 3))))} />
      <LiveMath label={`次の${axis}は${fmt(next[axis], 3)}`} markup={row(mo("="), signed(fmt(next[axis], 3)))} />
    </div>
  </section>;

  return (
    <ExplorableFrame
      id="coordinate-descent-walk"
      controls={<>
        <div className="cd-presets">
          <Choice<Preset> legend="谷を選ぶ" value={preset} onChange={choose} options={[
            { value: "aligned", label: "軸に沿う" },
            { value: "article", label: "本文の谷" },
            { value: "slanted", label: "細く斜め" },
            ...(preset === "custom" ? [{ value: "custom" as const, label: "調整した谷" }] : []),
          ]} />
          <button className="ex-action" type="button" aria-label="谷と初期点を戻す" onClick={reset}>↺ リセット</button>
        </div>
        <details className="cd-adjustments">
          <summary>谷の向き・細長さを変える</summary>
          <div>
            <Slider label="谷の向き θ" display={`${fmt(geometry.angle, 1)}°`} min={-90} max={90} step={0.1} value={geometry.angle} onChange={angle => adjust(angle, geometry.kappa)} />
            <Slider label="谷の細長さ κ（曲率比）" display={fmt(geometry.kappa, 1)} min={1} max={100} step={1} value={geometry.kappa} onChange={kappa => adjust(geometry.angle, kappa)} />
          </div>
        </details>
        <details className="cd-start">
          <summary>初期点 {fmtPair(...start)}</summary>
          <Choice legend="開始する場所" value={start === DEFAULT_START ? "example" : "minimum"} onChange={value => setStart(value === "example" ? DEFAULT_START : [1, -2])} options={[
            { value: "example", label: "本文の初期点 (4, 3)" },
            { value: "minimum", label: "最小点 (1, −2)" },
          ]} />
        </details>
      </>}
      stage={<div className="cd-panels">
        <div className="cd-primary">
          <WalkPlot q={q} points={run.points} current={current} next={next} step={step} done={timeline.atEnd} />
          <PlayerBar timeline={{ ...timeline, restart: () => timeline.seek(0) }} stepLabel="座標更新" positionText={`${step} / ${updates}回`} />
          <div className="cd-diagnostics" aria-label="現在点と全体の勾配">
            <p>現在点 <strong>{fmtPair(current.x, current.y)}</strong> · 目的値 <strong>{magnitude(current.f)}</strong></p>
            <p>偏微分 x: <strong>{magnitude(current.gx)}</strong> · y: <strong>{magnitude(current.gy)}</strong></p>
            <p>全体の勾配ノルム <strong>{magnitude(current.gradNorm)}</strong></p>
          </div>
          {equation}
        </div>
        <section className="cd-detail" aria-label="一手を確かめる補助図">
          <Choice<DetailView> legend="確かめる図" value={view} onChange={setView} options={[
            { value: "slice", label: "一手の断面" },
            { value: "loss", label: "目的値の推移" },
          ]} />
          <DetailPlot q={q} points={run.points} current={current} next={next} axis={axis} position={timeline.position} view={view} />
          <p className="ex-hint">{view === "slice"
            ? `${axis === "x" ? "y" : "x"}を固定した放物線。橙は現在点、青緑はこの方向だけの最小です。`
            : "目的値は対数目盛。10⁻¹²以下は下端に表示します。横軸は座標更新の回数です。"}</p>
        </section>
      </div>}
      readout={<>
        <p className={`ex-verdict ${timeline.atEnd && run.outcome === "converged" ? "ex-tone-good" : "ex-tone-slow"}`}>
          {timeline.atEnd ? outcome : step === 0
            ? "x、yの順に一方向ずつ最小化します。「1つ進む」で最初の一手を確かめられます。"
            : `完了した更新は${step}回（${Math.floor(step / 2)}掃引）。一方向の偏微分が0でも、全体の勾配が残っていれば続けます。`}
        </p>
        <p className="ex-hint">座標の結びつき ρ = {fmt(geometry.rho, 3)}。一掃引後のyのずれの倍率は ρ² = {fmt(geometry.sweepFactor, 3)}。0なら1掃引、1に近いほど少しずつ進みます。</p>
      </>}
      summary={summary}
    />
  );
}

function magnitude(value: number): string {
  if (value === 0) return "0";
  return Math.abs(value) < 0.001 ? value.toExponential(2) : fmt(value, 3);
}

/** Equal units on both axes, with the entire run in view; no steps disappear offscreen. */
function fittedViewport(raw: Viewport, points: CoordinatePoint[]): Viewport {
  const xs = [1 - 2, 1 + 2, ...points.map(p => p.x)];
  const ys = [-2 - 2, -2 + 2, ...points.map(p => p.y)];
  const xmin = Math.min(...xs), xmax = Math.max(...xs);
  const ymin = Math.min(...ys), ymax = Math.max(...ys);
  const unit = Math.max((xmax - xmin) / (raw.width - 90), (ymax - ymin) / (raw.height - 80));
  const cx = (xmin + xmax) / 2, cy = (ymin + ymax) / 2;
  return { ...raw, bounds: { xMin: cx - raw.width * unit / 2, xMax: cx + raw.width * unit / 2, yMin: cy - raw.height * unit / 2, yMax: cy + raw.height * unit / 2 } };
}

function WalkPlot({ q, points, current, next, step, done }: {
  q: CoordinateQuadratic; points: CoordinatePoint[]; current: CoordinatePoint; next: CoordinatePoint; step: number; done: boolean;
}) {
  const { ref, viewport: raw } = useStageViewport(PLACEHOLDER, 0.7, { below: 450, bounds: PLACEHOLDER, aspect: 1 });
  const viewport = useMemo(() => fittedViewport(raw, points), [raw, points]);
  const scale = useMemo(() => makeScale(viewport), [viewport]);
  const contours = useMemo(() => LEVELS.map(level => polylinePath(coordinateEllipse(q, level), scale)), [q, scale]);
  const travelled = [...points.slice(0, step + 1), current];
  const tick = (low: number, high: number) => [0.2, 0.5, 0.8].map(t => Math.round((low + (high - low) * t) * 10) / 10);
  return <section className="ex-canvas cd-walk" ref={ref} aria-label="等高線と座標更新の軌跡">
    <p className="ex-panel-title">一方向ずつ、谷を進む</p>
    <svg className="ex-svg" viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
      <rect className="ex-ground" width={viewport.width} height={viewport.height} />
      <g className="ex-axes">
        {tick(viewport.bounds.xMin, viewport.bounds.xMax).map(x => <g key={x}><line x1={scale.px(x)} x2={scale.px(x)} y1={0} y2={viewport.height} /><text x={scale.px(x)} y={viewport.height - 8} textAnchor="middle">{x}</text></g>)}
        {tick(viewport.bounds.yMin, viewport.bounds.yMax).map(y => <g key={y}><line x1={0} x2={viewport.width} y1={scale.py(y)} y2={scale.py(y)} /><text x={6} y={scale.py(y) - 5}>{y}</text></g>)}
      </g>
      {contours.map((d, i) => <path className="ex-contour" d={d} key={i} />)}
      <path className="ex-ghost" d={polylinePath(points.map(p => [p.x, p.y]), scale)} />
      <path className="ex-trail" d={polylinePath(travelled.map(p => [p.x, p.y]), scale)} />
      {!done && <line className="ex-next-step" x1={scale.px(current.x)} x2={scale.px(next.x)} y1={scale.py(current.y)} y2={scale.py(next.y)} />}
      <g className="ex-minimum"><circle cx={scale.px(1)} cy={scale.py(-2)} r={10} /><text x={scale.px(1)} y={scale.py(-2) + 23} textAnchor="middle">最小点</text></g>
      <circle className="ex-head" cx={scale.px(current.x)} cy={scale.py(current.y)} r={7} />
      <circle className="ex-handle-ring" cx={scale.px(points[0].x)} cy={scale.py(points[0].y)} r={5} />
      <text className="ex-label" x={scale.px(points[0].x)} y={scale.py(points[0].y) - 13} textAnchor="middle">初期点</text>
      <text className="ex-axis-name" x={viewport.width - 10} y={viewport.height - 8}>x</text>
      <text className="ex-axis-name" x={8} y={18}>y</text>
    </svg>
  </section>;
}

function DetailPlot({ q, points, current, next, axis, position, view }: {
  q: CoordinateQuadratic; points: CoordinatePoint[]; current: CoordinatePoint; next: CoordinatePoint; axis: Coordinate; position: number; view: DetailView;
}) {
  const { ref, viewport } = useStageViewport(PLACEHOLDER, 0.7);
  const width = viewport.width, height = Math.max(180, viewport.height);
  const left = 44, right = width - 18, top = 24, bottom = height - 38;
  const loss = view === "loss";
  const radius = Math.max(1, Math.abs(current[axis] - next[axis]) * 1.4);
  const lo = loss ? 0 : next[axis] - radius;
  const hi = loss ? Math.max(2, points.length - 1) : next[axis] + radius;
  const high = loss ? Math.max(0, Math.ceil(Math.log10(Math.max(points[0].f, 1e-12)))) : coordinatePoint(q, axis === "x" ? hi : current.x, axis === "y" ? hi : current.y).f;
  const low = loss ? -12 : next.f;
  const range = Math.max(high - low, 1e-12);
  const px = (x: number) => left + (x - lo) / (hi - lo) * (right - left);
  const py = (y: number) => bottom - (y - low) / range * (bottom - top);
  const log = (f: number) => Math.log10(Math.max(f, 1e-12));
  const lossSamples = useMemo(() => points.flatMap((p, k) => {
    const nextPoint = points[k + 1];
    if (!nextPoint) return [[k, log(p.f)] as const];
    return Array.from({ length: 16 }, (_, i) => {
      const t = i / 16;
      return [k + t, log(nextPoint.f + (p.f - nextPoint.f) * (1 - t) ** 2)] as const;
    });
  }), [points]);
  const samples = loss ? lossSamples : Array.from({ length: 81 }, (_, i) => {
    const x = lo + (hi - lo) * i / 80;
    return [x, coordinatePoint(q, axis === "x" ? x : current.x, axis === "y" ? x : current.y).f] as const;
  });
  const curve = samples.map(([x, y], i) => `${i ? "L" : "M"}${px(x)} ${py(y)}`).join("");
  return <div className="ex-canvas" ref={ref}>
    <svg className="ex-svg cd-support" aria-label={loss ? "目的値の推移" : `${axis}だけを動かした断面`} viewBox={`0 0 ${width} ${height}`}>
      <rect className="ex-ground" width={width} height={height} />
      <g className="ex-axes">
        <line x1={left} x2={right} y1={bottom} y2={bottom} />
        <line x1={left} x2={left} y1={top} y2={bottom} />
        {[lo, (lo + hi) / 2, hi].map(x => <text key={x} textAnchor="middle" x={px(x)} y={bottom + 20}>{fmt(loss ? x : Math.round(x * 10) / 10, loss ? 0 : 1)}</text>)}
        <text x={6} y={top + 8}>{loss ? `10^${high}` : fmt(high, 1)}</text>
        <text x={6} y={bottom - 5}>{loss ? "10⁻¹²" : fmt(low, 1)}</text>
      </g>
      <text className="ex-axis-name" x={left + 5} y={17}>目的値 f{loss ? "（対数）" : ""}</text>
      <text className="ex-axis-name" textAnchor="end" x={right} y={height - 4}>{loss ? "更新回数" : axis}</text>
      <path className={loss ? "ex-loss" : "ex-curve"} d={curve} />
      {!loss && <g className="ex-minimum"><circle cx={px(next[axis])} cy={py(next.f)} r={9} /></g>}
      <circle className="ex-head" cx={px(loss ? position : current[axis])} cy={py(loss ? log(current.f) : current.f)} r={6} />
    </svg>
  </div>;
}
