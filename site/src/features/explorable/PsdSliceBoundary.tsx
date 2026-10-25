import { useState } from "react";

import { PlayerBar, Slider } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import { fmt } from "./format";
import { LiveMath, mn, mo, row, signed } from "./mathml";
import { boundaryS, determinant, eigenvalues, objective, psdState, R_LIMIT, X11, X22, type PsdState } from "./math/psdSlice";
import { useStageViewport } from "./svg";
import { useManualOrPlayback } from "./useManualOrPlayback";
import { useTimeline } from "./useTimeline";

const R_MIN = -3, R_MAX = 3, SWEEP_STEPS = 60;
const BOUNDS = { xMin: 0, xMax: 1, yMin: 0, yMax: 1 };

const STATE_TEXT: Record<PsdState, string> = {
  inside: "半正定値（可行）",
  boundary: "境界（可行で、固有値の一つが 0）",
  outside: "半正定値ではない（可行でない）",
};

export default function PsdSliceBoundary() {
  const timeline = useTimeline(SWEEP_STEPS, 12);
  const { value: r, set: setR } = useManualOrPlayback(timeline, 1, (p) => p * 0.05, false);
  const state = psdState(r);
  const [low, high] = eigenvalues(r);
  const det = determinant(r);

  return <ExplorableFrame
    id="sdp-psd-boundary"
    controls={<Slider label="共分散 r（非対角成分）" display={fmt(r, 2)} min={R_MIN} max={R_MAX} step={0.05} value={r} onChange={setR}
      hint="対角成分は 1 と 4 に固定しています。" />}
    stage={<>
      <PlanePanel r={r} state={state} />
      <EigenPanel low={low} high={high} state={state} />
    </>}
    player={<PlayerBar timeline={timeline} stepLabel="r の掃引" positionText={`r = ${fmt(r, 2)}`} />}
    readout={<>
      <p className={`ex-verdict ${state === "outside" ? "ex-tone-bad" : state === "boundary" ? "ex-tone-swing" : "ex-tone-good"}`}>
        r = {fmt(r, 2)}：{STATE_TEXT[state]}。行列式 4 − r² = {fmt(det, 3)}、固有値は {fmt(low, 3)} と {fmt(high, 3)}、目的 −r = {fmt(objective(r), 2)}。
      </p>
      <LiveMath block label={`行列は 1、${fmt(r, 2)}、${fmt(r, 2)}、4`}
        markup={row(
          mo("("),
          `<mtable><mtr><mtd>${mn("1")}</mtd><mtd>${signed(fmt(r, 2))}</mtd></mtr><mtr><mtd>${signed(fmt(r, 2))}</mtd><mtd>${mn("4")}</mtd></mtr></mtable>`,
          mo(")"),
        )} />
      <p className="ex-hint">
        {state === "outside"
          ? `全成分が正でも、固有値 ${fmt(low, 3)} が負なので、ある方向で二次形式 vᵀXv が負になります。`
          : state === "boundary"
            ? "目的 −r を最小にする最大の r です。これ以上 r を増やすと、固有値が負になります。"
            : `r を ${fmt(R_LIMIT - Math.abs(r), 2)} だけ動かすと境界に着きます。`}
      </p>
    </>}
    summary={`対角を1と4に固定した2×2行列で、非対角成分rを${fmt(r, 2)}にしています。行列式は${fmt(det, 3)}、固有値は${fmt(low, 3)}と${fmt(high, 3)}で、${STATE_TEXT[state]}です。r=2で固有値の一つが0になり、それを超えると負になります。`}
  />;
}

function PlanePanel({ r, state }: { r: number; state: PsdState }) {
  const { ref, viewport } = useStageViewport(BOUNDS, 0.5);
  const width = viewport.width, height = 300;
  const left = 40, right = width - 14, top = 14, bottom = height - 34;
  const rMin = -3.4, rMax = 3.4, sMin = -0.4, sMax = 9.4;
  const px = (v: number) => left + ((v - rMin) / (rMax - rMin)) * (right - left);
  const py = (v: number) => bottom - ((v - sMin) / (sMax - sMin)) * (bottom - top);
  const parabola = Array.from({ length: 61 }, (_, i) => {
    const t = -3.05 + (6.1 * i) / 60;
    return `${i ? "L" : "M"}${px(t).toFixed(1)} ${py(boundaryS(t)).toFixed(1)}`;
  }).join("");
  const region = `${parabola}L${px(3.05)} ${py(sMax)}L${px(-3.05)} ${py(sMax)}Z`;
  return <figure className="ex-panel psd-panel">
    <figcaption className="ex-panel-title">(r, s) 平面：X₁₁ = 1 なら、半正定値になる範囲は s ≥ r²</figcaption>
    <div className="ex-canvas" ref={ref}>
      <svg className="ex-svg" role="img" viewBox={`0 0 ${width} ${height}`}
        aria-label={`非対角成分rと、2列目の対角成分sの平面。点は(${fmt(r, 2)}, ${X22})で、${STATE_TEXT[state]}`}>
        <rect className="ex-ground" width={width} height={height} />
        <path className="psd-region" d={region} />
        <path className="psd-edge" d={parabola} />
        <g className="ex-axes">
          <line x1={left} x2={right} y1={py(0)} y2={py(0)} />
          <line x1={px(0)} x2={px(0)} y1={top} y2={bottom} />
          {[-3, -2, -1, 0, 1, 2, 3].map((t) => <g key={t}>
            <line x1={px(t)} x2={px(t)} y1={py(0)} y2={py(0) + 5} />
            <text x={px(t)} y={bottom + 22} textAnchor="middle">{t}</text>
          </g>)}
          {[0, 4, 9].map((s) => <text key={s} x={left - 6} y={py(s) + 4} textAnchor="end">{s}</text>)}
        </g>
        <text className="ex-axis-name" x={right} y={bottom - 8} textAnchor="end">r</text>
        <text className="ex-axis-name" x={left + 8} y={top + 12}>s</text>
        <text className="ex-label ex-label-strong" x={px(0)} y={py(7.2)} textAnchor="middle">可行（s ≥ r²）</text>
        <line className="psd-fixed" x1={left} x2={right} y1={py(X22)} y2={py(X22)} />
        <text className="ex-label" x={right - 4} y={py(X22) - 24} textAnchor="end">s = X₂₂ = 4 に固定</text>
        <line className="psd-feasible-segment" x1={px(-R_LIMIT)} x2={px(R_LIMIT)} y1={py(X22)} y2={py(X22)} />
        <g className="psd-point" style={{ transform: `translate(${px(r)}px, ${py(X22)}px)` }}>
          <circle className={`psd-dot psd-dot-${state}`} r={9} />
        </g>
        <text className="ex-label ex-label-strong" x={px(-2)} y={py(X22) + 22} textAnchor="middle">r = −2</text>
        <text className="ex-label ex-label-strong" x={px(2)} y={py(X22) + 22} textAnchor="middle">r = 2</text>
      </svg>
    </div>
    <p className="ex-hint">緑の線分が、点が可行でいられる範囲です。点が放物線に触れる r = ±2 が境界で、そこで行列式が 0 になります。</p>
  </figure>;
}

function EigenPanel({ low, high, state }: { low: number; high: number; state: PsdState }) {
  const { ref, viewport } = useStageViewport(BOUNDS, 0.5);
  const width = viewport.width, height = 300;
  const left = 40, right = width - 14, top = 18, bottom = height - 44;
  const vMin = -2.4, vMax = 6.5;
  const py = (v: number) => bottom - ((v - vMin) / (vMax - vMin)) * (bottom - top);
  const barW = Math.min(76, (right - left) * 0.24);
  const cols = [left + (right - left) * 0.3, left + (right - left) * 0.7];
  const bar = (value: number, cx: number, name: string, negative: boolean, zero: boolean) => {
    const y0 = py(0);
    const y1 = py(value);
    return <g key={name}>
      <rect className={negative ? "psd-bar psd-bar-negative" : zero ? "psd-bar psd-bar-zero" : "psd-bar"}
        x={cx - barW / 2} y={Math.min(y0, y1)} width={barW} height={Math.max(2, Math.abs(y1 - y0))} />
      <text className="ex-label ex-label-strong" x={cx} y={value >= 0 ? Math.min(y0, y1) - 8 : Math.max(y0, y1) + 20} textAnchor="middle">
        {zero ? "0（境界）" : fmt(value, 2)}
      </text>
      <text className="ex-label" x={cx} y={bottom + 28} textAnchor="middle">{name}</text>
    </g>;
  };
  return <figure className="ex-panel psd-panel">
    <figcaption className="ex-panel-title">固有値：どちらも 0 以上なら半正定値</figcaption>
    <div className="ex-canvas" ref={ref}>
      <svg className="ex-svg" role="img" viewBox={`0 0 ${width} ${height}`}
        aria-label={`固有値は${fmt(low, 3)}と${fmt(high, 3)}。${STATE_TEXT[state]}`}>
        <rect className="ex-ground" width={width} height={height} />
        <rect className="psd-forbidden" x={left} y={py(0)} width={right - left} height={bottom - py(0)} />
        <g className="ex-axes">
          <line x1={left} x2={right} y1={py(0)} y2={py(0)} />
          {[0, 2, 4, 6].map((v) => <text key={v} x={left - 6} y={py(v) + 4} textAnchor="end">{v}</text>)}
          <text x={left - 6} y={py(-2) + 4} textAnchor="end">−2</text>
        </g>
        <text className="ex-label" x={right - 4} y={bottom - 4} textAnchor="end">0 未満は半正定値でない</text>
        {bar(low, cols[0], "小さい方", low < -1e-9, state === "boundary")}
        {bar(high, cols[1], "大きい方", false, false)}
      </svg>
    </div>
    <p className="ex-hint">二つの固有値の和は常に 5（= 1 + 4）です。小さい方が 0 を下回った瞬間に、点は可行でなくなります。</p>
  </figure>;
}
