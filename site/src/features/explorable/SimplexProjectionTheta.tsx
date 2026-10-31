import { useId, useMemo, useState } from "react";

import { Choice, PlayerBar, Slider } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import { fmt } from "./format";
import {
  bisectTheta, clippedSum, clippedValues, distance3, divideBySum, halfSquaredDistance, planeShadow, projectionTheta,
  PROJECTED, shadowXY, thetaPath, triangleXY, TRIANGLE_VERTICES, WISH,
} from "./math/simplexProjection";
import { smooth } from "./math/rootFinding";
import { useStageViewport } from "./svg";
import { useManualOrPlayback } from "./useManualOrPlayback";
import { useTimeline } from "./useTimeline";

const NAMES = ["調査", "制作", "確認"] as const;
const SEARCH_STEPS = 14;
const BOUNDS = { xMin: 0, xMax: 1, yMin: 0, yMax: 1 };
const THETA_MAX = Math.max(...WISH);
const SUM_MAX = 1.3;
const ON_SIMPLEX = 5e-4;

type Compare = "none" | "divide";
type View = "zoom" | "whole";

export default function SimplexProjectionTheta() {
  const [compare, setCompare] = useState<Compare>("none");
  const [view, setView] = useState<View>("zoom");
  const probes = useMemo(() => bisectTheta(WISH, SEARCH_STEPS), []);
  const path = useMemo(() => thetaPath(WISH, SEARCH_STEPS), []);
  const timeline = useTimeline(SEARCH_STEPS, 2);
  const valueAt = (position: number) => {
    const i = Math.min(Math.floor(position + 1e-9), SEARCH_STEPS - 1);
    const f = Math.min(1, position - i);
    return path[i] + (path[i + 1] - path[i]) * smooth(f);
  };
  const { value: theta, set: setTheta, playback } = useManualOrPlayback(timeline, 0.1, valueAt, true);

  const x = clippedValues(WISH, theta);
  const total = clippedSum(WISH, theta);
  const onSimplex = Math.abs(total - 1) < ON_SIMPLEX;
  const ghost = divideBySum(WISH);
  const exact = projectionTheta(WISH);
  const probeIndex = Math.min(Math.floor(timeline.position + 1e-9), SEARCH_STEPS - 1);
  const bracket = playback ? probes[probeIndex] : undefined;

  const verdict = onSimplex
    ? `合計が 1 に戻りました。x = (${x.map((v) => fmt(v, 3)).join(", ")}) が、希望量 y を単体へ射影した点です。`
    : total > 1
      ? `合計は ${fmt(total, 3)} で、1 より ${fmt(total - 1, 3)} 多いままです。もっと引きます。`
      : `合計は ${fmt(total, 3)} で、1 に ${fmt(1 - total, 3)} 足りません。引きすぎです。`;

  return <ExplorableFrame
    id="simplex-projection-theta"
    controls={<>
      <Slider label="引く量 θ" display={fmt(theta, 3)} min={0} max={THETA_MAX} step={0.005} value={theta} onChange={setTheta}
        hint="全員から同じ量を引きます。確認は θ=0.05 を超えると負になり、0 に切られます。" />
      <Choice<Compare> legend="重ねて比べる" value={compare} onChange={setCompare} options={[
        { value: "none", label: "なし" },
        { value: "divide", label: "合計で割った配分" },
      ]} />
      <Choice<View> legend="三角形の見え方" value={view} onChange={setView} options={[
        { value: "zoom", label: "辺のそばを拡大" },
        { value: "whole", label: "三角形全体" },
      ]} />
    </>}
    stage={<>
      <BarsPanel theta={theta} onSimplex={onSimplex} ghost={compare === "divide" ? ghost : undefined} />
      <SumPanel theta={theta} total={total} exact={exact} bracket={bracket ? [bracket.lo, bracket.hi] : undefined} />
      <TrianglePanel theta={theta} onSimplex={onSimplex} showDivide={compare === "divide"} zoom={view === "zoom"} />
    </>}
    player={<PlayerBar showButtonNames timeline={timeline} stepLabel="二分" positionText={`${timeline.step} / ${SEARCH_STEPS} 回`} />}
    readout={<>
      <p className="ex-verdict">{verdict}</p>
      <div className="rb-scroll"><table className="ex-table">
        <thead><tr><th scope="col">配分</th>{NAMES.map((n) => <th key={n} scope="col">{n}</th>)}<th scope="col">合計</th><th scope="col">目的値 ½‖x−y‖²</th></tr></thead>
        <tbody>
          <tr><th scope="row">希望量 y</th>{WISH.map((v, i) => <td key={i}>{fmt(v, 3)}</td>)}<td>{fmt(WISH.reduce((a, b) => a + b, 0), 3)}</td><td>—</td></tr>
          <tr className={onSimplex ? "ex-row-best" : undefined}>
            <th scope="row">θ={fmt(theta, 3)} で引いて0に切る</th>{x.map((v, i) => <td key={i}>{fmt(v, 3)}</td>)}
            <td>{fmt(total, 3)}</td><td>{onSimplex ? fmt(halfSquaredDistance(x, WISH), 5) : "合計が1でないので比べません"}</td>
          </tr>
          <tr>
            <th scope="row">合計で割る</th>{ghost.map((v, i) => <td key={i}>{fmt(v, 3)}</td>)}
            <td>{fmt(ghost.reduce((a, b) => a + b, 0), 3)}</td><td>{fmt(halfSquaredDistance(ghost, WISH), 5)}</td>
          </tr>
        </tbody>
      </table></div>
    </>}
    summary={`希望量は ${WISH.join("、")}。共通の量θを${fmt(theta, 3)}引いて負を0に切ると、配分は${x.map((v) => fmt(v, 3)).join("、")}で合計${fmt(total, 3)}です。θが${fmt(exact, 3)}のとき合計が1になり、目的値は0.01125です。合計で割る配分は0.72、0.24、0.04で目的値は0.01805です。`}
  />;
}

function BarsPanel({ theta, onSimplex, ghost }: { theta: number; onSimplex: boolean; ghost: number[] | undefined }) {
  const { ref, viewport } = useStageViewport(BOUNDS, 0.5);
  const width = viewport.width, height = 290;
  const left = 44, right = width - 12, top = 22, bottom = height - 34;
  const yMin = -0.2, yMax = 1.0;
  const py = (v: number) => bottom - ((v - yMin) / (yMax - yMin)) * (bottom - top);
  const slot = (right - left) / 3;
  const barW = Math.min(64, slot * 0.46);
  return <figure className="ex-panel sp-panel">
    <figcaption className="ex-panel-title">希望量から θ を引いて、負を 0 に切る</figcaption>
    <div className="ex-canvas" ref={ref}>
      <svg className="ex-svg" role="img" viewBox={`0 0 ${width} ${height}`}
        aria-label={`三つの活動の希望量から共通の量${fmt(theta, 3)}を引き、負になった棒を0に切った様子`}>
        <rect className="ex-ground" width={width} height={height} />
        <g className="ex-axes">
          {[0, 0.5, 1].map((v) => <g key={v}>
            <line x1={left} x2={right} y1={py(v)} y2={py(v)} className={v === 0 ? "sp-zero" : "nr-grid"} />
            <text x={left - 6} y={py(v) + 4} textAnchor="end">{v}</text>
          </g>)}
          <line x1={left} x2={right} y1={py(-0.2)} y2={py(-0.2)} className="nr-grid" />
          <text x={left - 6} y={py(-0.2) + 4} textAnchor="end">−0.2</text>
        </g>
        {WISH.map((y, i) => {
          const cx = left + slot * (i + 0.5);
          const kept = Math.max(y - theta, 0);
          const clipped = y - theta < 0;
          const negative = Math.min(y - theta, 0);
          return <g key={i}>
            <rect className="sp-wish" x={cx - barW / 2} y={py(y)} width={barW} height={py(0) - py(y)} />
            {/* the part taken away, always from the top of the wish */}
            <rect className="sp-taken" x={cx - barW / 2} y={py(y)} width={barW} height={py(y - Math.min(theta, y)) - py(y)} />
            <rect className={clipped ? "sp-kept sp-kept-zero" : "sp-kept"} x={cx - barW / 2} y={py(kept)} width={barW} height={Math.max(0, py(0) - py(kept))} />
            {clipped && <rect className="sp-negative" x={cx - barW / 2} y={py(0)} width={barW} height={py(negative) - py(0)} />}
            {ghost && <g className="sp-ghost">
              <line x1={cx - barW / 2 - 8} x2={cx + barW / 2 + 8} y1={py(ghost[i])} y2={py(ghost[i])} />
              <text x={cx + barW / 2 + 10} y={py(ghost[i]) + 4}>{fmt(ghost[i], 2)}</text>
            </g>}
            <text className="ex-label ex-label-strong" x={cx} y={bottom + 24} textAnchor="middle">{NAMES[i]}</text>
            <text className="ex-label ex-label-strong" x={cx} y={py(Math.max(y, kept)) - 8} textAnchor="middle">
              {clipped ? `${fmt(y - theta, 2)} → 0` : fmt(kept, 3)}
            </text>
          </g>;
        })}
      </svg>
    </div>
    <p className="ex-hint">
      薄い橙が引いた量、緑が残った配分です。負になった棒は灰色の枠で下へはみ出し、0 に切ります。
      {ghost ? "黒い短い線が、合計で割った配分です。" : ""}
      {onSimplex ? "いま合計は 1 です。" : ""}
    </p>
  </figure>;
}

/** The three-activity simplex as a triangle: y's shadow, the θ path, the projected point and the divided point. */
function TrianglePanel({ theta, onSimplex, showDivide, zoom }: { theta: number; onSimplex: boolean; showDivide: boolean; zoom: boolean }) {
  const { ref, viewport } = useStageViewport(BOUNDS, 0.5);
  const clipId = useId();
  const width = viewport.width, height = 330;
  const whole = Math.min(width - 48, (height - 64) / (Math.sqrt(3) / 2));
  const scale = zoom ? 2000 : whole;
  const px = (x: number) => (zoom ? width / 2 + (x - 0.23) * scale : (width - scale) / 2 + x * scale);
  const py = (y: number) => (zoom ? 235 - y * scale : height - 32 - y * scale);
  const pt = (xy: readonly [number, number]) => [px(xy[0]), py(xy[1])] as const;
  const verts = TRIANGLE_VERTICES.map(pt);
  const outline = `M${verts.map(([a, b]) => `${a.toFixed(1)} ${b.toFixed(1)}`).join("L")}Z`;
  const knots = [0, 0.05, 0.3, THETA_MAX].map((t) => pt(shadowXY(clippedValues(WISH, t))));
  const trail = `M${knots.map(([a, b]) => `${a.toFixed(1)} ${b.toFixed(1)}`).join("L")}`;
  const shadowY = pt(shadowXY(WISH));
  const proj = pt(triangleXY(PROJECTED));
  const divided = divideBySum(WISH);
  const div = pt(triangleXY(divided));
  const now = pt(shadowXY(clippedValues(WISH, theta)));
  const toProjected = distance3(planeShadow(WISH), PROJECTED);
  const toDivided = distance3(planeShadow(WISH), divided);
  const place = (x: number, text: string, gap = 12) => (x + gap + text.length * 14 > width - 4
    ? { x: x - gap, anchor: "end" as const }
    : { x: x + gap, anchor: "start" as const });
  const mapW = 96, mapX = width - mapW - 26, mapY = 28;
  const mapH = mapW * (Math.sqrt(3) / 2);
  const mp = (xy: readonly [number, number]) => [mapX + xy[0] * mapW, mapY + mapH - xy[1] * mapW] as const;
  const mapOutline = `M${TRIANGLE_VERTICES.map((v) => mp(v).map((n) => n.toFixed(1)).join(" ")).join("L")}Z`;
  const labelProj = place(proj[0], "射影 x");
  const labelShadow = place(shadowY[0], "y の影");
  const labelDiv = place(div[0], "割った配分");
  return <figure className="ex-panel sp-panel">
    <figcaption className="ex-panel-title">三角形（合計 1 の領域）の上の動き</figcaption>
    <div className="ex-canvas" ref={ref}>
      <svg className="ex-svg" role="img" viewBox={`0 0 ${width} ${height}`}
        aria-label={`三つの活動の配分を表す三角形。希望量の影、θを${fmt(theta, 3)}にしたときの印、辺の上の射影、合計で割った配分の位置を示す`}>
        <defs><clipPath id={clipId}><rect width={width} height={height} /></clipPath></defs>
        <rect className="ex-ground" width={width} height={height} />
        <g clipPath={`url(#${clipId})`}>
          <path className="sp-tri" d={outline} />
          <line className="sp-tri-floor" x1={verts[0][0]} y1={verts[0][1]} x2={verts[1][0]} y2={verts[1][1]} />
          <path className="sp-trail" d={trail} />
          <line className="sp-perp" x1={shadowY[0]} y1={shadowY[1]} x2={proj[0]} y2={proj[1]} />
          <path className="sp-right-angle" d={`M${proj[0] + 10} ${proj[1]}L${proj[0] + 10} ${proj[1] + 10}L${proj[0]} ${proj[1] + 10}`} />
          {showDivide && <line className="sp-divide-line" x1={shadowY[0]} y1={shadowY[1]} x2={div[0]} y2={div[1]} />}
          <circle className="sp-shadow-y" cx={shadowY[0]} cy={shadowY[1]} r={7} />
          <rect className="sp-proj" x={proj[0] - 7} y={proj[1] - 7} width={14} height={14} />
          {showDivide && <path className="sp-divided" d={`M${div[0]} ${div[1] - 9}L${div[0] + 9} ${div[1]}L${div[0]} ${div[1] + 9}L${div[0] - 9} ${div[1]}Z`} />}
          <circle className={onSimplex ? "sp-marker sp-marker-ok" : "sp-marker"} cx={now[0]} cy={now[1]} r={6} />
          <text className="ex-label ex-label-strong" x={labelProj.x} y={proj[1] - 12} textAnchor={labelProj.anchor}>射影 x</text>
          <text className="ex-label ex-label-strong" x={labelShadow.x} y={shadowY[1] + 5} textAnchor={labelShadow.anchor}>y の影</text>
          {showDivide && <text className="ex-label ex-label-strong" x={labelDiv.x} y={div[1] - 12} textAnchor={labelDiv.anchor}>割った配分</text>}
          {zoom && <text className="ex-label" x={width - 8} y={py(0) + 22} textAnchor="end">確認 = 0 の辺</text>}
          {!zoom && ["調査", "制作", "確認"].map((name, i) => <text key={name} className="ex-label ex-label-strong"
            x={verts[i][0]} y={i === 2 ? verts[i][1] - 10 : verts[i][1] + 24} textAnchor={i === 0 ? "start" : i === 1 ? "end" : "middle"}>{name}</text>)}
          {zoom && <g>
            <path className="sp-tri" d={mapOutline} />
            {["調", "制", "確"].map((name, i) => {
              const [mx, my] = mp(TRIANGLE_VERTICES[i]);
              return <text key={name} className="ex-label" x={mx + (i === 0 ? -4 : i === 1 ? 4 : 0)} y={my + (i === 2 ? -4 : 15)}
                textAnchor={i === 0 ? "end" : i === 1 ? "start" : "middle"}>{name}</text>;
            })}
            <circle className="sp-map-dot" cx={mp([0.2, 0])[0]} cy={mp([0.2, 0])[1]} r={5} />
          </g>}
        </g>
      </svg>
    </div>
    <p className="ex-hint">
      三角形は、合計が 1 の配分の集まりです。y は合計が 1.25 で三角形の面の外にあるため、面へ垂直に落とした「影」を白い丸で描きます。
      影から辺{zoom ? "（確認 = 0）" : ""}へ直角におりた先の緑の四角が射影 x で、橙の印は、いまの θ で引いて切った配分の影です。
      影から射影までの距離は {fmt(toProjected, 3)}{showDivide ? `、合計で割った配分までは ${fmt(toDivided, 3)} で、その道は辺に直角ではありません。` : "です。"}
      {zoom ? " 小さな三角形の黒い点が、拡大している場所です。" : ""}
    </p>
  </figure>;
}

function SumPanel({ theta, total, exact, bracket }: { theta: number; total: number; exact: number; bracket: [number, number] | undefined }) {
  const { ref, viewport } = useStageViewport(BOUNDS, 0.5);
  const width = viewport.width, height = 260;
  const left = 44, right = width - 14, top = 54, bottom = height - 34;
  const px = (t: number) => left + (t / THETA_MAX) * (right - left);
  const py = (s: number) => bottom - (s / SUM_MAX) * (bottom - top);
  const knots = [0, 0.05, 0.3, THETA_MAX];
  const curve = knots.map((t, i) => `${i ? "L" : "M"}${px(t).toFixed(1)} ${py(clippedSum(WISH, t)).toFixed(1)}`).join("");
  const meterL = left, meterR = right;
  const meter = (s: number) => meterL + (Math.min(s, SUM_MAX) / SUM_MAX) * (meterR - meterL);
  const ok = Math.abs(total - 1) < ON_SIMPLEX;
  return <figure className="ex-panel sp-panel">
    <figcaption className="ex-panel-title">合計メーターと、θ に対する合計</figcaption>
    <div className="ex-canvas" ref={ref}>
      <svg className="ex-svg" role="img" viewBox={`0 0 ${width} ${height}`}
        aria-label={`θが${fmt(theta, 3)}のとき、残った配分の合計は${fmt(total, 3)}です`}>
        <rect className="ex-ground" width={width} height={height} />
        <rect className="sp-meter-track" x={meterL} y={14} width={meterR - meterL} height={20} rx={3} />
        <rect className={ok ? "sp-meter-fill sp-meter-ok" : "sp-meter-fill"} x={meterL} y={14} width={meter(total) - meterL} height={20} rx={3} />
        <line className="sp-target" x1={meter(1)} x2={meter(1)} y1={8} y2={40} />
        <text className="ex-label ex-label-strong" x={meter(1)} y={50} textAnchor="middle">合計 1</text>
        <text className="ex-label ex-label-strong" x={meterR - 4} y={30} textAnchor="end">{fmt(total, 3)}</text>
        <g className="ex-axes">
          <line x1={left} x2={right} y1={bottom} y2={bottom} />
          {[0, 0.3, 0.6, 0.9].map((t) => <g key={t}>
            <line x1={px(t)} x2={px(t)} y1={bottom} y2={bottom + 5} />
            <text x={px(t)} y={bottom + 22} textAnchor="middle">{t}</text>
          </g>)}
          {[0, 1].map((s) => <text key={s} x={left - 6} y={py(s) + 4} textAnchor="end">{s}</text>)}
        </g>
        <text className="ex-axis-name" x={right} y={bottom - 8} textAnchor="end">θ</text>
        {bracket && <rect className="sp-bracket" x={px(bracket[0])} y={top} width={px(bracket[1]) - px(bracket[0])} height={bottom - top} />}
        <line className="sp-target" x1={left} x2={right} y1={py(1)} y2={py(1)} />
        <path className="ex-curve" d={curve} />
        <line className="nr-root" x1={px(exact)} x2={px(exact)} y1={py(1)} y2={bottom} />
        <circle className={ok ? "sp-marker sp-marker-ok" : "sp-marker"} cx={px(theta)} cy={py(total)} r={7} />
      </svg>
    </div>
    <p className="ex-hint">曲線は、引く量 θ に対して残る合計です。1 の水平線と交わる θ = {fmt(exact, 3)} が答えです。再生では、橙の帯の中点を見て帯を半分にします。</p>
  </figure>;
}
