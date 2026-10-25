import { PlayerBar, Slider } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import { fmt } from "./format";
import { balanceAt, BEST_Q, H, TARGET } from "./math/pdeHeat";
import { useStageViewport } from "./svg";
import { useManualOrPlayback } from "./useManualOrPlayback";
import { useTimeline } from "./useTimeline";

const Q_MAX = 12, SWEEP_STEPS = 48;
const BOUNDS = { xMin: 0, xMax: 1, yMin: 0, yMax: 1 };
const J_MAX = 1.95;

export default function PdeHeatSourceBalance() {
  const timeline = useTimeline(SWEEP_STEPS, 10);
  const { value: q, set: setQ } = useManualOrPlayback(timeline, BEST_Q, (p) => p * 0.25, false);
  const now = balanceAt(q);
  const atBest = Math.abs(q - BEST_Q) < 1e-9;
  const verdict = atBest
    ? "温度のずれ 0.250 と熱源の罰則 0.250 がちょうど釣り合い、合計 0.500 は最小です。"
    : now.misfit > now.penalty
      ? `温度のずれ ${fmt(now.misfit, 3)} が罰則 ${fmt(now.penalty, 3)} より大きく、熱源を強くすると合計は下がります。`
      : `熱源の罰則 ${fmt(now.penalty, 3)} がずれ ${fmt(now.misfit, 3)} より大きく、熱源を弱くすると合計は下がります。`;

  return <ExplorableFrame
    id="pde-heat-source-balance"
    controls={<Slider label="熱源の強さ q（両方の点で同じ）" display={fmt(q, 2)} min={0} max={Q_MAX} step={0.25} value={q} onChange={setQ}
      hint="記事の表は q = 0、4.5、9 です。" />}
    stage={<>
      <RodPanel q={q} />
      <BreakdownPanel misfit={now.misfit} penalty={now.penalty} />
      <CurvePanel q={q} />
    </>}
    player={<PlayerBar timeline={timeline} stepLabel="q の掃引" positionText={`q = ${fmt(q, 2)}`} />}
    readout={<>
      <p className="ex-verdict">{verdict}</p>
      <div className="rb-scroll"><table className="ex-table">
        <thead><tr><th scope="col">熱源 q</th><th scope="col">状態 u</th><th scope="col">温度のずれの項</th><th scope="col">熱源の罰則</th><th scope="col">合計 J</th></tr></thead>
        <tbody>
          <tr className={atBest ? "ex-row-best" : undefined}>
            <td>({fmt(q, 2)}, {fmt(q, 2)})</td>
            <td>({fmt(now.u[0], 3)}, {fmt(now.u[1], 3)})</td>
            <td>{fmt(now.misfit, 3)}</td><td>{fmt(now.penalty, 3)}</td><td>{fmt(now.total, 3)}</td>
          </tr>
        </tbody>
      </table></div>
      <p className="ex-hint">温度の目標は 1 です。u = K⁻¹q は、q が決まると自動で決まる状態で、q を動かすたびに状態方程式 Ku = q を解き直しています。</p>
    </>}
    summary={`熱源の強さqを${fmt(q, 2)}にすると、内部2点の温度は${fmt(now.u[0], 3)}になります。温度のずれの項は${fmt(now.misfit, 3)}、熱源の罰則は${fmt(now.penalty, 3)}、合計は${fmt(now.total, 3)}です。qが4.5のとき二つの項が0.25で等しく、合計0.5が最小です。`}
  />;
}

function RodPanel({ q }: { q: number }) {
  const { ref, viewport } = useStageViewport(BOUNDS, 0.5);
  const width = viewport.width, height = 270;
  const left = 36, right = width - 20, top = 20, base = 188;
  const uMax = 1.5;
  const px = (s: number) => left + s * (right - left);
  const py = (u: number) => base - (u / uMax) * (base - top);
  const nodes = [0, H, 2 * H, 1];
  const b = balanceAt(q);
  const values = [0, b.u[0], b.u[1], 0];
  const profile = nodes.map((s, i) => `${i ? "L" : "M"}${px(s).toFixed(1)} ${py(values[i]).toFixed(1)}`).join("");
  const arrowLen = (q / Q_MAX) * 54;
  return <figure className="ex-panel pde-panel">
    <figcaption className="ex-panel-title">棒の温度 u（両端は 0 に固定）</figcaption>
    <div className="ex-canvas" ref={ref}>
      <svg className="ex-svg" role="img" viewBox={`0 0 ${width} ${height}`}
        aria-label={`熱源${fmt(q, 2)}のとき、内部2点の温度は${fmt(b.u[0], 3)}で、目標1との差は${fmt(TARGET - b.u[0], 3)}です`}>
        <rect className="ex-ground" width={width} height={height} />
        <g className="ex-axes">
          <line x1={left} x2={right} y1={base} y2={base} />
          {[0, 0.5, 1].map((u) => <text key={u} x={left - 6} y={py(u) + 4} textAnchor="end">{u}</text>)}
        </g>
        <line className="pde-target" x1={left} x2={right} y1={py(TARGET)} y2={py(TARGET)} />
        <text className="ex-label ex-label-strong" x={right} y={py(TARGET) - 8} textAnchor="end">目標温度 1</text>
        {[1, 2].map((i) => <line key={i} className="pde-gap" x1={px(nodes[i])} x2={px(nodes[i])} y1={py(values[i])} y2={py(TARGET)} />)}
        <path className="ex-curve" d={profile} />
        {[1, 2].map((i) => <circle key={i} className="ex-head" cx={px(nodes[i])} cy={py(values[i])} r={7} />)}
        {[0, 3].map((i) => <rect key={i} className="pde-wall" x={px(nodes[i]) - 5} y={py(0) - 18} width={10} height={18} />)}
        {[1, 2].map((i) => <g key={i}>
          <line className="pde-heater" x1={px(nodes[i])} x2={px(nodes[i])} y1={base + 12 + arrowLen} y2={base + 12} />
          {arrowLen > 3 && <path className="pde-heater-head" d={`M${px(nodes[i]) - 6} ${base + 18}L${px(nodes[i])} ${base + 8}L${px(nodes[i]) + 6} ${base + 18}Z`} />}
        </g>)}
        <text className="ex-label ex-label-strong" x={(px(H) + px(2 * H)) / 2} y={height - 8} textAnchor="middle">熱源 q = {fmt(q, 2)}（両方の点）</text>
        {[1, 2].map((i) => <text key={i} className="ex-label" x={px(nodes[i])} y={py(values[i]) + 26} textAnchor="middle">u = {fmt(values[i], 2)}</text>)}
      </svg>
    </div>
    <p className="ex-hint">橙の縦線が、目標との差（温度のずれ）です。下の矢印が熱源で、強いほど長くなります。</p>
  </figure>;
}

function BreakdownPanel({ misfit, penalty }: { misfit: number; penalty: number }) {
  const { ref, viewport } = useStageViewport(BOUNDS, 0.3);
  const width = viewport.width, height = 112;
  const left = 14, right = width - 14, top = 30;
  const px = (v: number) => left + (v / J_MAX) * (right - left);
  return <figure className="ex-panel pde-panel">
    <figcaption className="ex-panel-title">目的 J の内訳（二つを積んだ長さが J）</figcaption>
    <div className="ex-canvas" ref={ref}>
      <svg className="ex-svg" role="img" viewBox={`0 0 ${width} ${height}`}
        aria-label={`温度のずれの項${fmt(misfit, 3)}と熱源の罰則${fmt(penalty, 3)}を積んだ合計は${fmt(misfit + penalty, 3)}`}>
        <rect className="ex-ground" width={width} height={height} />
        <rect className="pde-bar-misfit" x={px(0)} y={top} width={Math.max(0, px(misfit) - px(0))} height={30} />
        <rect className="pde-bar-penalty" x={px(misfit)} y={top} width={Math.max(0, px(misfit + penalty) - px(misfit))} height={30} />
        <line className="pde-best" x1={px(0.5)} x2={px(0.5)} y1={top - 12} y2={top + 42} />
        <text className="ex-label ex-label-strong" x={px(0.5) + 6} y={top - 14}>最小 0.5</text>
        <text className="ex-label ex-label-strong" x={px(0)} y={top + 56}>ずれ {fmt(misfit, 3)}</text>
        <text className="ex-label ex-label-strong" x={right} y={top + 56} textAnchor="end">罰則 {fmt(penalty, 3)}　合計 {fmt(misfit + penalty, 3)}</text>
      </svg>
    </div>
  </figure>;
}

function CurvePanel({ q }: { q: number }) {
  const { ref, viewport } = useStageViewport(BOUNDS, 0.55);
  const width = viewport.width, height = 270;
  const left = 40, right = width - 14, top = 16, bottom = height - 36;
  const px = (v: number) => left + (v / Q_MAX) * (right - left);
  const py = (v: number) => bottom - (v / 2) * (bottom - top);
  const samples = Array.from({ length: 97 }, (_, i) => balanceAt((Q_MAX * i) / 96));
  const path = (pick: (b: ReturnType<typeof balanceAt>) => number) =>
    samples.map((b, i) => `${i ? "L" : "M"}${px(b.q).toFixed(1)} ${py(pick(b)).toFixed(1)}`).join("");
  const now = balanceAt(q);
  return <figure className="ex-panel pde-panel">
    <figcaption className="ex-panel-title">J(q) の曲線：ずれの項と罰則の交点が最小</figcaption>
    <div className="ex-canvas" ref={ref}>
      <svg className="ex-svg" role="img" viewBox={`0 0 ${width} ${height}`}
        aria-label={`熱源${fmt(q, 2)}での合計は${fmt(now.total, 3)}。曲線はq=4.5で最小の0.5`}>
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
        <g className="pde-marker" style={{ transform: `translate(${px(q)}px, ${py(now.total)}px)` }}>
          <circle className="ex-head" r={8} />
        </g>
      </svg>
    </div>
    <p className="ex-hint">太い黒線が合計 J、緑がずれ、橙が罰則です。マーカーは、いまの q での J を指します。</p>
  </figure>;
}
