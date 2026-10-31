import { useMemo, useState, type CSSProperties } from "react";

import { Choice, PlayerBar } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import { fmt, fmtPair } from "./format";
import type { Bounds } from "./math/contours";
import { levelLine, type Vec2 } from "./math/lp2d";
import {
  DOMAIN_LABEL, DOMAINS, VD_PROFIT, roundRelaxation, solveDomains, type Domain, type DomainSolution,
  type RoundedPlan,
} from "./math/variableDomain";
import { makeScale, polylinePath, useStageViewport } from "./svg";
import { useReplayOnChange, useTimeline } from "./useTimeline";

const BOUNDS: Bounds = { xMin: -0.7, xMax: 5.2, yMin: -0.7, yMax: 3.9 };
const ASPECT = (BOUNDS.yMax - BOUNDS.yMin) / (BOUNDS.xMax - BOUNDS.xMin);
const X_TICKS = [0, 1, 2, 3, 4, 5];
const Y_TICKS = [1, 2, 3];

const OPTIONS: ReadonlyArray<{ value: Domain; label: string }> = [
  { value: "continuous", label: DOMAIN_LABEL.continuous },
  { value: "integer", label: DOMAIN_LABEL.integer },
  { value: "binary", label: DOMAIN_LABEL.binary },
];

export default function VariableDomain() {
  const [d1, setD1] = useState<Domain>("continuous");
  const [d2, setD2] = useState<Domain>("continuous");
  const { ref: stageRef, viewport } = useStageViewport(BOUNDS, ASPECT);
  const scale = useMemo(() => makeScale(viewport), [viewport]);
  const s = useMemo(() => solveDomains(d1, d2), [d1, d2]);
  const [from, setFrom] = useState<DomainSolution>(s);
  const timeline = useTimeline(1, 1.2);
  useReplayOnChange(timeline, `${d1}|${d2}`);
  const t = timeline.position * timeline.position * (3 - 2 * timeline.position);
  const mix = (a: number, b: number) => a + (b - a) * t;
  const choose = (which: 1 | 2) => (value: Domain) => {
    setFrom(s);
    if (which === 1) setD1(value);
    else setD2(value);
  };
  const reference = useMemo(() => solveDomains("continuous", "continuous"), []);
  const grid = useMemo(
    () => DOMAINS.map((row) => DOMAINS.map((column) => solveDomains(row, column))),
    [],
  );
  const [rounding, setRounding] = useState(false);
  const rounded = useMemo(() => roundRelaxation(d1, d2), [d1, d2]);
  const baselineLevel = levelLine(VD_PROFIT, reference.bestValue, viewport.bounds);

  const relaxedPath = polylinePath(s.relaxedVertices, scale) + "Z";
  const level = levelLine(VD_PROFIT, mix(from.bestValue, s.bestValue), viewport.bounds);
  const relaxedLevel = levelLine(VD_PROFIT, mix(from.relaxedValue, s.relaxedValue), viewport.bounds);
  const relaxedOnBaseline = Math.abs(s.relaxedValue - reference.bestValue) < 1e-9 && Math.abs(from.relaxedValue - reference.bestValue) < 1e-9;
  const bestNow: Vec2 = [mix(from.best[0], s.best[0]), mix(from.best[1], s.best[1])];
  const relaxedNow: Vec2 = [mix(from.relaxedPoint[0], s.relaxedPoint[0]), mix(from.relaxedPoint[1], s.relaxedPoint[1])];
  const showGap = s.gap > 1e-9;
  const verdict = verdictText(s, reference.bestValue);
  const summary = `製品Aは${DOMAIN_LABEL[d1]}、製品Bは${DOMAIN_LABEL[d2]}のとき。${verdict}`;

  return (
    <ExplorableFrame
      controls={
        <>
          <Choice
            legend="製品Aの量 x₁ の定義域"
            onChange={choose(1)}
            options={OPTIONS}
            value={d1}
          />
          <Choice
            legend="製品Bの量 x₂ の定義域"
            onChange={choose(2)}
            options={OPTIONS}
            value={d2}
          />
          <label className="vd-toggle">
            <input checked={rounding} onChange={(event) => setRounding(event.target.checked)} type="checkbox" />
            <span>丸めてみる</span>
          </label>
          <p className="ex-hint">
            目的 5x₁+4x₂ と二つの資源制約 6x₁+4x₂≤24、x₁+2x₂≤6 は固定です。変わるのは、各変数が取れる値だけです。
          </p>
        </>
      }
      id="variable-domain-switch"
      player={<PlayerBar positionText={`${DOMAIN_LABEL[d1]} × ${DOMAIN_LABEL[d2]}`} stepLabel="定義域の切り替え" timeline={timeline} />}
      readout={
        <>
          <section aria-label="九通りの一覧">
            <p className="ex-eyebrow">九通りの一覧。押すと切り替わる（上段が利益、下段がギャップ）</p>
            <table className="ex-table vd-grid">
              <thead>
                <tr>
                  <th scope="col">A↓ B→</th>
                  {DOMAINS.map((column) => <th key={column} scope="col">B {DOMAIN_LABEL[column]}</th>)}
                </tr>
              </thead>
              <tbody>
                {DOMAINS.map((row, i) => (
                  <tr key={row}>
                    <th scope="row">A {DOMAIN_LABEL[row]}</th>
                    {DOMAINS.map((column, j) => {
                      const cell = grid[i][j];
                      const here = row === d1 && column === d2;
                      return (
                        <td key={column}>
                          <button
                            aria-label={`製品Aを${DOMAIN_LABEL[row]}、製品Bを${DOMAIN_LABEL[column]}にする。利益 ${fmt(cell.bestValue)}、ギャップ ${fmt(cell.gap)}`}
                            aria-pressed={here}
                            className={here ? "vd-cell is-current" : "vd-cell"}
                            onClick={() => {
                              setFrom(s);
                              setD1(row);
                              setD2(column);
                            }}
                            style={{ "--gap": cell.gap / 2 } as CSSProperties}
                            type="button"
                          >
                            <span className="vd-cell-profit">{fmt(cell.bestValue)}</span>
                            <span className="vd-cell-gap">{cell.gap > 1e-9 ? fmt(cell.gap) : "0"}</span>
                          </button>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
          <section aria-label="最適値の比較">
            <p className="ex-eyebrow">利益 z = 5x₁ + 4x₂ を、三つの問題で比べる</p>
            <table className="ex-table vd-table">
              <thead>
                <tr>
                  <th scope="col">問題</th>
                  <th scope="col">最適解</th>
                  <th scope="col">利益 z</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <th scope="row">両方連続<span className="vd-state">基準</span></th>
                  <td>{fmtPair(reference.best[0], reference.best[1])}</td>
                  <td>{fmt(reference.bestValue)}</td>
                </tr>
                <tr>
                  <th scope="row">
                    選んだ定義域を連続に戻した緩和
                    <span className="vd-state">{relaxNote(s)}</span>
                  </th>
                  <td>{fmtPair(s.relaxedPoint[0], s.relaxedPoint[1])}</td>
                  <td>{fmt(s.relaxedValue)}</td>
                </tr>
                <tr className="ex-row-best">
                  <th scope="row">
                    選んだ定義域の最適解
                    <span className="vd-state">{candidateNote(s)}</span>
                  </th>
                  <td>{fmtPair(s.best[0], s.best[1], s.bestHasFraction ? 2 : 0)}</td>
                  <td>{fmt(s.bestValue, s.bestHasFraction ? 2 : 0)}</td>
                </tr>
              </tbody>
            </table>
            <p className="ex-hint">
              緩和との差（ギャップ）は {fmt(s.gap)}。両方連続の利益 {fmt(reference.bestValue)} との差は {fmt(reference.bestValue - s.bestValue)} です。
            </p>
          </section>
          {rounding && <p className="ex-hint vd-round-note">{roundingText(rounded)}</p>}
          <p className={`ex-verdict ${s.gap === 0 ? "ex-tone-good" : "ex-tone-slow"}`}>{verdict}</p>
        </>
      }
      stage={
        <figure className="ex-panel">
          <figcaption className="ex-panel-title">選べる計画の集合</figcaption>
          <div className="ex-canvas" ref={stageRef}>
            <svg className="ex-svg" viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
              <rect className="ex-ground" height={viewport.height} width={viewport.width} />
              <g className="ex-axes">
                <line x1={scale.px(0)} x2={scale.px(0)} y1={0} y2={viewport.height} />
                <line x1={0} x2={viewport.width} y1={scale.py(0)} y2={scale.py(0)} />
                {X_TICKS.map((tick) => (
                  <text key={`x${tick}`} textAnchor="middle" x={scale.px(tick)} y={scale.py(0) + 18}>{tick}</text>
                ))}
                {Y_TICKS.map((tick) => (
                  <text key={`y${tick}`} textAnchor="end" x={scale.px(0) - 7} y={scale.py(tick) + 4}>{tick}</text>
                ))}
                <text textAnchor="end" x={viewport.width - 8} y={scale.py(0) - 8}>x₁ A</text>
                <text x={scale.px(0) + 8} y={16}>x₂ B</text>
              </g>
              <path className="vd-relaxed" d={relaxedPath} />
              {d1 === "binary" && (
                <g>
                  <line className="vd-bound" x1={scale.px(1)} x2={scale.px(1)} y1={scale.py(0)} y2={scale.py(BOUNDS.yMax)} />
                  <text className="ex-label" x={scale.px(1) + 6} y={scale.py(3.55)}>x₁ ≤ 1</text>
                </g>
              )}
              {d2 === "binary" && (
                <g>
                  <line className="vd-bound" x1={scale.px(0)} x2={scale.px(BOUNDS.xMax)} y1={scale.py(1)} y2={scale.py(1)} />
                  <text className="ex-label" textAnchor="end" x={scale.px(BOUNDS.xMax) - 6} y={scale.py(1) - 6}>x₂ ≤ 1</text>
                </g>
              )}
              {baselineLevel && (
                <g>
                  <line
                    className="vd-baseline"
                    x1={scale.px(baselineLevel[0][0])}
                    x2={scale.px(baselineLevel[1][0])}
                    y1={scale.py(baselineLevel[0][1])}
                    y2={scale.py(baselineLevel[1][1])}
                  />
                  <circle className="vd-baseline-dot" cx={scale.px(reference.best[0])} cy={scale.py(reference.best[1])} r={5} />
                  <text className="ex-label" x={scale.px((reference.bestValue - 4 * 3.5) / 5) + 10} y={scale.py(3.5)}>
                    連続の最適 利益{fmt(reference.bestValue, 0)}
                  </text>
                </g>
              )}
              {relaxedLevel && showGap && !relaxedOnBaseline && (
                <line
                  className="vd-level-relaxed"
                  x1={scale.px(relaxedLevel[0][0])}
                  x2={scale.px(relaxedLevel[1][0])}
                  y1={scale.py(relaxedLevel[0][1])}
                  y2={scale.py(relaxedLevel[1][1])}
                />
              )}
              {level && (
                <line
                  className="ex-level-now"
                  x1={scale.px(level[0][0])}
                  x2={scale.px(level[1][0])}
                  y1={scale.py(level[0][1])}
                  y2={scale.py(level[1][1])}
                />
              )}
              {t < 1 && (
                <g opacity={1 - t}>
                  <FeasibleLayer scale={scale} set={from.feasible} />
                </g>
              )}
              <g opacity={t}>
                <FeasibleLayer scale={scale} set={s.feasible} />
              </g>
              {showGap && (
                <g opacity={t}>
                  <line
                    className="vd-gap"
                    x1={scale.px(s.relaxedPoint[0])}
                    x2={scale.px(s.best[0])}
                    y1={scale.py(s.relaxedPoint[1])}
                    y2={scale.py(s.best[1])}
                  />
                  <text
                    className="vd-gap-label"
                    textAnchor="end"
                    x={scale.px((s.relaxedPoint[0] + s.best[0]) / 2) - 8}
                    y={scale.py((s.relaxedPoint[1] + s.best[1]) / 2) + 22}
                  >
                    ギャップ {fmt(s.gap)}
                  </text>
                </g>
              )}
              {rounding && !rounded.nothingToRound && (
                <g>
                  <line
                    className="vd-round-link"
                    x1={scale.px(rounded.from[0])}
                    x2={scale.px(rounded.nearest.point[0])}
                    y1={scale.py(rounded.from[1])}
                    y2={scale.py(rounded.nearest.point[1])}
                  />
                  <RoundMark plan={rounded.nearest} scale={scale} shape="nearest" />
                  <RoundMark plan={rounded.floor} scale={scale} shape="floor" />
                  <text
                    className="ex-label"
                    textAnchor="end"
                    x={scale.px(rounded.nearest.point[0]) - 12}
                    y={scale.py(rounded.nearest.point[1]) + 4}
                  >
                    丸め{rounded.nearest.feasible ? "" : "（不可）"}
                  </text>
                  {!rounded.nearest.feasible && (
                    <text
                      className="ex-label"
                      textAnchor="end"
                      x={scale.px(rounded.nearest.point[0]) - 12}
                      y={scale.py(rounded.nearest.point[1]) + 20}
                    >
                      {excessText(rounded.nearest.excess)}
                    </text>
                  )}
                  {(rounded.floor.point[0] !== rounded.nearest.point[0] || rounded.floor.point[1] !== rounded.nearest.point[1]) && (
                    <text
                      className="ex-label"
                      textAnchor="end"
                      x={scale.px(rounded.floor.point[0]) - 12}
                      y={scale.py(rounded.floor.point[1]) + 16}
                    >
                      切り下げ
                    </text>
                  )}
                </g>
              )}
              {showGap
                ? <path className="milp-lp" d={diamond(scale.px(relaxedNow[0]), scale.py(relaxedNow[1]), 9)} />
                : <path className="vd-diamond-ghost" d={diamond(scale.px(relaxedNow[0]), scale.py(relaxedNow[1]), 14)} />}
              <path className="milp-best" d={star(scale.px(bestNow[0]), scale.py(bestNow[1]), 10)} />
            </svg>
          </div>
        </figure>
      }
      summary={summary}
    />
  );
}

function FeasibleLayer({
  set, scale,
}: { set: DomainSolution["feasible"]; scale: ReturnType<typeof makeScale> }) {
  if (set.kind === "region") return <path className="ex-feasible" d={polylinePath(set.vertices, scale) + "Z"} />;
  if (set.kind === "segments") {
    return (
      <g>
        {set.segments.map(([from, to]) => (
          <g key={`${from[0]},${from[1]}`}>
            <line
              className="vd-segment"
              x1={scale.px(from[0])}
              x2={scale.px(to[0])}
              y1={scale.py(from[1])}
              y2={scale.py(to[1])}
            />
            <circle className="milp-dot-in" cx={scale.px(from[0])} cy={scale.py(from[1])} r={4.5} />
          </g>
        ))}
      </g>
    );
  }
  return (
    <g>
      {set.points.map((point: Vec2) => (
        <circle
          className="milp-dot-in"
          cx={scale.px(point[0])}
          cy={scale.py(point[1])}
          key={`${point[0]},${point[1]}`}
          r={5}
        />
      ))}
    </g>
  );
}

function RoundMark({
  plan, scale, shape,
}: { plan: RoundedPlan; scale: ReturnType<typeof makeScale>; shape: "nearest" | "floor" }) {
  const x = scale.px(plan.point[0]);
  const y = scale.py(plan.point[1]);
  const tone = plan.feasible ? "vd-round-ok" : "vd-round-bad";
  if (shape === "floor") return <path className={`${tone} vd-round-floor`} d={`M${x} ${y - 8}L${x + 8} ${y + 7}L${x - 8} ${y + 7}Z`} />;
  return plan.feasible
    ? <circle className={tone} cx={x} cy={y} r={8} />
    : <path className={tone} d={`M${x - 8} ${y - 8}L${x + 8} ${y + 8}M${x - 8} ${y + 8}L${x + 8} ${y - 8}`} />;
}

function roundingText(r: ReturnType<typeof roundRelaxation>): string {
  if (r.nothingToRound) {
    return `緩和の最適解 ${fmtPair(r.from[0], r.from[1])} は、選んだ定義域でもそのまま選べる値なので、丸める必要がありません。`;
  }
  const describe = (name: string, plan: RoundedPlan) => {
    const pair = fmtPair(plan.point[0], plan.point[1], 0);
    if (plan.feasible) return `${name}の ${pair} は資源の上限を守り、利益は ${fmt(plan.profit, 0)}`;
    const over = plan.excess
      .map((value, index) => (value > 1e-9 ? `資源${index + 1}を ${fmt(value, 0)} 超過` : ""))
      .filter(Boolean)
      .join("、");
    return `${name}の ${pair} は${over}して実行できません（式の上の利益は ${fmt(plan.profit, 0)}）`;
  };
  return `緩和の最適解 ${fmtPair(r.from[0], r.from[1])} を丸めると（0.5 は切り上げ）、${describe("丸め", r.nearest)}。${describe("切り下げ", r.floor)}。`;
}

function excessText(excess: [number, number]): string {
  return excess
    .map((value, index) => (value > 1e-9 ? `資源${index + 1}を${fmt(value, 0)}超過` : ""))
    .filter(Boolean)
    .join("・");
}

function diamond(x: number, y: number, r: number): string {
  return `M${x} ${y - r}L${x + r} ${y}L${x} ${y + r}L${x - r} ${y}Z`;
}

function star(x: number, y: number, r: number): string {
  const points = Array.from({ length: 10 }, (_, index) => {
    const radius = index % 2 === 0 ? r : r * 0.45;
    const angle = -Math.PI / 2 + (index * Math.PI) / 5;
    return `${x + radius * Math.cos(angle)} ${y + radius * Math.sin(angle)}`;
  });
  return `M${points.join("L")}Z`;
}

function relaxNote(s: DomainSolution): string {
  const hasBinary = s.d1 === "binary" || s.d2 === "binary";
  return hasBinary ? "整数条件を外し、0か1は 0 以上 1 以下にする" : "整数条件を外すだけで、領域は変わらない";
}

function candidateNote(s: DomainSolution): string {
  switch (s.feasible.kind) {
    case "region":
      return "候補は無限にあり、頂点を調べれば足りる";
    case "segments":
      return `連続の変数は線分の端まで。${s.candidateCount} 本の線分を全部調べた`;
    case "points":
      return `候補は ${s.candidateCount} 点。全部調べた`;
    default:
      return "";
  }
}

function verdictText(s: DomainSolution, referenceValue: number): string {
  const best = s.bestHasFraction ? fmtPair(s.best[0], s.best[1]) : fmtPair(s.best[0], s.best[1], 0);
  const value = fmt(s.bestValue, s.bestHasFraction ? 2 : 0);
  if (s.d1 === "continuous" && s.d2 === "continuous") {
    return `選べる計画は多角形の面全体です。最適解は頂点 ${best}、利益 ${value}。この値が、ほかの組み合わせの上限になります。`;
  }
  const lost = referenceValue - s.bestValue;
  if (s.gap < 1e-9) {
    return `最適解は ${best}、利益 ${value}。連続に戻した緩和の最適値 ${fmt(s.relaxedValue)} と同じなので、緩和の最適解がそのまま選べます。両方連続の ${fmt(referenceValue)} からは ${fmt(lost)} 下がります。`;
  }
  return `最適解は ${best}、利益 ${value}。連続に戻した緩和の最適値は ${fmt(s.relaxedValue)} で、差は ${fmt(s.gap)}。緩和の解は選べないので、定義域の中で探し直した結果です。`;
}
