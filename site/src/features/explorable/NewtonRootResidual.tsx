import { useId, useMemo, useState } from "react";

import { Choice, PlayerBar, Slider } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import { fmt } from "./format";
import { LiveMath, mi, mn, mo, row, signed, sub } from "./mathml";
import {
  bisectionSteps, bracketWindow, blendWindow, digits, dF, fStable, newtonSteps, newtonWindow, ROOT,
  smooth, WIDE_WINDOW, type BisectionStep, type NewtonStep, type Window,
} from "./math/rootFinding";
import { useStageViewport } from "./svg";
import { useReplayOnChange, useTimeline } from "./useTimeline";

type Method = "newton" | "bisection";
type Zoom = "auto" | "wide";

const NEWTON_STEPS = 3;
const BISECTION_STEPS = 8;
const SUBSCRIPT = "₀₁₂₃₄₅₆₇₈₉";
const sub10 = (n: number) => [...String(n)].map((d) => SUBSCRIPT[Number(d)]).join("");
const clamp01 = (u: number) => Math.min(1, Math.max(0, u));
const BOUNDS = { xMin: 0, xMax: 1, yMin: 0, yMax: 1 };

/** 0.19 -> "0.190", 0.006267 -> "6.27e-3", -0.25 -> "−0.250". */
function sci(value: number): string {
  const magnitude = Math.abs(value);
  if (magnitude === 0) return "0";
  const text = magnitude >= 0.1 ? magnitude.toFixed(3) : magnitude.toExponential(2).replace("e+", "e");
  return `${value < 0 ? "−" : ""}${text}`;
}

interface Frame {
  window: Window;
  /** Whole-step index the figure is working on and the 0..1 progress inside it. */
  k: number;
  f: number;
  tangent: number;
  slide: number;
  drop: number;
}

function newtonFrame(steps: readonly NewtonStep[], windows: readonly Window[], position: number): Frame {
  const n = steps.length;
  const k = Math.min(Math.floor(position + 1e-9), n - 1);
  const f = Math.min(1, position - k);
  const zoomIn = k + 1 < n ? smooth(clamp01((f - 0.9) / 0.1)) : 0;
  return {
    k, f,
    tangent: smooth(clamp01(f / 0.3)),
    slide: smooth(clamp01((f - 0.3) / 0.35)),
    drop: smooth(clamp01((f - 0.7) / 0.2)),
    window: blendWindow(windows[k], windows[k + 1], zoomIn),
  };
}

function bisectionFrame(steps: readonly BisectionStep[], windows: readonly Window[], position: number): Frame {
  const n = steps.length;
  const k = Math.min(Math.floor(position + 1e-9), n - 1);
  const f = Math.min(1, position - k);
  const zoomIn = k + 1 < n ? smooth(clamp01((f - 0.85) / 0.15)) : 0;
  return {
    k, f,
    tangent: 0,
    slide: smooth(clamp01((f - 0.45) / 0.4)),
    drop: smooth(clamp01(f / 0.4)),
    window: blendWindow(windows[k], windows[k + 1], zoomIn),
  };
}

export default function NewtonRootResidual() {
  const [method, setMethod] = useState<Method>("newton");
  const [zoom, setZoom] = useState<Zoom>("auto");
  const [t0, setT0] = useState(0.7);
  const count = method === "newton" ? NEWTON_STEPS : BISECTION_STEPS;
  const timeline = useTimeline(count, 0.7);
  useReplayOnChange(timeline, `${method}|${zoom}|${t0}`);

  const newton = useMemo(() => newtonSteps(t0, NEWTON_STEPS + 1), [t0]);
  const bisection = useMemo(() => bisectionSteps(0, 1, BISECTION_STEPS), []);
  const windows = useMemo<Window[]>(() => {
    if (zoom === "wide") return Array.from({ length: count + 1 }, () => WIDE_WINDOW);
    if (method === "newton") return newton.map(newtonWindow);
    const list = bisection.map((s) => bracketWindow(s.lo, s.hi));
    const last = bisection[bisection.length - 1];
    list.push(bracketWindow(last.nextLo, last.nextHi));
    return list;
  }, [zoom, method, count, newton, bisection]);

  const shown = method === "newton" ? newton.slice(0, NEWTON_STEPS) : [];
  const frame = method === "newton"
    ? newtonFrame(shown, windows, timeline.position)
    : bisectionFrame(bisection, windows, timeline.position);
  const finished = timeline.atEnd;

  return <ExplorableFrame
    id="newton-root-residual"
    controls={<>
      <Choice<Method> legend="方法" value={method} onChange={setMethod} options={[
        { value: "newton", label: "Newton法（接線）" },
        { value: "bisection", label: "二分法（区間を半分）" },
      ]} />
      <Choice<Zoom> legend="拡大" value={zoom} onChange={setZoom} options={[
        { value: "auto", label: "自動で拡大" },
        { value: "wide", label: "拡大しない" },
      ]} />
      {method === "newton" && <Slider label="始点 t₀" display={fmt(t0, 2)} min={0.2} max={1.2} step={0.05} value={t0} onChange={setT0}
        hint="記事の始点は 0.7 です。" />}
    </>}
    stage={<>
      <CurvePanel method={method} frame={frame} newton={shown} bisection={bisection} wide={zoom === "wide"} />
      <DigitsPanel method={method} frame={frame} newton={newton} bisection={bisection} />
    </>}
    player={<PlayerBar timeline={timeline} stepLabel="手" positionText={`${Math.min(count, timeline.step)} / ${count} 手`} />}
    readout={method === "newton"
      ? <NewtonReadout steps={newton} frame={frame} finished={finished} />
      : <BisectionReadout steps={bisection} frame={frame} finished={finished} />}
    summary={method === "newton"
      ? `Newton法を始点${fmt(t0, 2)}から3手進めます。残差は${sci(newton[0].residual)}、${sci(newton[1].residual)}、${sci(newton[2].residual)}、${sci(newton[3].residual)}と縮み、根${fmt(ROOT, 6)}に着きます。`
      : `二分法を区間0から1で8回進めます。区間は1回ごとに半分になり、8回後の幅は${fmt(1 / 256, 4)}、中点の残差は${sci(bisection[7].midResidual)}です。`}
  />;
}

interface CurvePanelProps {
  method: Method;
  frame: Frame;
  newton: readonly NewtonStep[];
  bisection: readonly BisectionStep[];
  wide: boolean;
}

function CurvePanel({ method, frame, newton, bisection, wide }: CurvePanelProps) {
  const { ref, viewport } = useStageViewport(BOUNDS, 0.5);
  const clipId = useId();
  const width = viewport.width, height = 300;
  const left = 58, right = width - 14, top = 18, bottom = height - 40;
  const w = frame.window;
  const px = (t: number) => left + ((t - (w.center - w.half)) / (2 * w.half)) * (right - left);
  const mid = (top + bottom) / 2;
  const py = (y: number) => mid - (y / w.yHalf) * ((bottom - top) / 2);
  const samples = 90;
  const curve = Array.from({ length: samples + 1 }, (_, i) => {
    const t = w.center - w.half + (2 * w.half * i) / samples;
    return `${i ? "L" : "M"}${px(t).toFixed(1)} ${py(fStable(t)).toFixed(1)}`;
  }).join("");
  const offset = method === "newton" && !wide;
  const tickLabel = (t: number) => {
    if (!offset) return fmt(t, wide ? 2 : 4);
    const d = t - ROOT;
    if (Math.abs(d) < w.half * 1e-6) return "根 t*";
    return `t*${d < 0 ? "−" : "+"}${Math.abs(d) >= 0.01 ? Math.abs(d).toFixed(3) : Math.abs(d).toExponential(1)}`;
  };
  const ticks = [w.center - w.half * 0.7, w.center, w.center + w.half * 0.7];
  const scale = Math.round(WIDE_WINDOW.half / w.half);

  let tangentLine: React.ReactNode = null;
  let marker: React.ReactNode = null;
  let note: React.ReactNode = null;
  const dots: React.ReactNode[] = [];

  if (method === "newton") {
    const step = newton[frame.k];
    const slideX = step.t + (step.next - step.t) * frame.slide;
    const slideY = step.residual * (1 - frame.slide);
    const landY = frame.f >= 0.7 ? step.nextResidual : 0;
    const markY = frame.f < 0.7 ? slideY : slideY + (landY - slideY) * frame.drop;
    const tx1 = w.center - w.half, tx2 = w.center + w.half;
    const line = (t: number) => step.residual + step.slope * (t - step.t);
    tangentLine = <g className="nr-tangent" style={{ opacity: frame.tangent }}>
      <line className="nr-tangent-line" clipPath={`url(#${clipId})`} x1={px(tx1)} y1={py(line(tx1))} x2={px(tx2)} y2={py(line(tx2))} />
    </g>;
    if (frame.f >= 0.3) {
      dots.push(<circle key="cross" className="nr-cross" cx={px(step.next)} cy={py(0)} r={6} style={{ opacity: frame.slide }} />);
    }
    if (frame.f >= 0.7) {
      dots.push(<line key="drop" className="nr-drop" x1={px(step.next)} x2={px(step.next)} y1={py(0)} y2={py(markY)} />);
    }
    for (let j = 0; j < frame.k; j += 1) {
      dots.push(<circle key={`old${j}`} className="nr-old" cx={px(newton[j].next)} cy={py(newton[j].nextResidual)} r={4} />);
    }
    dots.push(<circle key="from" className="nr-from" cx={px(step.t)} cy={py(step.residual)} r={5} />);
    marker = <circle className="nr-marker" cx={px(slideX)} cy={py(markY)} r={7} />;
    const labelFrom = `t${sub10(frame.k)} = ${fmt(step.t, 6)}`;
    const labelTo = `t${sub10(frame.k + 1)} = ${fmt(step.next, 6)}`;
    note = <>
      <text className="ex-label ex-label-strong" x={Math.min(px(step.t) + 10, right - 150)} y={py(step.residual) - 12}>{labelFrom}</text>
      {frame.slide > 0.95 && <text className="ex-label ex-label-strong nr-to" x={Math.min(Math.max(px(step.next) + 10, left + 4), right - 150)} y={py(0) + 24}>{labelTo}</text>}
    </>;
  } else {
    const step = bisection[frame.k];
    const shadeLo = step.lo + (step.nextLo - step.lo) * frame.slide;
    const shadeHi = step.hi + (step.nextHi - step.hi) * frame.slide;
    const markY = step.midResidual * frame.drop;
    tangentLine = <>
      <rect className="nr-bracket" x={px(shadeLo)} y={top} width={Math.max(0, px(shadeHi) - px(shadeLo))} height={bottom - top} />
      <line className="nr-bracket-edge" x1={px(shadeLo)} x2={px(shadeLo)} y1={top} y2={bottom} />
      <line className="nr-bracket-edge" x1={px(shadeHi)} x2={px(shadeHi)} y1={top} y2={bottom} />
    </>;
    for (let j = 0; j < frame.k; j += 1) {
      dots.push(<circle key={`old${j}`} className="nr-old" cx={px(bisection[j].mid)} cy={py(bisection[j].midResidual)} r={4} />);
    }
    dots.push(<line key="drop" className="nr-drop" x1={px(step.mid)} x2={px(step.mid)} y1={py(0)} y2={py(markY)} />);
    marker = <circle className="nr-marker" cx={px(step.mid)} cy={py(markY)} r={7} />;
    note = <text className="ex-label ex-label-strong" x={Math.min(Math.max(px(step.mid) + 10, left + 4), right - 170)} y={py(markY) + (markY >= 0 ? -12 : 22)}>
      {`c = ${fmt(step.mid, 6)}、F = ${sci(step.midResidual)}`}
    </text>;
  }

  return <figure className="ex-panel nr-panel">
    <figcaption className="ex-panel-title">残差 F(t) = t²+t−1 の曲線{wide ? "（拡大なし）" : offset ? `（根の周りを ×${scale.toLocaleString("en-US")} に拡大）` : "（区間の周りを拡大）"}</figcaption>
    <div className="ex-canvas" ref={ref}>
      <svg className="ex-svg" role="img" viewBox={`0 0 ${width} ${height}`}
        aria-label={method === "newton" ? "残差の曲線と、接線が F=0 と交わる点を次の値にする一手" : "残差の曲線と、区間の中点で符号を見て区間を半分にする一手"}>
        <defs>
          <clipPath id={clipId}><rect x={left} y={top} width={right - left} height={bottom - top} /></clipPath>
        </defs>
        <rect className="ex-ground" width={width} height={height} />
        <g className="ex-axes">
          <line x1={left} x2={right} y1={py(0)} y2={py(0)} />
          {ticks.map((t) => <g key={t}>
            <line x1={px(t)} x2={px(t)} y1={bottom} y2={bottom + 5} />
            <text x={px(t)} y={bottom + 22} textAnchor="middle">{tickLabel(t)}</text>
          </g>)}
          <text x={left - 6} y={py(0) + 5} textAnchor="end">0</text>
          <text x={left - 6} y={top + 10} textAnchor="end">{sci(w.yHalf)}</text>
          <text x={left - 6} y={bottom} textAnchor="end">{sci(-w.yHalf)}</text>
        </g>
        <text className="ex-axis-name" x={left + 4} y={top + 12}>F</text>
        <g clipPath={`url(#${clipId})`}>
          {method === "bisection" ? tangentLine : null}
          <line className="nr-root" x1={px(ROOT)} x2={px(ROOT)} y1={top} y2={bottom} />
          <path className="ex-curve" d={curve} />
          {method === "newton" ? tangentLine : null}
          {dots}
          {marker}
        </g>
        {note}
      </svg>
    </div>
    <p className="ex-hint">緑の縦線が根 t* = 0.618034 です。橙の印が、いま動かしている点です。</p>
  </figure>;
}

function DigitsPanel({ method, frame, newton, bisection }: {
  method: Method; frame: Frame; newton: readonly NewtonStep[]; bisection: readonly BisectionStep[];
}) {
  const { ref, viewport } = useStageViewport(BOUNDS, 0.4);
  const width = viewport.width;
  const rows = method === "newton"
    ? newton.slice(0, NEWTON_STEPS + 1).map((s, i) => ({
      label: `t${sub10(i)}`, value: i === 0 ? s.residual : newton[i - 1].nextResidual,
    }))
    : bisection.map((s, i) => ({ label: `c${sub10(i + 1)}`, value: s.midResidual }));
  const rowH = 30, left = 40, right = width - 78, top = 8;
  const height = top + rows.length * rowH + 30;
  const scale = (digitsValue: number) => (digitsValue / 12) * (right - left);
  // A bar appears when its point lands on the curve: Newton row i after step i−1 drops, bisection row i during step i.
  const reached = (i: number) => {
    if (method === "newton") {
      if (i === 0) return 1;
      if (i - 1 < frame.k) return 1;
      return i - 1 === frame.k ? frame.drop : 0;
    }
    if (i < frame.k) return 1;
    return i === frame.k ? frame.drop : 0;
  };
  return <figure className="ex-panel nr-panel">
    <figcaption className="ex-panel-title">残差 |F| の小ささ（右へ伸びるほど小さい。桁数 = −log₁₀|F|）</figcaption>
    <div className="ex-canvas" ref={ref}>
      <svg className="ex-svg" role="img" viewBox={`0 0 ${width} ${height}`} aria-label="各回の残差を、小数点以下の桁数の棒で表した図">
        <rect className="ex-ground" width={width} height={height} />
        <g className="ex-axes">
          {[0, 3, 6, 9, 12].map((d) => <g key={d}>
            <line x1={left + scale(d)} x2={left + scale(d)} y1={top} y2={top + rows.length * rowH} className="nr-grid" />
            <text x={left + scale(d)} y={top + rows.length * rowH + 20} textAnchor="middle">{d}桁</text>
          </g>)}
        </g>
        {rows.map((r, i) => {
          const y = top + i * rowH;
          const u = reached(i);
          return <g key={r.label} style={{ opacity: u > 0 ? 1 : 0.28 }}>
            <text className="ex-label" x={left - 6} y={y + 19} textAnchor="end">{r.label}</text>
            <rect className={i === rows.length - 1 || u < 1 ? "nr-bar nr-bar-now" : "nr-bar"} x={left} y={y + 5} height={rowH - 12}
              width={Math.max(2, scale(digits(r.value)) * u)} />
            <text className="ex-label" x={Math.min(left + scale(digits(r.value)) * u + 6, right + 6)} y={y + 19}>{u > 0 ? sci(r.value) : ""}</text>
          </g>;
        })}
      </svg>
    </div>
  </figure>;
}

function NewtonReadout({ steps, frame, finished }: { steps: readonly NewtonStep[]; frame: Frame; finished: boolean }) {
  const step = steps[frame.k];
  const factor = Math.abs(step.nextResidual) > 0 ? Math.abs(step.residual / step.nextResidual) : Infinity;
  const afterDigits = digits(step.nextResidual);
  return <>
    <p className="ex-verdict">
      {frame.f < 0.3 && !finished
        ? `いま t${sub10(frame.k)} = ${fmt(step.t, 6)} の点で接線を引いています。傾きは F′ = 2t+1 = ${fmt(step.slope, 4)} です。`
        : `接線が F = 0 と交わるのは t = ${fmt(step.next, 6)} です。そこから曲線へ落とすと、残差は ${sci(step.residual)} から ${sci(step.nextResidual)} へ、約 ${fmt(factor, 0)} 分の 1 になります。`}
    </p>
    <section aria-label="いまの一手の計算" className="ex-equation">
      <LiveMath label={`t${frame.k + 1} は ${fmt(step.t, 6)} 引く ${sci(step.residual)} 割る ${fmt(step.slope, 4)} で ${fmt(step.next, 6)}`}
        block markup={row(sub(mi("t"), row(mi("k"), mo("+"), mn("1"))), mo("="), sub(mi("t"), mi("k")), mo("−"),
          mi("F"), mo("("), sub(mi("t"), mi("k")), mo(")"), mo("/"), mi("F′"), mo("("), sub(mi("t"), mi("k")), mo(")"))} />
      <LiveMath label="数値を入れた形"
        block markup={row(signed(fmt(step.next, 6)), mo("="), signed(fmt(step.t, 6)), mo("−"), mn(sci(Math.abs(step.residual))), mo("/"), mn(fmt(step.slope, 4)))} />
    </section>
    <p className="ex-hint">この手の後、残差の桁数は {fmt(digits(step.residual), 1)} から {fmt(afterDigits, 1)} になります。傾き {fmt(dF(ROOT), 4)} の接線は、根の近くで曲線とほとんど重なるからです。</p>
  </>;
}

function BisectionReadout({ steps, frame, finished }: { steps: readonly BisectionStep[]; frame: Frame; finished: boolean }) {
  const step = steps[frame.k];
  const width = step.hi - step.lo;
  return <>
    <p className="ex-verdict">
      {`区間 [${fmt(step.lo, 4)}, ${fmt(step.hi, 4)}]（幅 ${fmt(width, 4)}）の中点 c = ${fmt(step.mid, 6)} で F(c) = ${sci(step.midResidual)}。`}
      {step.midResidual < 0 ? "負なので、左端を c に替えます。" : "正なので、右端を c に替えます。"}
      {finished ? ` ${steps.length} 回で幅は ${fmt(1 / 256, 4)} になります。` : ""}
    </p>
    <p className="ex-hint">区間に根が入っていることは保証されますが、残差 |F| は回ごとに減るとは限りません。1回で縮むのは区間の幅だけで、ちょうど半分です。</p>
  </>;
}
