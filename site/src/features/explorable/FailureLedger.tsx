import { useMemo, useState } from "react";

import { Choice, Slider } from "./controls";
import { ExplorableFrame } from "./ExplorableFrame";
import { fmt, fmtPair } from "./format";
import {
  BUDGET,
  BUDGET_UNIT,
  DOMAIN,
  halfSummaries,
  LEDGER,
  LEDGER_LENGTH,
  PENALTY_CHOICES,
  PENALTY_DEFAULT_INDEX,
  PROBE_DEFAULT,
  PROBE_RANGE,
  probeVerdict,
  ranking,
  STATUS_LABEL,
  tally,
  type EvalStatus,
  type LedgerRow,
  type Policy,
  type ProbeVerdict,
} from "./math/failureLedger";
import { markerBox, placeLabel, placeLabels, type Box, type PlacedLabel } from "./math/labelLayout";
import { makeScale, useStageViewport, type Scale } from "./svg";

const BOUNDS = { xMin: -0.2, xMax: 1.25, yMin: -0.2, yMax: 1.25 };
const ASPECT = 1;
const R = 5;
const PROBE_R = 8;
const LABEL_H = 18;
const DIGIT_W = 8;
const CJK_W = 13.2;

const POLICY_OPTIONS: ReadonlyArray<{ value: Policy; label: string }> = [
  { value: "status", label: "状態として記録する" },
  { value: "penalty", label: "罰則値に置き換える" },
];

/** A penalty is typed as a plain number: 0, 0.05, 10, 1000000. */
function penaltyText(value: number): string {
  return value >= 1000 ? value.toLocaleString("en-US") : String(value);
}

function percentText(share: number): string {
  const percent = share * 100;
  if (percent >= 0.01) return `${Number(percent.toFixed(3))}%`;
  return `${percent.toExponential(3).replace("e-", "e−")}%`;
}

function callList(calls: readonly number[]): string {
  return calls.map((call) => `評価${call}`).join("、");
}

export default function FailureLedger() {
  const [policy, setPolicy] = useState<Policy>("status");
  const [penaltyIndex, setPenaltyIndex] = useState(PENALTY_DEFAULT_INDEX);
  const [n, setN] = useState(LEDGER_LENGTH);
  const [probe, setProbe] = useState<readonly [number, number]>(PROBE_DEFAULT);
  const penalty = PENALTY_CHOICES[penaltyIndex];
  const { ref: stageRef, viewport } = useStageViewport(BOUNDS, ASPECT);
  const scale = useMemo(() => makeScale(viewport), [viewport]);

  const rows = useMemo(() => LEDGER.slice(0, n), [n]);
  const layout = useMemo(
    () => layoutLabels(rows, probe, scale, viewport.width, viewport.height),
    [rows, probe, scale, viewport.width, viewport.height],
  );
  const t = useMemo(() => tally(n), [n]);
  const halves = useMemo(() => halfSummaries(n, policy, penalty), [n, policy, penalty]);
  const rank = useMemo(() => ranking(n, policy, penalty), [n, policy, penalty]);
  const verdict = useMemo(() => probeVerdict(probe[0], probe[1], n, policy, penalty), [probe, n, policy, penalty]);
  const replaced = policy === "penalty";
  const summaryLine = summarize(policy, penalty, t, halves, rank);
  const probeLine = probeSentence(verdict, probe);

  return (
    <ExplorableFrame
      controls={
        <>
          <Choice<Policy> legend="失敗の扱い" onChange={setPolicy} options={POLICY_OPTIONS} value={policy} />
          <Slider
            disabled={!replaced}
            display={penaltyText(penalty)}
            hint="「罰則値に置き換える」のときだけ使います。"
            label="罰則値 P"
            max={PENALTY_CHOICES.length - 1}
            min={0}
            onChange={setPenaltyIndex}
            step={1}
            value={penaltyIndex}
            valueText={`P は ${penaltyText(penalty)}`}
          />
          <Slider
            display={`${n} / ${LEDGER_LENGTH}`}
            hint="何回目の評価までを台帳に入れるか。"
            label="ここまでの評価回数 N"
            max={LEDGER_LENGTH}
            min={1}
            onChange={setN}
            step={1}
            value={n}
          />
          <Slider
            display={fmt(probe[0])}
            label="試す点 u₁"
            max={PROBE_RANGE[1]}
            min={PROBE_RANGE[0]}
            onChange={(value) => setProbe([value, probe[1]])}
            step={0.01}
            value={probe[0]}
          />
          <Slider
            display={fmt(probe[1])}
            label="試す点 u₂"
            max={PROBE_RANGE[1]}
            min={PROBE_RANGE[0]}
            onChange={(value) => setProbe([probe[0], value])}
            step={0.01}
            value={probe[1]}
          />
        </>
      }
      id="failure-ledger"
      readout={
        <>
          <section aria-label="予算">
            <p className="ex-eyebrow">予算の消費（単位は{BUDGET_UNIT}）</p>
            <div
              aria-label={`${BUDGET_UNIT}の消費`}
              aria-valuemax={BUDGET}
              aria-valuemin={0}
              aria-valuenow={t.spent}
              aria-valuetext={`${BUDGET_UNIT} ${t.spent} / ${BUDGET}`}
              className="fl-meter"
              role="meter"
            >
              {Array.from({ length: BUDGET }, (_, index) => {
                const row = rows[index];
                return (
                  <span
                    className={row ? (row.status === "ok" ? "fl-cell fl-cell-ok" : "fl-cell fl-cell-fail") : "fl-cell"}
                    key={index}
                  />
                );
              })}
            </div>
            <p className="ex-hint">
              {BUDGET_UNIT} {t.spent} / {BUDGET}。成功 {t.ok}、失敗 {t.failed}（クラッシュ {t.crash}、時間切れ {t.timeout}
              、物理的にありえない出力 {t.nonphysical}）。失敗も1回に数えるので、残りは {t.remaining} 回です。
            </p>
          </section>
          <section aria-label="記録の要約">
            <p className="ex-eyebrow">{replaced ? `失敗を P = ${penaltyText(penalty)} の値にした要約` : "成功だけの要約（失敗は件数で別に数える）"}</p>
            <table className="ex-table fl-table">
              <tbody>
                <tr>
                  <th scope="row">最小の値</th>
                  <td>
                    {fmt(rank.bestValue, 4)}（{callList(rank.bestCalls)}）
                    {rank.bestCalls.length > 1 ? "。失敗が最良と同点です" : ""}
                  </td>
                </tr>
                {halves.map((half) => (
                  <tr key={half.side}>
                    <th scope="row">{half.side === "left" ? "u₁＜0.5 の側の平均" : "u₁≥0.5 の側の平均"}</th>
                    <td>
                      {half.mean === null ? "値なし" : fmt(half.mean, 4)}
                      （評価{half.evaluations}回のうち{replaced ? "値にした" : "成功"}{half.used}回）
                    </td>
                  </tr>
                ))}
                <tr>
                  <th scope="row">小さい順の上位3件</th>
                  <td>
                    {rank.topThree
                      .map((item) => `評価${item.call}（${fmt(item.value, 4)}${item.status === "ok" ? "" : "、失敗"}）`)
                      .join("、")}
                  </td>
                </tr>
                {replaced && (
                  <tr>
                    <th scope="row">成功どうしの差が、記録値の幅に占める割合</th>
                    <td>{rank.spreadShare === null ? "成功が1件のため定まらない" : percentText(rank.spreadShare)}</td>
                  </tr>
                )}
              </tbody>
            </table>
          </section>
          <p className={`ex-verdict ${replaced ? "ex-tone-swing" : "ex-tone-good"}`}>{summaryLine}</p>
          <p className={`ex-verdict ${verdict.kind === "known_violation" ? "ex-tone-bad" : "ex-tone-slow"}`}>{probeLine}</p>
          <section aria-label="評価の台帳">
            <p className="ex-eyebrow">評価の台帳（形は図のマークと同じ）</p>
            <table className="ex-table fl-table">
              <thead>
                <tr>
                  <th scope="col">回</th>
                  <th scope="col">点 (u₁, u₂, mode)</th>
                  <th scope="col">状態</th>
                  <th scope="col">値</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.call}>
                    <th scope="row">{row.call}</th>
                    <td>{`(${fmt(row.u1)}, ${fmt(row.u2)}, ${row.mode})`}</td>
                    <td>
                      <Glyph status={row.status} />{STATUS_LABEL[row.status]}
                    </td>
                    <td>{cellValue(row, replaced, penalty)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </>
      }
      stage={
        <figure className="ex-panel fl-panel">
          <figcaption className="ex-panel-title">評価した点と状態（u₁–u₂ の平面）</figcaption>
          <div className="ex-canvas" ref={stageRef}>
            <svg className="ex-svg" viewBox={`0 0 ${viewport.width} ${viewport.height}`}>
              <rect className="ex-ground" height={viewport.height} width={viewport.width} />
              <rect
                className="fl-domain"
                height={scale.py(DOMAIN[0]) - scale.py(DOMAIN[1])}
                width={scale.px(DOMAIN[1]) - scale.px(DOMAIN[0])}
                x={scale.px(DOMAIN[0])}
                y={scale.py(DOMAIN[1])}
              />
              <text className="ex-axes-text" x={scale.px(0)} y={scale.py(DOMAIN[1]) - 6}>範囲 [0, 1]²</text>
              <g className="ex-axes">
                {[0, 0.5, 1].map((tick) => (
                  <text key={`x${tick}`} textAnchor="middle" x={scale.px(tick)} y={scale.py(0) + 18}>{tick}</text>
                ))}
                {[0.5, 1].map((tick) => (
                  <text key={`y${tick}`} textAnchor="end" x={scale.px(0) - 6} y={scale.py(tick) + 4}>{tick}</text>
                ))}
                <text textAnchor="end" x={viewport.width - 6} y={scale.py(0) + 18}>u₁</text>
                <text x={scale.px(0) + 6} y={16}>u₂</text>
              </g>
              {verdict.kind === "unknown" && (
                <line
                  className="fl-link"
                  x1={scale.px(probe[0])}
                  x2={scale.px(LEDGER[verdict.nearest.call - 1].u1)}
                  y1={scale.py(probe[1])}
                  y2={scale.py(LEDGER[verdict.nearest.call - 1].u2)}
                />
              )}
              {rows.map((row) => (
                <Marker
                  cx={scale.px(row.u1)}
                  cy={scale.py(row.u2)}
                  key={row.call}
                  replaced={replaced && row.status !== "ok"}
                  status={row.status}
                />
              ))}
              {rows.map((row, index) => (
                <text
                  className="ex-label fl-call"
                  key={`t${row.call}`}
                  textAnchor={layout.calls[index].anchor}
                  x={layout.calls[index].x}
                  y={layout.calls[index].y}
                >
                  {row.call}
                </text>
              ))}
              <Probe known={verdict.kind === "known_violation"} x={scale.px(probe[0])} y={scale.py(probe[1])} />
              <text
                className="ex-label fl-probe-label"
                textAnchor={layout.probe.anchor}
                x={layout.probe.x}
                y={layout.probe.y}
              >
                試す点
              </text>
            </svg>
          </div>
        </figure>
      }
      summary={`${summaryLine}${probeLine}`}
    />
  );
}

const textWidth = (text: string) =>
  [...text].reduce((sum, ch) => sum + (ch.charCodeAt(0) > 0x2000 ? CJK_W : DIGIT_W), 0);

/** Boxes of the fixed texts in the figure (axis numbers, axis names, the range label). */
function fixedTextBoxes(scale: Scale, width: number): Box[] {
  const baseline = scale.py(0) + 18;
  const boxes: Box[] = [];
  for (const tick of [0, 0.5, 1]) {
    const w = textWidth(String(tick));
    boxes.push({ x0: scale.px(tick) - w / 2, y0: baseline - 12, x1: scale.px(tick) + w / 2, y1: baseline + 4 });
  }
  for (const tick of [0.5, 1]) {
    const w = textWidth(String(tick));
    boxes.push({ x0: scale.px(0) - 6 - w, y0: scale.py(tick) - 9, x1: scale.px(0) - 6, y1: scale.py(tick) + 4 });
  }
  boxes.push({ x0: width - 6 - textWidth("u₁"), y0: baseline - 12, x1: width - 6, y1: baseline + 4 });
  boxes.push({ x0: scale.px(0) + 6, y0: 3, x1: scale.px(0) + 6 + textWidth("u₂"), y1: 19 });
  const range = textWidth("範囲 [0, 1]²");
  boxes.push({ x0: scale.px(0), y0: scale.py(DOMAIN[1]) - 18, x1: scale.px(0) + range, y1: scale.py(DOMAIN[1]) - 3 });
  return boxes;
}

interface LabelLayout {
  calls: PlacedLabel[];
  probe: PlacedLabel;
}

/** Puts every number and the probe label where it overlaps neither a marker nor another text. */
function layoutLabels(
  rows: readonly LedgerRow[],
  probe: readonly [number, number],
  scale: Scale,
  width: number,
  height: number,
): LabelLayout {
  const bounds: Box = { x0: 1, y0: 1, x1: width - 1, y1: height - 1 };
  const fixed = fixedTextBoxes(scale, width);
  const probeX = scale.px(probe[0]);
  const probeY = scale.py(probe[1]);
  // The probe label is the longest text, so it chooses its spot first; the numbers then avoid it.
  const markers = rows.map((row) => markerBox(scale.px(row.u1), scale.py(row.u2), R + 1));
  const placedProbe = placeLabel(
    { cx: probeX, cy: probeY, radius: PROBE_R, width: textWidth("試す点"), height: LABEL_H },
    [...fixed, ...markers],
    bounds,
  );
  const calls = placeLabels(
    rows.map((row) => ({
      cx: scale.px(row.u1),
      cy: scale.py(row.u2),
      radius: R,
      width: textWidth(String(row.call)),
      height: LABEL_H,
    })),
    [...fixed, markerBox(probeX, probeY, PROBE_R + 1), placedProbe.box],
    bounds,
  );
  return { calls, probe: placedProbe };
}

function cellValue(row: LedgerRow, replaced: boolean, penalty: number): string {
  if (row.value !== null) return fmt(row.value, 4);
  return replaced ? `${penaltyText(penalty)}（置き換え）` : "値なし";
}

function summarize(
  policy: Policy,
  penalty: number,
  t: ReturnType<typeof tally>,
  halves: ReturnType<typeof halfSummaries>,
  rank: ReturnType<typeof ranking>,
): string {
  const [left, right] = halves;
  const mean = (value: number | null) => (value === null ? "なし" : fmt(value, 4));
  if (policy === "status") {
    return `失敗は値にせず状態で数えます。${BUDGET_UNIT} ${t.spent} 回のうち成功 ${t.ok}、失敗 ${t.failed} です。`
      + `成功だけの平均は、u₁＜0.5 の側が ${mean(left.mean)}、u₁≥0.5 の側が ${mean(right.mean)} です。`;
  }
  return `失敗 ${t.failed} 件を P = ${penaltyText(penalty)} の値にすると、平均は u₁＜0.5 の側が ${mean(left.mean)}、`
    + `u₁≥0.5 の側が ${mean(right.mean)} になります。最小の値は ${fmt(rank.bestValue, 4)}（${callList(rank.bestCalls)}）です。`;
}

function probeSentence(verdict: ProbeVerdict, probe: readonly [number, number]): string {
  const where = fmtPair(probe[0], probe[1]);
  if (verdict.kind === "known_violation") {
    return `試す点 ${where} は、${verdict.reasons.join("、")}です。実行する前に違反と分かるので、評価回数を使わず、台帳にも入れません。`;
  }
  const { nearest, nearestSuccess, guess } = verdict;
  const near = `試す点 ${where} に最も近い記録は評価${nearest.call}（${STATUS_LABEL[nearest.status]}、距離 ${fmt(nearest.distance, 3)}）です。`;
  const success = `最も近い成功は評価${nearestSuccess.call}で、距離は ${fmt(nearestSuccess.distance, 3)} です。`;
  if (guess.kind === "none") {
    return `${near}失敗には値がないので、この点の値は予想しません。${success}この点が実行できるかは、台帳からは分かりません。`;
  }
  if (guess.replaced) {
    return `${near}罰則値に置き換えているため、この点の値を ${penaltyText(guess.value)} と予想します。実行できるかどうかは分かっていないのに、悪い値だと言い切っています。${success}`;
  }
  return `${near}この点の値を ${fmt(guess.value, 4)} と予想します。実行できるかどうかは、実行するまで分かりません。`;
}

function Marker({
  cx, cy, status, replaced,
}: { cx: number; cy: number; status: EvalStatus; replaced: boolean }) {
  return (
    <g>
      {replaced && <circle className="fl-replaced" cx={cx} cy={cy} r={R + 5} />}
      <ShapeAt cx={cx} cy={cy} r={R} status={status} />
    </g>
  );
}

function ShapeAt({ cx, cy, r, status }: { cx: number; cy: number; r: number; status: EvalStatus }) {
  switch (status) {
    case "ok":
      return <circle className="fl-ok" cx={cx} cy={cy} r={r} />;
    case "crash":
      return <path className="fl-crash" d={`M${cx - r} ${cy - r}L${cx + r} ${cy + r}M${cx - r} ${cy + r}L${cx + r} ${cy - r}`} />;
    case "timeout":
      return <rect className="fl-timeout" height={2 * r - 1} width={2 * r - 1} x={cx - r + 0.5} y={cy - r + 0.5} />;
    case "nonphysical":
      return <path className="fl-nonphysical" d={`M${cx} ${cy - r}L${cx + r} ${cy + r}L${cx - r} ${cy + r}Z`} />;
  }
}

function Probe({ known, x, y }: { known: boolean; x: number; y: number }) {
  const r = 8;
  if (known) {
    return <path className="fl-probe-known" d={`M${x - r} ${y - r}L${x + r} ${y + r}M${x - r} ${y + r}L${x + r} ${y - r}`} />;
  }
  return <path className="fl-probe" d={`M${x} ${y - r}L${x + r} ${y}L${x} ${y + r}L${x - r} ${y}Z`} />;
}

/** The same marker as in the plot, so a table row can be matched to its point by shape. */
function Glyph({ status }: { status: EvalStatus }) {
  return (
    <svg aria-hidden="true" className="fl-glyph" height={18} viewBox="0 0 18 18" width={18}>
      <ShapeAt cx={9} cy={9} r={6} status={status} />
    </svg>
  );
}
