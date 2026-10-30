import { useId, useState } from "react";

import { Choice, Slider } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import { fmt } from "./format";
import { frac, LiveMath, mi, mn, mo, paren, row, sub, sup } from "./mathml";
import {
  BEST_X, betaFraction, equilibrium, equilibriumG, gAlpha, gBeta, LOWEST_G_X, objectiveJ, objectiveSlope,
  TARGET, X_ALPHA, X_BETA, type Candidate,
} from "./math/phaseFraction";
import { useStageViewport } from "./svg";

const ID = "phase-fraction-target";
const BOUNDS = { xMin: 0, xMax: 1, yMin: 0, yMax: 1 };
const SAMPLES = Array.from({ length: 201 }, (_, i) => i / 200);
/** Values that should read as exactly 0 (x = 0.35 gives 5e-33 in floating point). */
const clean = (v: number) => (Math.abs(v) < 1e-12 ? 0 : v);

type Goal = "J" | "G";
const GOAL_OPTIONS: ReadonlyArray<{ value: Goal; label: string }> = [
  { value: "J", label: "J：βの量を 0.30 に合わせる" },
  { value: "G", label: "G：ギブスエネルギーをそのまま最小にする" },
];

const REGIONS: ReadonlyArray<{ from: number; to: number; label: string }> = [
  { from: 0, to: X_ALPHA, label: "αだけ" },
  { from: X_ALPHA, to: X_BETA, label: "α+β" },
  { from: X_BETA, to: 1, label: "βだけ" },
];

export default function PhaseFractionTarget() {
  const [x, setX] = useState(0.5);
  const [goal, setGoal] = useState<Goal>("J");
  const eq = equilibrium(x);
  const f = clean(eq.chosen.fBeta);
  const j = clean(objectiveJ(x));
  const g = eq.chosen.g;
  const slopeJ = clean(objectiveSlope(x));
  const [alpha, beta, both] = eq.candidates;

  const verdict = goal === "G"
    ? `外側でも G を最小にすると、x = ${fmt(LOWEST_G_X, 2)}（αだけ、G = 0）が最小です。そこでは β の量は 0 で、目標の 0.30 とは関係がありません。いまの x = ${fmt(x, 2)} の G は ${fmt(g, 4)} です。`
    : eq.chosen.phases === "α"
      ? `αだけの ${fmt(alpha.g, 4)} が最も低く、ツールは β の量 0 を返します。x を少し動かしても 0 のままなので、J は 0.090 で平らで、傾きは 0 です。`
      : eq.chosen.phases === "β"
        ? `βだけの ${fmt(beta.g, 4)} が最も低く、β の量は 1 です。J は 0.490 で平らで、傾きは 0 です。`
        : `2相に分かれた ${fmt(both.g, 4)} が、αだけ ${fmt(alpha.g, 4)} と βだけ ${fmt(beta.g, 4)} より低くなります。β の量は ${fmt(f, 2)}、J は ${fmt(j, 3)} です。${j === 0 ? "目標の 0.30 にちょうど合っています。" : `J の傾きは ${fmt(slopeJ, 2)} です。`}`;

  const summary = `Bの分率 x は${fmt(x, 2)}です。ツールは${eq.chosen.phases}を返し、βの量は${fmt(f, 2)}、ギブスエネルギーは${fmt(g, 4)}です。${goal === "J" ? `目的 J は${fmt(j, 3)}で、x=0.35 のとき0が最小です。` : "外側で G を最小にすると x=0.10 に向かい、βの量は0になります。"}`;

  return (
    <ExplorableFrame
      controls={<>
        <Slider
          display={fmt(x, 2)}
          hint="記事の表は x = 0.10、0.35、0.50、0.80 です。"
          label="Bの分率 x"
          max={1}
          min={0}
          onChange={setX}
          step={0.01}
          value={x}
        />
        <Choice<Goal> legend="外側の目的" onChange={setGoal} options={GOAL_OPTIONS} value={goal} />
      </>}
      id={ID}
      readout={<>
        <p className="ex-verdict">{verdict}</p>
        <section aria-label="βの量と目的の式" className="ex-equation">
          <FractionMath f={f} j={j} phases={eq.chosen.phases} x={x} />
        </section>
        <div className="rb-scroll"><table className="ex-table">
          <thead><tr>
            <th scope="col">x</th><th scope="col">αだけ</th><th scope="col">βだけ</th><th scope="col">α+β</th>
            <th scope="col">返る相</th><th scope="col">βの量</th><th scope="col">{goal === "J" ? "J" : "G"}</th>
          </tr></thead>
          <tbody><tr className={goal === "J" && j === 0 ? "ex-row-best" : undefined}>
            <td>{fmt(x, 2)}</td><td>{fmt(alpha.g, 4)}</td><td>{fmt(beta.g, 4)}</td>
            <td>{both ? fmt(both.g, 4) : "—"}</td>
            <td>{eq.chosen.phases}</td><td>{fmt(f, 2)}</td>
            <td>{goal === "J" ? fmt(j, 3) : fmt(g, 4)}</td>
          </tr></tbody>
        </table></div>
        <p className="ex-hint">
          ギブスエネルギーの3つの候補を比べて、最も低いものを返すのはツールの仕事です。外側で決めるのは x だけで、β の量は x の結果として決まります。
        </p>
      </>}
      stage={<>
        <InnerPanel candidates={eq.candidates} chosen={eq.chosen} x={x} />
        <div className="ex-twin">
          <BetaPanel f={f} x={x} />
          <GoalPanel goal={goal} x={x} />
        </div>
      </>}
      summary={summary}
    />
  );
}

function FractionMath({ x, f, j, phases }: { x: number; f: number; j: number; phases: Candidate["phases"] }) {
  const fBeta = sub(mi("f"), mi("β"));
  const fLine = phases === "α+β"
    ? row(fBeta, mo("="), frac(row(mn(fmt(x, 2)), mo("−"), mn("0.20")), row(mn("0.70"), mo("−"), mn("0.20"))), mo("="), mn(fmt(f, 2)))
    : row(fBeta, mo("="), mn(fmt(f, 0)));
  const jLine = row(mi("J"), mo("="), sup(paren(mn(fmt(f, 2)), mo("−"), mn("0.30")), mn("2")), mo("="), mn(fmt(j, 3)));
  return <>
    <LiveMath block label={phases === "α+β" ? `fβ = (${fmt(x, 2)} − 0.20) / (0.70 − 0.20) = ${fmt(f, 2)}` : `fβ = ${fmt(f, 0)}`} markup={fLine} />
    <LiveMath block label={`J = (${fmt(f, 2)} − 0.30)² = ${fmt(j, 3)}`} markup={jLine} />
  </>;
}

function axisTicks(values: readonly number[], px: (v: number) => number, y: number) {
  return values.map((v) => <text key={v} textAnchor="middle" x={px(v)} y={y}>{v}</text>);
}

function InnerPanel({ x, candidates, chosen }: { x: number; candidates: Candidate[]; chosen: Candidate }) {
  const clipId = useId();
  const { ref, viewport } = useStageViewport(BOUNDS, 0.42);
  const width = viewport.width, height = Math.max(340, viewport.height);
  const left = 44, right = width - 16, top = 16, bottom = height - 74;
  const yMin = -0.03, yMax = 0.3;
  const px = (v: number) => left + v * (right - left);
  const py = (v: number) => bottom - ((v - yMin) / (yMax - yMin)) * (bottom - top);
  const curve = (g: (v: number) => number) => SAMPLES.map((s, i) => `${i ? "L" : "M"}${px(s).toFixed(1)} ${py(g(s)).toFixed(1)}`).join("");
  const onRight = x > 0.55;
  const leverY = height - 26;
  const offChart = candidates.filter((c) => c.g > yMax);
  const shown = candidates.filter((c) => c.g <= yMax);
  const labelY = spreadLabels(shown.map((c) => py(c.g) + 5), 18);
  return (
    <figure className="ex-panel">
      <figcaption className="ex-panel-title">ツールの中：3つの候補のギブスエネルギー</figcaption>
      <div className="ex-canvas" ref={ref}>
        <svg
          aria-label={`x=${fmt(x, 2)}で、αだけ${fmt(candidates[0].g, 4)}、βだけ${fmt(candidates[1].g, 4)}${candidates[2] ? `、α+β ${fmt(candidates[2].g, 4)}` : ""}。最も低い${chosen.phases}をツールが返します`}
          className="ex-svg"
          role="img"
          viewBox={`0 0 ${width} ${height}`}
        >
          <defs><clipPath id={clipId}><rect height={bottom - top} width={right - left} x={left} y={top} /></clipPath></defs>
          <rect className="ex-ground" height={height} width={width} />
          <g className="ex-axes">
            <line x1={left} x2={right} y1={bottom} y2={bottom} />
            {[0, 0.1, 0.2, 0.3].map((v) => <text key={v} textAnchor="end" x={left - 6} y={py(v) + 4}>{v}</text>)}
            {axisTicks([0, 0.2, 0.5, 0.7, 1], px, bottom + 18)}
          </g>
          <g clipPath={`url(#${clipId})`}>
            <path className="pf-g-alpha" d={curve(gAlpha)} />
            <path className="pf-g-beta" d={curve(gBeta)} />
            <line className="pf-tangent" x1={px(X_ALPHA)} x2={px(X_BETA)} y1={py(gAlpha(X_ALPHA))} y2={py(gBeta(X_BETA))} />
          </g>
          <text className="ex-label ex-label-strong" x={px(0.62) + 8} y={py(gAlpha(0.62)) + 4}>α相</text>
          <text className="ex-label ex-label-strong" textAnchor="end" x={px(0.98)} y={py(0.27)}>β相</text>
          <text className="ex-label pf-tangent-label" textAnchor="middle" x={px(0.45)} y={py(0.06) + 22}>共通接線</text>
          <line className="pf-guide" x1={px(x)} x2={px(x)} y1={top} y2={bottom} />
          {shown.map((c, i) => (
            <g key={c.phases}>
              <circle className={c === chosen ? "ex-head" : "pf-candidate"} cx={px(x)} cy={py(c.g)} r={c === chosen ? 8 : 6} />
              <text className={c === chosen ? "ex-label ex-label-strong" : "ex-label"} textAnchor={onRight ? "end" : "start"}
                x={px(x) + (onRight ? -12 : 12)} y={labelY[i]}>
                {c.phases === "α+β" ? "α+β" : `${c.phases}だけ`} {fmt(c.g, 4)}
              </text>
            </g>
          ))}
          {offChart.length > 0 && (
            <text className="ex-label" textAnchor={onRight ? "end" : "start"} x={px(x) + (onRight ? -10 : 10)} y={top + 14}>
              ↑ {offChart.map((c) => `${c.phases}だけ ${fmt(c.g, 4)}`).join("、")}
            </text>
          )}
          <text className="ex-axis-name" textAnchor="end" x={right} y={bottom + 36}>Bの分率</text>
          <line className="pf-lever-base" x1={px(X_ALPHA)} x2={px(X_BETA)} y1={leverY} y2={leverY} />
          {chosen.phases === "α+β" && <>
            <line className="pf-lever-beta" x1={px(X_ALPHA)} x2={px(x)} y1={leverY} y2={leverY} />
            <text className="ex-label ex-label-strong" textAnchor="middle" x={px((X_ALPHA + X_BETA) / 2)} y={leverY - 10}>
              βの量 = {fmt(x - X_ALPHA, 2)} ÷ 0.50 = {fmt(chosen.fBeta, 2)}
            </text>
          </>}
          {chosen.phases !== "α+β" && (
            <text className="ex-label" textAnchor="middle" x={px((X_ALPHA + X_BETA) / 2)} y={leverY - 10}>
              x が 0.2〜0.7 の外：1相だけ
            </text>
          )}
          {[X_ALPHA, X_BETA].map((v) => <circle className="pf-tangent-point" cx={px(v)} cy={leverY} key={v} r={4} />)}
        </svg>
      </div>
      <p className="ex-hint">
        紺の実線が α相、点線が β相の曲線です。橙の破線は、2相に分かれたときのギブスエネルギー（共通接線）です。橙の丸が、ツールが返す最も低い候補です。下の棒は、x=0.2 から x までの長さが βの量に比例することを示します。
      </p>
    </figure>
  );
}

/** Push label baselines apart so that no two are closer than `gap`, keeping their order. */
function spreadLabels(ys: number[], gap: number): number[] {
  const order = ys.map((y, i) => [y, i] as const).sort((a, b) => a[0] - b[0]);
  const placed: number[] = [];
  for (const [y] of order) placed.push(placed.length ? Math.max(y, placed[placed.length - 1] + gap) : y);
  const out = new Array<number>(ys.length);
  order.forEach(([, i], k) => { out[i] = placed[k]; });
  return out;
}

function BetaPanel({ x, f }: { x: number; f: number }) {
  const { ref, viewport } = useStageViewport(BOUNDS, 0.75);
  const width = viewport.width, height = Math.max(220, viewport.height);
  const left = 40, right = width - 14, top = 30, bottom = height - 30;
  const px = (v: number) => left + v * (right - left);
  const py = (v: number) => bottom - v * (bottom - top);
  const path = SAMPLES.map((s, i) => `${i ? "L" : "M"}${px(s).toFixed(1)} ${py(betaFraction(s)).toFixed(1)}`).join("");
  return (
    <figure className="ex-panel">
      <figcaption className="ex-panel-title">ツールが返すβの量</figcaption>
      <div className="ex-canvas" ref={ref}>
        <svg aria-label={`x=${fmt(x, 2)}でβの量は${fmt(f, 2)}。0.2以下では0、0.7以上では1`} className="ex-svg" role="img" viewBox={`0 0 ${width} ${height}`}>
          <rect className="ex-ground" height={height} width={width} />
          <Regions bottom={bottom} px={px} top={top} />
          <g className="ex-axes">
            <line x1={left} x2={right} y1={bottom} y2={bottom} />
            {[0, 0.3, 1].map((v) => <text key={v} textAnchor="end" x={left - 6} y={py(v) + 4}>{v}</text>)}
            {axisTicks([0, 0.2, 0.7, 1], px, bottom + 18)}
          </g>
          <line className="pf-target" x1={left} x2={right} y1={py(TARGET)} y2={py(TARGET)} />
          <text className="ex-label ex-label-strong" textAnchor="end" x={right} y={py(TARGET) - 6}>目標 0.30</text>
          <path className="ex-curve" d={path} />
          <circle className="ex-head" cx={px(x)} cy={py(f)} r={8} />
        </svg>
      </div>
    </figure>
  );
}

function GoalPanel({ x, goal }: { x: number; goal: Goal }) {
  const { ref, viewport } = useStageViewport(BOUNDS, 0.75);
  const width = viewport.width, height = Math.max(220, viewport.height);
  const left = 44, right = width - 14, top = 30, bottom = height - 30;
  const value = goal === "J" ? (s: number) => clean(objectiveJ(s)) : equilibriumG;
  const yMax = goal === "J" ? 0.5 : 0.3;
  const best = goal === "J" ? BEST_X : LOWEST_G_X;
  const px = (v: number) => left + v * (right - left);
  const py = (v: number) => bottom - (v / yMax) * (bottom - top);
  const path = SAMPLES.map((s, i) => `${i ? "L" : "M"}${px(s).toFixed(1)} ${py(value(s)).toFixed(1)}`).join("");
  const flat = goal === "J" ? [[0, X_ALPHA], [X_BETA, 1]] : [];
  return (
    <figure className="ex-panel">
      <figcaption className="ex-panel-title">{goal === "J" ? "外側の目的 J" : "外側で最小にする G"}</figcaption>
      <div className="ex-canvas" ref={ref}>
        <svg aria-label={`x=${fmt(x, 2)}で${goal}は${fmt(value(x), goal === "J" ? 3 : 4)}。最小はx=${fmt(best, 2)}`} className="ex-svg" role="img" viewBox={`0 0 ${width} ${height}`}>
          <rect className="ex-ground" height={height} width={width} />
          <Regions bottom={bottom} px={px} top={top} />
          <g className="ex-axes">
            <line x1={left} x2={right} y1={bottom} y2={bottom} />
            {(goal === "J" ? [0, 0.09, 0.49] : [0, 0.1, 0.2]).map((v) => <text key={v} textAnchor="end" x={left - 6} y={py(v) + 4}>{v}</text>)}
            {axisTicks([0, 0.2, 0.7, 1], px, bottom + 18)}
          </g>
          {flat.map(([a, b]) => <line className="pf-flat" key={a} x1={px(a)} x2={px(b)} y1={py(value(a))} y2={py(value(a))} />)}
          <path className="ex-curve" d={path} />
          {goal === "J" && <text className="ex-label pf-flat-label" x={px(0.01)} y={py(0.09) + 22}>傾き 0</text>}
          <g className="ex-minimum">
            <circle cx={px(best)} cy={py(value(best))} r={6} />
            <text textAnchor="middle" x={px(best)} y={py(value(best)) - 12}>最小 {fmt(best, 2)}</text>
          </g>
          <circle className="ex-head" cx={px(x)} cy={py(value(x))} r={8} />
        </svg>
      </div>
    </figure>
  );
}

function Regions({ px, top, bottom }: { px: (v: number) => number; top: number; bottom: number }) {
  return <g>
    <rect className="pf-two-phase" height={bottom - top} width={px(X_BETA) - px(X_ALPHA)} x={px(X_ALPHA)} y={top} />
    {REGIONS.map((r) => (
      <text className="ex-label" key={r.label} textAnchor="middle" x={(px(r.from) + px(r.to)) / 2} y={top - 10}>{r.label}</text>
    ))}
  </g>;
}
