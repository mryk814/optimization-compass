import { PlayerBar, Slider } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import { fmt } from "./format";
import { LiveMath, mn, mo, row, signed } from "./mathml";
import {
  boundaryS, determinant, eigenvalues, objective, psdState, R_LIMIT, SWEEP_LENGTH, sweepR, X22,
  type PsdState,
} from "./math/psdSlice";
import { useStageViewport } from "./svg";
import { useManualOrPlayback } from "./useManualOrPlayback";
import { useTimeline } from "./useTimeline";

const R_MIN = -3, R_MAX = 3;
const BOUNDS = { xMin: 0, xMax: 1, yMin: 0, yMax: 1 };
const PANEL_HEIGHT = 340;

const STATE_TEXT: Record<PsdState, string> = {
  inside: "半正定値（可行）",
  boundary: "境界（可行で、固有値の一つが 0）",
  outside: "半正定値ではない（可行でない）",
};

export default function PsdSliceBoundary() {
  const timeline = useTimeline(SWEEP_LENGTH, 12);
  const { value: r, set: setR } = useManualOrPlayback(timeline, 1, sweepR, false);
  const state = psdState(r);
  const [low, high] = eigenvalues(r);
  const det = determinant(r);

  return <ExplorableFrame
    id="sdp-psd-boundary"
    controls={<Slider label="共分散 r（非対角成分）" display={fmt(r, 2)} min={R_MIN} max={R_MAX} step={0.05} value={r} onChange={setR}
      hint="対角成分は 1 と 4 に固定しています。" />}
    stage={<>
      <PlanePanel r={r} state={state} />
      <EigenPanel r={r} low={low} high={high} det={det} state={state} />
    </>}
    player={<PlayerBar timeline={timeline} stepLabel="r の掃引" positionText={`r = ${fmt(r, 2)}`} showButtonNames />}
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
          ? `全成分が正でも、固有値 ${fmt(low, 3)} が負なので、ある方向で二次形式 vᵀXv が負になります。目的 −r だけを見ると良く見えても、この点は選べません。`
          : state === "boundary"
            ? "目的 −r を下げたい向き（r を増やす向き）の行き止まりです。これ以上 r を増やすと、固有値の積 4 − r² が負になり、小さい方の固有値が 0 を下回ります。"
            : `目的 −r は r を増やすほど小さくなるので、点は右へ進みたがります。境界まで r をあと ${fmt(R_LIMIT - r, 2)} です。`}
      </p>
    </>}
    summary={`対角を1と4に固定した2×2行列で、非対角成分rを${fmt(r, 2)}にしています。行列式は${fmt(det, 3)}、固有値は${fmt(low, 3)}と${fmt(high, 3)}で、${STATE_TEXT[state]}です。目的 −r は${fmt(objective(r), 2)}で、r を増やすほど小さくなります。r=2で固有値の一つが0になり、それを超えると負になります。`}
  />;
}

function PlanePanel({ r, state }: { r: number; state: PsdState }) {
  const { ref, viewport } = useStageViewport(BOUNDS, 0.5);
  const width = viewport.width, height = PANEL_HEIGHT;
  const left = 40, right = width - 14, top = 62, bottom = height - 34;
  const rMin = -3.4, rMax = 3.4, sMin = -0.4, sMax = 9.4;
  const px = (v: number) => left + ((v - rMin) / (rMax - rMin)) * (right - left);
  const py = (v: number) => bottom - ((v - sMin) / (sMax - sMin)) * (bottom - top);
  const parabola = Array.from({ length: 61 }, (_, i) => {
    const t = -3.05 + (6.1 * i) / 60;
    return `${i ? "L" : "M"}${px(t).toFixed(1)} ${py(boundaryS(t)).toFixed(1)}`;
  }).join("");
  const region = `${parabola}L${px(3.05)} ${py(sMax)}L${px(-3.05)} ${py(sMax)}Z`;
  const stripY = 34;
  const liveAnchor = r > 2 ? "end" : r < -2 ? "start" : "middle";
  return <figure className="ex-panel psd-panel">
    <figcaption className="ex-panel-title">(r, s) 平面：s = X₂₂、半正定値になる範囲は s ≥ r²</figcaption>
    <div className="ex-canvas" ref={ref}>
      <svg className="ex-svg" role="img" viewBox={`0 0 ${width} ${height}`}
        aria-label={`非対角成分rと、2列目の対角成分sの平面。点は(${fmt(r, 2)}, ${X22})で、${STATE_TEXT[state]}。目的 −r は右へ行くほど小さくなる`}>
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
        <g className="psd-objective">
          <text className="ex-label ex-label-strong" x={left} y={16}>目的 −r は右ほど小さい（良い）</text>
          <line className="psd-objective-arrow" x1={left} x2={right - 8} y1={stripY} y2={stripY} />
          <path className="psd-objective-head" d={`M${right} ${stripY}L${right - 12} ${stripY - 6}L${right - 12} ${stripY + 6}Z`} />
          <line className={`psd-contour psd-contour-${state}`} x1={px(r)} x2={px(r)} y1={stripY + 4} y2={bottom} />
          <text className="ex-label ex-label-strong" x={Math.min(Math.max(px(r), left + 4), right - 4)} y={stripY + 22} textAnchor={liveAnchor}>
            −r = {fmt(objective(r), 2)}
          </text>
        </g>
        <g className="psd-point" style={{ transform: `translate(${px(r)}px, ${py(X22)}px)` }}>
          <circle className={`psd-dot psd-dot-${state}`} r={9} />
        </g>
        <text className="ex-label ex-label-strong" x={px(-2)} y={py(X22) + 22} textAnchor="middle">r = −2</text>
        <text className="ex-label ex-label-strong" x={px(2)} y={py(X22) + 22} textAnchor="middle">r = 2</text>
      </svg>
    </div>
    <p className="ex-hint">緑の線分が、点が可行でいられる範囲です。縦の点線は目的 −r の等高線で、右へ動かすほど目的が下がります。点が放物線に触れる r = ±2 が境界で、そこで行列式が 0 になります。</p>
  </figure>;
}

function EigenPanel({ r, low, high, det, state }: { r: number; low: number; high: number; det: number; state: PsdState }) {
  const { ref, viewport } = useStageViewport(BOUNDS, 0.5);
  const width = viewport.width, height = PANEL_HEIGHT;
  const left = 40, right = width - 14, top = 18, bottom = height - 100;
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
  const productClass = state === "outside" ? "psd-sum-bad" : state === "boundary" ? "psd-sum-zero" : "psd-sum-ok";
  return <figure className="ex-panel psd-panel">
    <figcaption className="ex-panel-title">固有値：どちらも 0 以上なら半正定値</figcaption>
    <div className="ex-canvas" ref={ref}>
      <svg className="ex-svg" role="img" viewBox={`0 0 ${width} ${height}`}
        aria-label={`固有値は${fmt(low, 3)}と${fmt(high, 3)}。和は5、積は行列式と同じ${fmt(det, 3)}。${STATE_TEXT[state]}`}>
        <rect className="ex-ground" width={width} height={height} />
        <rect className="psd-forbidden" x={left} y={py(0)} width={right - left} height={bottom - py(0)} />
        <g className="ex-axes">
          <line x1={left} x2={right} y1={py(0)} y2={py(0)} />
          {[0, 2, 4, 6].map((v) => <text key={v} x={left - 6} y={py(v) + 4} textAnchor="end">{v}</text>)}
          <text x={left - 6} y={py(-2) + 4} textAnchor="end">−2</text>
        </g>
        <text className="ex-label" x={right - 4} y={bottom - 4} textAnchor="end">0 未満は半正定値でない</text>
        {bar(low, cols[0], "小さい方 λ₁", low < -1e-9, state === "boundary")}
        {bar(high, cols[1], "大きい方 λ₂", false, false)}
        <text className="ex-label ex-label-strong psd-sum-ok" x={left} y={height - 44}>和 λ₁ + λ₂ = {fmt(low + high, 2)}（1 + 4 で一定）</text>
        <text className={`ex-label ex-label-strong ${productClass}`} x={left} y={height - 16}>
          積 λ₁λ₂ = 4 − r² = {fmt(4 - r * r, 2)}（行列式）
        </text>
      </svg>
    </div>
    <p className="ex-hint">和は r によらず 5 のままなので、積 4 − r² が 0 になる r = 2 で、小さい方が 0 に着きます。積が負になると、片方の固有値は負です。</p>
  </figure>;
}
