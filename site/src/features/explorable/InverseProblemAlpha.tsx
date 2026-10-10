import { useId, useMemo, useState } from "react";

import { Slider } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import {
  discrepancyAlpha, INVERSE_ALPHA_MAX_LOG10, INVERSE_ALPHA_MIN_LOG10, INVERSE_DELTA, INVERSE_TRUTH, INVERSE_X, tikhonov,
} from "./math/inverseProblem";
import { alphaText, sig } from "./format";
import { useStageViewport } from "./svg";
import "./inverse-problem.css";

const BOUNDS = { xMin: 0, xMax: 1, yMin: -0.4, yMax: 1.4 };
const Y_MIN = -0.4, Y_MAX = 1.4;

export default function InverseProblemAlpha() {
  const [logAlpha, setLogAlpha] = useState(-6);
  const [showTruth, setShowTruth] = useState(true);
  const alpha = 10 ** logAlpha;
  const reading = useMemo(() => tikhonov(alpha), [alpha]);
  const dpAlpha = useMemo(() => discrepancyAlpha(), []);
  const maxAbs = Math.max(...reading.m.map(Math.abs));
  const side = reading.residual < INVERSE_DELTA * 0.95
    ? "残差が δ より小さいので、雑音まで合わせすぎている側です。"
    : reading.residual > INVERSE_DELTA * 1.05
      ? "残差が δ より大きいので、罰則が観測の形まで削り始めている側です。"
      : "残差がほぼ δ に等しい、残差原理が選ぶ重みの近くです。";
  const errorText = showTruth ? `真の分布との相対誤差は${sig(reading.relativeError)}` : "真の分布を隠しているので誤差は表示しません";
  const checkpoint = (Math.abs(logAlpha - Math.log10(dpAlpha)) < 0.05)
    ? ""
    : `残差原理が選ぶのは α=${alphaText(dpAlpha)} です。`;

  return <ExplorableFrame
    id="inverse-problem-alpha"
    controls={<div className="ip-controls">
      <Slider
        label="罰則の重み α（対数目盛り）"
        display={`α = ${alphaText(alpha)}`}
        valueText={`アルファ ${alphaText(alpha)}`}
        min={INVERSE_ALPHA_MIN_LOG10} max={INVERSE_ALPHA_MAX_LOG10} step={0.1}
        value={logAlpha} onChange={setLogAlpha}
        hint="左ほど観測に合わせ、右ほど罰則が強くなります。"
      />
      <label className="ip-answer">
        <input type="checkbox" checked={showTruth} onChange={(event) => setShowTruth(event.target.checked)} />
        真の分布を重ねる（答え合わせ用。実際の問題では分かりません）
      </label>
    </div>}
    stage={<>
      <ProfilePanel m={reading.m} showTruth={showTruth} maxAbs={maxAbs} />
      <ErrorPanel error={reading.relativeError} residual={reading.residual} showTruth={showTruth} />
    </>}
    readout={<>
      <p className="ex-verdict">{side}{checkpoint}</p>
      <ul className="ip-metrics">
        <li>相対誤差: {showTruth ? sig(reading.relativeError) : "（真の分布を隠しています）"}</li>
        <li>観測とのずれ ‖Gm−d‖: {sig(reading.residual)}（雑音の大きさ δ = {sig(INVERSE_DELTA)}）</li>
        <li>解の長さ ‖m‖: {sig(reading.length)}</li>
      </ul>
    </>}
    summary={`罰則の重み α は${alphaText(alpha)}。${errorText}。観測とのずれは${sig(reading.residual)}で、雑音の大きさ δ は${sig(INVERSE_DELTA)}です。復元した分布の絶対値の最大は${sig(maxAbs)}で、真の分布の最大は1です。${side}`}
  />;
}

function ProfilePanel({ m, showTruth, maxAbs }: { m: readonly number[]; showTruth: boolean; maxAbs: number }) {
  const { ref, viewport } = useStageViewport(BOUNDS, 0.62);
  const clipId = useId();
  const width = viewport.width, height = Math.max(210, viewport.height);
  const left = 44, right = width - 12, top = 14, bottom = height - 40;
  const px = (x: number) => left + x * (right - left);
  const py = (y: number) => bottom - (y - Y_MIN) / (Y_MAX - Y_MIN) * (bottom - top);
  const path = (values: readonly number[]) => values.map((v, i) => `${i ? "L" : "M"}${px(INVERSE_X[i]).toFixed(1)} ${py(v).toFixed(1)}`).join("");
  const clipped = maxAbs > Y_MAX;
  return <figure className="ex-panel">
    <figcaption className="ex-panel-title">復元した分布と真の分布</figcaption>
    <div className="ex-canvas" ref={ref}>
      <svg className="ex-svg" role="img"
        aria-label={`橙が復元した温度分布、破線が真の分布。復元の絶対値の最大は${sig(maxAbs)}`}
        viewBox={`0 0 ${width} ${height}`}>
        <defs><clipPath id={clipId}><rect x={left} y={top} width={right - left} height={bottom - top} /></clipPath></defs>
        <rect className="ex-ground" width={width} height={height} />
        <g className="ex-axes">
          <line x1={left} x2={right} y1={py(0)} y2={py(0)} />
          <line x1={left} x2={left} y1={top} y2={bottom} />
          {[0, 0.5, 1].map(x => <text key={x} x={px(x)} y={bottom + 20} textAnchor="middle">{x}</text>)}
          {[0, 1].map(y => <text key={y} x={left - 6} y={py(y) + 5} textAnchor="end">{y}</text>)}
        </g>
        <text className="ex-axis-name" x={right} y={height - 6} textAnchor="end">位置 x</text>
        <text className="ex-axis-name" x={left + 6} y={top + 14}>温度</text>
        <g clipPath={`url(#${clipId})`}>
          {showTruth && <path className="ip-truth" d={path(INVERSE_TRUTH)} />}
          <path className="ip-recon" d={path(m)} />
        </g>
        {clipped && <text className="ex-label ip-clip-note" x={right} y={top + 14} textAnchor="end">図の範囲外へ振れる（最大 {sig(maxAbs)}）</text>}
      </svg>
    </div>
    <p className="ex-hint">橙の実線が復元、紺の破線が真の分布です。縦軸は−0.4〜1.4で固定し、範囲外は切り取っています。</p>
  </figure>;
}

function LogRow({ y, label, value, domain, ticks, width, left, right, marker, hidden }: {
  y: number; label: string; value: number; domain: [number, number]; ticks: number[]; width: number;
  left: number; right: number; marker?: { value: number; text: string }; hidden?: boolean;
}) {
  const [lo, hi] = domain.map(Math.log10);
  const pos = (v: number) => left + (Math.log10(Math.min(Math.max(v, domain[0]), domain[1])) - lo) / (hi - lo) * (right - left);
  return <g data-row={label}>
    <text className="ex-label ex-label-strong" x={left} y={y - 24}>{label}{hidden ? "：真の分布を隠しています" : `：${sig(value)}`}</text>
    <g className="ex-axes">
      <line x1={left} x2={right} y1={y} y2={y} />
      {ticks.map(t => <g key={t}><line x1={pos(t)} x2={pos(t)} y1={y - 4} y2={y + 4} /><text x={pos(t)} y={y + 22} textAnchor="middle">{t >= 1 ? String(t) : alphaText(t)}</text></g>)}
    </g>
    {!hidden && <>
      <rect className="ip-bar" x={left} y={y - 9} width={Math.max(0, pos(value) - left)} height={18} />
      <circle className="ip-dot" cx={pos(value)} cy={y} r={7} />
    </>}
    {marker && <>
      <line className="ip-delta" x1={pos(marker.value)} x2={pos(marker.value)} y1={y - 16} y2={y + 12} />
      <text className="ex-label ip-delta-text" x={Math.min(pos(marker.value) + 6, width - 4)} y={y - 12} textAnchor={pos(marker.value) > width - 90 ? "end" : "start"}>{marker.text}</text>
    </>}
  </g>;
}

function ErrorPanel({ error, residual, showTruth }: { error: number; residual: number; showTruth: boolean }) {
  const { ref, viewport } = useStageViewport(BOUNDS, 0.4);
  const width = viewport.width, height = 190;
  const left = 16, right = width - 18;
  return <figure className="ex-panel">
    <figcaption className="ex-panel-title">誤差と残差</figcaption>
    <div className="ex-canvas" ref={ref}>
      <svg className="ex-svg" role="img"
        aria-label={`相対誤差${showTruth ? sig(error) : "は非表示"}、観測とのずれ${sig(residual)}、雑音の大きさ δ ${sig(INVERSE_DELTA)}`}
        viewBox={`0 0 ${width} ${height}`}>
        <rect className="ex-ground" width={width} height={height} />
        <LogRow y={52} label="相対誤差" value={error} domain={[0.01, 100]} ticks={[0.01, 1, 100]} width={width} left={left} right={right} hidden={!showTruth} />
        <LogRow y={142} label="観測とのずれ" value={residual} domain={[0.001, 1]} ticks={[0.001, 0.01, 0.1, 1]} width={width} left={left} right={right}
          marker={{ value: INVERSE_DELTA, text: `δ = ${sig(INVERSE_DELTA)}` }} />
      </svg>
    </div>
    <p className="ex-hint">どちらも対数目盛りです。青緑の破線 δ は雑音の大きさで、真の分布を知らなくても計算できます。</p>
  </figure>;
}
