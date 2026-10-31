import { useState } from "react";

import { Choice, PlayerBar, Slider } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import { fmt } from "./format";
import {
  balanceAt, BEST_Q, freeBalance, H, Q_MAX, SWEEP_LENGTH, sweepQ, TARGET,
  type FreeBalance, type HeatBalance,
} from "./math/pdeHeat";
import { useStageViewport } from "./svg";
import { useManualOrPlayback } from "./useManualOrPlayback";
import { useTimeline } from "./useTimeline";

type Mode = "design" | "free";
const BOUNDS = { xMin: 0, xMax: 1, yMin: 0, yMax: 1 };
const J_MAX = 1.95;
const RESIDUAL_MAX = 14;
/** In the free mode u is fixed at the target by default, the tempting "perfect" choice. */
const FREE_U_START = 1;
/** Where the playback rests: the best q in the real model, the one consistent q (= 9u) in the free mode. */
const REST_AT: Record<Mode, number> = { design: BEST_Q, free: 9 };

const MODE_OPTIONS: ReadonlyArray<{ value: Mode; label: string }> = [
  { value: "design", label: "q から u を計算する（実際の問題）" },
  { value: "free", label: "u を自由に決める（PDE を無視）" },
];

type Shown = HeatBalance & { residual: number; required: number };

export default function PdeHeatSourceBalance() {
  const [mode, setMode] = useState<Mode>("design");
  const [freeU, setFreeU] = useState(FREE_U_START);
  const timeline = useTimeline(SWEEP_LENGTH, 10);
  const { value: q, set: setQ } = useManualOrPlayback(timeline, mode === "design" ? BEST_Q : 0, (p) => sweepQ(p, REST_AT[mode]), false);
  const free = mode === "free";
  const shown: Shown = free
    ? freeBalance(freeU, q)
    : { ...balanceAt(q), residual: 0, required: 9 * balanceAt(q).u[0] };
  const atBest = !free && Math.abs(q - BEST_Q) < 1e-9;
  const consistent = shown.residual < 1e-9;

  const switchMode = (next: Mode) => {
    timeline.seek(0);
    setMode(next);
    setQ(next === "design" ? BEST_Q : 0);
  };

  const verdict = free
    ? consistent
      ? `u = ${fmt(freeU, 2)} が成り立つ熱源は q = ${fmt(shown.required, 2)} だけで、いまちょうど一致し、状態残差は 0 です。合計は ${fmt(shown.total, 3)} で、q = 4.5 の最小 0.500 より大きくなります。`
      : `合計 ${fmt(shown.total, 3)} は小さく見えても、状態残差 ‖Ku − q‖ が ${fmt(shown.residual, 2)} あります。u = ${fmt(freeU, 2)} を保つには熱源 ${fmt(shown.required, 2)} が要るのに、いまは ${fmt(q, 2)} です。この u は実現できません。`
    : atBest
      ? "温度のずれ 0.250 と熱源の罰則 0.250 がちょうど釣り合い、合計 0.500 は最小です。"
      : shown.misfit > shown.penalty
        ? `温度のずれ ${fmt(shown.misfit, 3)} が罰則 ${fmt(shown.penalty, 3)} より大きく、熱源を強くすると合計は下がります。`
        : `熱源の罰則 ${fmt(shown.penalty, 3)} がずれ ${fmt(shown.misfit, 3)} より大きく、熱源を弱くすると合計は下がります。`;

  return <ExplorableFrame
    id="pde-heat-source-balance"
    controls={<>
      <Choice<Mode> legend="u の決め方" value={mode} options={MODE_OPTIONS} onChange={switchMode} />
      <Slider label="熱源の強さ q（両方の点で同じ）" display={fmt(q, 2)} min={0} max={Q_MAX} step={0.25} value={q} onChange={setQ}
        hint={free ? "二つの熱源は別々には動かせません。" : "記事の表は q = 0、4.5、9 です。二つの熱源は別々には動かせません。"} />
      {free && <Slider label="温度 u（両方の点で同じ）" display={fmt(freeU, 2)} min={0} max={1.5} step={0.05} value={freeU}
        onChange={(v) => { timeline.seek(0); setFreeU(v); }} />}
    </>}
    stage={<>
      <RodPanel q={q} shown={shown} free={free} />
      <BreakdownPanel misfit={shown.misfit} penalty={shown.penalty} residual={shown.residual} free={free} />
      <CurvePanel q={q} total={shown.total} free={free} />
    </>}
    player={<PlayerBar timeline={timeline} stepLabel="q の掃引" positionText={`q = ${fmt(q, 2)}`} showButtonNames />}
    readout={<>
      <p className="ex-verdict">{verdict}</p>
      <div className="rb-scroll"><table className="ex-table">
        <thead><tr><th scope="col">熱源 q</th><th scope="col">状態 u</th><th scope="col">温度のずれの項</th><th scope="col">熱源の罰則</th><th scope="col">合計 J</th><th scope="col">状態残差 ‖Ku − q‖</th></tr></thead>
        <tbody>
          <tr className={atBest ? "ex-row-best" : undefined}>
            <td>({fmt(q, 2)}, {fmt(q, 2)})</td>
            <td>({fmt(shown.u[0], 3)}, {fmt(shown.u[1], 3)})</td>
            <td>{fmt(shown.misfit, 3)}</td><td>{fmt(shown.penalty, 3)}</td><td>{fmt(shown.total, 3)}</td>
            <td>{fmt(shown.residual, 3)}</td>
          </tr>
        </tbody>
      </table></div>
      <p className="ex-hint">
        {free
          ? "温度の目標は 1 です。u を手で決めると、状態方程式 Ku = q は自動では成り立ちません。残差が 0 でない点は、実際の棒では起こらない温度です。"
          : "温度の目標は 1 です。u = K⁻¹q は、q が決まると自動で決まる状態で、q を動かすたびに状態方程式 Ku = q を解き直しています。そのため状態残差はいつも 0 です。"}
      </p>
    </>}
    summary={free
      ? `温度uを${fmt(freeU, 2)}、熱源qを${fmt(q, 2)}と別々に決めています。合計は${fmt(shown.total, 3)}、状態残差は${fmt(shown.residual, 2)}で、${consistent ? "状態方程式を満たしています" : "状態方程式を満たしていません"}。`
      : `熱源の強さqを${fmt(q, 2)}にすると、内部2点の温度は${fmt(shown.u[0], 3)}になります。温度のずれの項は${fmt(shown.misfit, 3)}、熱源の罰則は${fmt(shown.penalty, 3)}、合計は${fmt(shown.total, 3)}です。qが4.5のとき二つの項が0.25で等しく、合計0.5が最小です。`}
  />;
}

function RodPanel({ q, shown, free }: { q: number; shown: Shown; free: boolean }) {
  const { ref, viewport } = useStageViewport(BOUNDS, 0.5);
  const width = viewport.width, height = 300;
  const left = 36, right = width - 20, top = 20, base = 188;
  const uMax = 1.5;
  const px = (s: number) => left + s * (right - left);
  const py = (u: number) => base - (u / uMax) * (base - top);
  const nodes = [0, H, 2 * H, 1];
  const values = [0, shown.u[0], shown.u[1], 0];
  const profile = nodes.map((s, i) => `${i ? "L" : "M"}${px(s).toFixed(1)} ${py(values[i]).toFixed(1)}`).join("");
  const arrowLen = (q / Q_MAX) * 54;
  const needLen = (shown.required / Q_MAX) * 54;
  return <figure className="ex-panel pde-panel">
    <figcaption className="ex-panel-title">棒の温度 u（両端は 0 に固定）</figcaption>
    <div className="ex-canvas" ref={ref}>
      <svg className="ex-svg" role="img" viewBox={`0 0 ${width} ${height}`}
        aria-label={`熱源${fmt(q, 2)}のとき、内部2点の温度は${fmt(shown.u[0], 3)}で、目標1との差は${fmt(TARGET - shown.u[0], 3)}です`}>
        <rect className="ex-ground" width={width} height={height} />
        <g className="ex-axes">
          <line x1={left} x2={right} y1={base} y2={base} />
          {[0, 0.5, 1].map((u) => <text key={u} x={left - 6} y={py(u) + 4} textAnchor="end">{u}</text>)}
        </g>
        <line className="pde-target" x1={left} x2={right} y1={py(TARGET)} y2={py(TARGET)} />
        <text className="ex-label ex-label-strong" x={right} y={py(TARGET) - 8} textAnchor="end">目標温度 1</text>
        {[1, 2].map((i) => <line key={i} className="pde-gap" x1={px(nodes[i])} x2={px(nodes[i])} y1={py(values[i])} y2={py(TARGET)} />)}
        <path className={free ? "ex-curve pde-curve-free" : "ex-curve"} d={profile} />
        {[1, 2].map((i) => <circle key={i} className="ex-head" cx={px(nodes[i])} cy={py(values[i])} r={7} />)}
        {[0, 3].map((i) => <rect key={i} className="pde-wall" x={px(nodes[i]) - 5} y={py(0) - 18} width={10} height={18} />)}
        {!free && [1, 2].map((i) => <line key={`link${i}`} className="pde-link" x1={px(nodes[i])} x2={px(nodes[i])} y1={base + 8} y2={py(values[i]) + 10} />)}
        {[1, 2].map((i) => <g key={i}>
          <line className="pde-heater" x1={px(nodes[i]) - (free ? 8 : 0)} x2={px(nodes[i]) - (free ? 8 : 0)} y1={base + 12 + arrowLen} y2={base + 12} />
          {arrowLen > 3 && <path className="pde-heater-head" d={`M${px(nodes[i]) - (free ? 8 : 0) - 6} ${base + 18}L${px(nodes[i]) - (free ? 8 : 0)} ${base + 8}L${px(nodes[i]) - (free ? 8 : 0) + 6} ${base + 18}Z`} />}
          {free && <g>
            <line className="pde-need" x1={px(nodes[i]) + 8} x2={px(nodes[i]) + 8} y1={base + 12 + needLen} y2={base + 12} />
            {needLen > 3 && <path className="pde-need-head" d={`M${px(nodes[i]) + 2} ${base + 18}L${px(nodes[i]) + 8} ${base + 8}L${px(nodes[i]) + 14} ${base + 18}Z`} />}
          </g>}
        </g>)}
        <text className="ex-label" x={(px(nodes[1]) + px(nodes[2])) / 2} y={py(values[1]) + 26} textAnchor="middle">u = {fmt(values[1], 2)}（両方の点）</text>
        {free
          ? <>
            <text className="ex-label ex-label-strong" x={(left + right) / 2} y={height - 30} textAnchor="middle">橙の矢印＝いまの熱源 q = {fmt(q, 2)}</text>
            <text className="ex-label ex-label-strong" x={(left + right) / 2} y={height - 8} textAnchor="middle">点線の矢印＝u に必要な Ku = {fmt(shown.required, 2)}</text>
          </>
          : <>
            <text className="ex-label ex-label-strong" x={(left + right) / 2} y={height - 30} textAnchor="middle">↑ Ku = q を解いて u を決める</text>
            <text className="ex-label ex-label-strong" x={(left + right) / 2} y={height - 8} textAnchor="middle">熱源 q = {fmt(q, 2)}（両方の点）</text>
          </>}
      </svg>
    </div>
    <p className="ex-hint">
      {free
        ? "緑の縦線が目標との差です。実線と点線の矢印の長さの違いが、状態方程式の破れです。"
        : "緑の縦線が、目標との差（温度のずれ）です。下の矢印が熱源で、強いほど長くなります。熱源から温度へ伸びる点線が、Ku = q を解く向きです。"}
    </p>
  </figure>;
}

function BreakdownPanel({ misfit, penalty, residual, free }: { misfit: number; penalty: number; residual: number; free: boolean }) {
  const { ref, viewport } = useStageViewport(BOUNDS, 0.4);
  const width = viewport.width, height = 168;
  const left = 14, right = width - 14, top = 30;
  const px = (v: number) => left + (v / J_MAX) * (right - left);
  const rx = (v: number) => left + (Math.min(v, RESIDUAL_MAX) / RESIDUAL_MAX) * (right - left);
  return <figure className="ex-panel pde-panel">
    <figcaption className="ex-panel-title">目的 J の内訳（二つを積んだ長さが J）と、状態方程式の残差</figcaption>
    <div className="ex-canvas" ref={ref}>
      <svg className="ex-svg" role="img" viewBox={`0 0 ${width} ${height}`}
        aria-label={`温度のずれの項${fmt(misfit, 3)}と熱源の罰則${fmt(penalty, 3)}を積んだ合計は${fmt(misfit + penalty, 3)}。状態残差は${fmt(residual, 3)}`}>
        <rect className="ex-ground" width={width} height={height} />
        <rect className="pde-bar-misfit" x={px(0)} y={top} width={Math.max(0, px(misfit) - px(0))} height={30} />
        <rect className="pde-bar-penalty" x={px(misfit)} y={top} width={Math.max(0, px(misfit + penalty) - px(misfit))} height={30} />
        <line className="pde-best" x1={px(0.5)} x2={px(0.5)} y1={top - 12} y2={top + 42} />
        <text className="ex-label ex-label-strong" x={px(0.5) + 6} y={top - 14}>最小 0.5</text>
        <text className="ex-label ex-label-strong" x={px(0)} y={top + 56}>ずれ {fmt(misfit, 3)}</text>
        <text className="ex-label ex-label-strong" x={right} y={top + 56} textAnchor="end">罰則 {fmt(penalty, 3)}　合計 {fmt(misfit + penalty, 3)}</text>
        <rect className="pde-bar-residual" x={rx(0)} y={top + 78} width={Math.max(0, rx(residual) - rx(0))} height={14} />
        <line className="pde-residual-zero" x1={rx(0)} x2={rx(0)} y1={top + 72} y2={top + 98} />
        <text className="ex-label ex-label-strong" x={px(0)} y={top + 116}>
          状態残差 {fmt(residual, 2)}{free ? (residual < 1e-9 ? "（満たす）" : "（満たさない）") : "（いつも 0）"}
        </text>
      </svg>
    </div>
  </figure>;
}

function CurvePanel({ q, total, free }: { q: number; total: number; free: boolean }) {
  const { ref, viewport } = useStageViewport(BOUNDS, 0.55);
  const width = viewport.width, height = 270;
  const left = 40, right = width - 14, top = 16, bottom = height - 36;
  const px = (v: number) => left + (v / Q_MAX) * (right - left);
  const py = (v: number) => bottom - (v / 2) * (bottom - top);
  const samples = Array.from({ length: 97 }, (_, i) => balanceAt((Q_MAX * i) / 96));
  const path = (pick: (b: ReturnType<typeof balanceAt>) => number) =>
    samples.map((b, i) => `${i ? "L" : "M"}${px(b.q).toFixed(1)} ${py(pick(b)).toFixed(1)}`).join("");
  return <figure className="ex-panel pde-panel">
    <figcaption className="ex-panel-title">J(q) の曲線：ずれの項と罰則の交点が最小</figcaption>
    <div className="ex-canvas" ref={ref}>
      <svg className="ex-svg" role="img" viewBox={`0 0 ${width} ${height}`}
        aria-label={`熱源${fmt(q, 2)}での合計は${fmt(total, 3)}。曲線はq=4.5で最小の0.5`}>
        <rect className="ex-ground" width={width} height={height} />
        <g className="ex-axes">
          <line x1={left} x2={right} y1={bottom} y2={bottom} />
          {[0, 3, 6, 9, 12].map((v) => <g key={v}>
            <line x1={px(v)} x2={px(v)} y1={bottom} y2={bottom + 5} />
            <text x={px(v)} y={bottom + 22} textAnchor="middle">{v}</text>
          </g>)}
          {[0, 0.5, 1, 1.5, 2].map((v) => <text key={v} x={left - 6} y={py(v) + 4} textAnchor="end">{v}</text>)}
        </g>
        <text className="ex-axis-name" x={right} y={bottom - 8} textAnchor="end">q</text>
        <line className="pde-best" x1={px(BEST_Q)} x2={px(BEST_Q)} y1={top} y2={bottom} />
        <path className="pde-curve-misfit" d={path((b) => b.misfit)} />
        <path className="pde-curve-penalty" d={path((b) => b.penalty)} />
        <path className="ex-curve" d={path((b) => b.total)} />
        <text className="ex-label pde-label-misfit" x={px(0.3)} y={py(0.78)}>ずれ</text>
        <text className="ex-label pde-label-penalty" x={px(11.7)} y={py(1.45)} textAnchor="end">罰則</text>
        <text className="ex-label ex-label-strong" x={px(BEST_Q) + 6} y={py(0.08)}>q = 4.5</text>
        <g className={free ? "pde-marker pde-marker-free" : "pde-marker"} style={{ transform: `translate(${px(q)}px, ${py(Math.min(total, 2))}px)` }}>
          <circle className="ex-head" r={8} />
        </g>
      </svg>
    </div>
    <p className="ex-hint">
      {free
        ? "太い黒線は、状態方程式を守る本当の J(q) です。マーカーは手で決めた u での合計を指し、黒線より下に出ることがあります。黒線の下は実現できない値です。"
        : "太い黒線が合計 J、緑がずれ、橙が罰則です。マーカーは、いまの q での J を指します。"}
    </p>
  </figure>;
}
