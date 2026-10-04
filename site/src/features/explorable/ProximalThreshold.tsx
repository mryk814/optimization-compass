import { useId, useMemo, useState } from "react";

import { PlayerBar, Slider } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import { fmt } from "./format";
import { PROXIMAL_BUDGET, proximalMinimum, proximalObjective, proximalRun, softThreshold, type ProximalStep } from "./math/proximalGradient";
import { LiveMath, mi, mn, mo, paren, row, signed, sub } from "./mathml";
import { useStageViewport } from "./svg";
import { useReplayOnChange, useTimeline } from "./useTimeline";

const BOUNDS = { xMin: -3, xMax: 5, yMin: -3, yMax: 5 };

export default function ProximalThreshold() {
  const [lambda, setLambda] = useState(0.8);
  const [eta, setEta] = useState(0.25);
  const [x0, setX0] = useState(0);
  const run = useMemo(() => proximalRun(x0, eta, lambda), [x0, eta, lambda]);
  // Each iteration has two visible operations: gradient, then proximal shrinkage.
  const timeline = useTimeline(PROXIMAL_BUDGET * 2, 2);
  useReplayOnChange(timeline, `${x0}|${eta}|${lambda}`);
  const k = Math.min(Math.floor(timeline.position / 2), PROXIMAL_BUDGET - 1);
  const phase = timeline.atEnd ? 2 : timeline.position - k * 2;
  const step = run[k];
  const minimum = proximalMinimum(lambda);
  const last = run[run.length - 1].next;
  const state = phase < 1 ? "勾配で進む" : phase < 2 ? "0へ縮める" : "二つの操作を完了";
  const number = (value: number) => signed(fmt(value, 3));

  return <ExplorableFrame
    id="proximal-gradient-threshold"
    controls={<>
      <Slider label="正則化の強さ λ" display={fmt(lambda, 2)} min={0} max={4} step={0.1} value={lambda} onChange={setLambda} />
      <Slider label="歩幅 η" display={fmt(eta, 2)} min={0.1} max={1} step={0.05} value={eta} onChange={setEta} />
      <details>
        <summary>始点を変える</summary>
        <Slider label="始点 x₀" display={fmt(x0, 2)} min={-3} max={5} step={0.1} value={x0} onChange={setX0} />
      </details>
    </>}
    stage={<div className="ex-twin">
      <StepPanel step={step} phase={phase} />
      <ThresholdPanel step={step} />
    </div>}
    player={<PlayerBar timeline={timeline} stepLabel="操作" positionText={`一手 ${k + 1} / ${PROXIMAL_BUDGET} · ${state}`} />}
    readout={<>
      <section className="prox-equations" aria-label="いまの一手の計算">
        <p>① 勾配で進む</p>
        <div className="prox-substitution">
          <LiveMath label={`zは${fmt(step.x, 3)}引く${fmt(eta, 3)}かける${fmt(step.gradient, 3)}`} markup={row(mi("z"), mo("="), number(step.x), mo("−"), mn(fmt(eta, 2)), mo("×"), paren(number(step.gradient)))} />
          <LiveMath label={`中間点zは${fmt(step.z, 3)}`} markup={row(mo("="), number(step.z))} />
        </div>
        <p>② 閾値 τ = ηλ = {fmt(step.threshold, 3)} で0へ縮める</p>
        <LiveMath block label={`次の点はzをソフト閾値処理した${fmt(step.next, 3)}`} markup={row(sub(mi("x"), row(mi("k"), mo("+"), mn("1"))), mo("="), mi("soft"), paren(mi("z"), mo(","), mi("τ")), mo("="), number(step.next))} />
      </section>
      <p className="ex-verdict">{step.next === 0
        ? "zが−τからτまでの区間に入るので、次の点はちょうど0です。"
        : `zの絶対値からτを引き、符号を保ちます。次の点は${fmt(step.next, 3)}です。`}</p>
      <p className="ex-hint">この一手の目的値 {fmt(proximalObjective(step.x, lambda), 3)} → {fmt(proximalObjective(step.next, lambda), 3)}。近接勾配写像の大きさ |Gη(xₖ)| = {fmt(Math.abs(step.mapping), 3)}。</p>
      <p className="ex-hint">解析的な最小点 x* = {fmt(minimum, 3)}。図は12回の更新を表示します。</p>
    </>}
    summary={`正則化の強さ${fmt(lambda, 2)}、歩幅${fmt(eta, 2)}、始点${fmt(x0, 2)}。勾配で進み、閾値${fmt(eta * lambda, 3)}で0へ縮めます。12回後は${fmt(last, 3)}、解析的な最小点は${fmt(minimum, 3)}です。`}
  />;
}

function StepPanel({ step, phase }: { step: ProximalStep; phase: number }) {
  const { ref, viewport } = useStageViewport(BOUNDS, 0.62, { below: 450, bounds: BOUNDS, aspect: 0.78 });
  const arrowId = useId();
  const width = viewport.width, height = Math.max(220, viewport.height);
  const left = 22, right = width - 22;
  // Include zero, but magnify this step so the shrinkage is visible on a phone.
  const low = Math.min(0, step.x, step.z, step.next);
  const high = Math.max(0, step.x, step.z, step.next);
  const padding = Math.max(1, high - low) * 0.15;
  const xMin = Math.floor((low - padding) * 2) / 2;
  const xMax = Math.ceil((high + padding) * 2) / 2;
  const px = (x: number) => left + (x - xMin) / (xMax - xMin) * (right - left);
  const firstY = 57, secondY = height - 62;
  const first = step.x + (step.z - step.x) * Math.min(phase, 1);
  const second = step.z + (step.next - step.z) * Math.max(0, phase - 1);
  const ticks = (y: number) => [xMin, 0, xMax].map(x => <g key={x}>
    <line x1={px(x)} x2={px(x)} y1={y - 5} y2={y + 5} />
    <text x={px(x)} y={y + 24} textAnchor="middle">{fmt(x, 1)}</text>
  </g>);
  const arrow = (from: number, to: number, y: number) => <line className="ex-next-step" x1={px(from)} x2={px(to)} y1={y} y2={y} markerEnd={Math.abs(to - from) > 0.2 ? `url(#${arrowId})` : undefined} />;
  return <figure className="ex-panel">
    <figcaption className="ex-panel-title">一手を二つに分ける（拡大）</figcaption>
    <div className="ex-canvas" ref={ref}>
      <svg className="ex-svg" aria-label="同じ数直線上の勾配の一歩と近接の一歩" viewBox={`0 0 ${width} ${height}`}>
        <rect className="ex-ground" width={width} height={height} />
        <rect className="prox-zero-band" x={px(Math.max(xMin, -step.threshold))} y={secondY - 20} width={px(Math.min(xMax, step.threshold)) - px(Math.max(xMin, -step.threshold))} height={40} />
        <g className="ex-axes">
          <line x1={left} x2={right} y1={firstY} y2={firstY} />{ticks(firstY)}
          <line x1={left} x2={right} y1={secondY} y2={secondY} />{ticks(secondY)}
        </g>
        <text className="ex-label" x={left} y={24}>① xₖ → z：勾配で進む</text>
        <text className="ex-label" x={left} y={secondY - 38}>② z → xₖ₊₁：0へ縮める</text>
        {arrow(step.x, step.z, firstY)}{arrow(step.z, step.next, secondY)}
        <circle className="prox-start" cx={px(step.x)} cy={firstY} r={6} />
        <circle className="prox-intermediate" cx={px(step.z)} cy={firstY} r={8} />
        <circle className="prox-intermediate" cx={px(step.z)} cy={secondY} r={8} />
        <circle className="prox-target" cx={px(step.next)} cy={secondY} r={4} />
        <circle className="ex-head" cx={px(phase < 1 ? first : second)} cy={phase < 1 ? firstY : secondY} r={5} />
        <text className="ex-label" x={left} y={height - 7}>薄い帯の中のzは、0へ</text>
        <defs><marker id={arrowId} markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto-start-reverse"><path className="ex-arrowhead" d="M0 0L8 4L0 8z" /></marker></defs>
      </svg>
    </div>
  </figure>;
}

function ThresholdPanel({ step }: { step: ProximalStep }) {
  const { ref, viewport } = useStageViewport(BOUNDS, 0.62, { below: 450, bounds: BOUNDS, aspect: 0.78 });
  const width = viewport.width, height = Math.max(220, viewport.height);
  const left = 36, right = width - 18, top = 26, bottom = height - 36;
  const px = (x: number) => left + (x + 3) / 8 * (right - left);
  const py = (x: number) => bottom - (x + 3) / 8 * (bottom - top);
  const xs = [-3, Math.max(-3, -step.threshold), step.threshold, 5];
  const path = xs.map((x, i) => `${i ? "L" : "M"}${px(x)} ${py(softThreshold(x, step.threshold))}`).join("");
  return <figure className="ex-panel">
    <figcaption className="ex-panel-title">どのzが0になるか</figcaption>
    <div className="ex-canvas" ref={ref}>
      <svg className="ex-svg" aria-label="ソフト閾値処理の入力zと出力の関係" viewBox={`0 0 ${width} ${height}`}>
        <rect className="ex-ground" width={width} height={height} />
        <rect className="prox-zero-band" x={px(Math.max(-3, -step.threshold))} y={top} width={px(step.threshold) - px(Math.max(-3, -step.threshold))} height={bottom - top} />
        <g className="ex-axes">
          <line x1={left} x2={right} y1={py(0)} y2={py(0)} />
          <line x1={px(0)} x2={px(0)} y1={top} y2={bottom} />
          {[-3, 0, 3, 5].map(x => <text x={px(x)} y={bottom + 20} textAnchor="middle" key={x}>{x}</text>)}
          {[-3, 0, 3, 5].map(y => <text x={left - 6} y={py(y) + 4} textAnchor="end" key={y}>{y}</text>)}
        </g>
        <text className="ex-axis-name" x={left + 5} y={17}>出力 xₖ₊₁</text>
        <text className="ex-axis-name" x={right} y={height - 5} textAnchor="end">入力 z</text>
        <path className="ex-curve" d={path} />
        <line className="prox-guide" x1={px(step.z)} x2={px(step.z)} y1={py(0)} y2={py(step.next)} />
        <circle className="ex-head" cx={px(step.z)} cy={py(step.next)} r={6} />
      </svg>
    </div>
  </figure>;
}
