import { useId, useMemo, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { EvidenceLinks } from "../features/evidence/EvidenceLinks";
import { DispositionMark, type Disposition } from "./DispositionMark";
import { buildMethodLens, flipText, type LensAxis, type LensCatalog, type MethodLens } from "./method-lens";
import { ProblemSignature } from "./ProblemSignature";
import { axisValueText, type SignatureAnswer, type SignatureAxis } from "./signature";

export interface LensEntry {
  methodId: string;
  name: string;
  href?: string;
  disposition: Disposition;
  /** Where the disposition comes from: the Case's sourced editorial reason, or the rule engine. */
  origin: "case" | "rules";
  reason?: string;
  sourceIds?: readonly string[];
}

/**
 * One problem signature, looked at through each method in turn. The board puts candidates,
 * conditional candidates and exclusions on equal footing: every entry gets the same tab, the
 * same overlay, and the same "what would change this" line.
 */
export function LensBoard({
  axes,
  answers,
  catalog,
  entries,
  heading,
  intro,
  renderMethodLink,
}: {
  axes: readonly SignatureAxis[];
  answers: Readonly<Record<string, SignatureAnswer | undefined>>;
  catalog: LensCatalog | undefined;
  entries: readonly LensEntry[];
  heading?: ReactNode;
  intro?: ReactNode;
  /** Lets a surface keep its journey state on method links. */
  renderMethodLink?: (entry: LensEntry) => ReactNode;
}) {
  const id = useId();
  const [selected, setSelected] = useState(entries[0]?.methodId);
  const lenses = useMemo(
    () => new Map(entries.map((entry) => [entry.methodId, catalog ? buildMethodLens(entry.methodId, answers, catalog) : undefined])),
    [answers, catalog, entries],
  );
  const active = entries.find((entry) => entry.methodId === selected) ?? entries[0];
  const activeLens = active ? lenses.get(active.methodId) : undefined;
  return (
    <section className="vs-lens-board" aria-label="手法の目で問題の署名を読む">
      {heading}
      {intro}
      <div className="vs-lens-tabs" role="tablist" aria-label="どの手法の目で見るか">
        {entries.map((entry) => {
          const lens = lenses.get(entry.methodId);
          const isActive = entry.methodId === active?.methodId;
          return (
            <button
              aria-controls={`${id}-panel`}
              aria-selected={isActive}
              className={`vs-lens-tab is-${entry.disposition}`}
              key={entry.methodId}
              onClick={() => setSelected(entry.methodId)}
              role="tab"
              type="button"
            >
              <DispositionMark kind={entry.disposition} />
              <strong>{entry.name}</strong>
              {lens && <ProblemSignature axes={axes} lens={lens} size="compact" label={`${entry.name}の目で見た署名`} />}
              {lens && <small>{lensTally(lens, entry.disposition)}</small>}
            </button>
          );
        })}
      </div>
      {active && (
        <div className="vs-lens-panel" id={`${id}-panel`} role="tabpanel">
          <ProblemSignature axes={axes} lens={activeLens} showReading={false} label={`${active.name}の目で見た問題の署名`} />
          <LensLegend />
          <LensExplanation axes={axes} entry={active} lens={activeLens} renderMethodLink={renderMethodLink} />
        </div>
      )}
    </section>
  );
}

function lensTally(lens: MethodLens, disposition: Disposition): string {
  const parts = [];
  if (disposition === "excluded" && lens.blockingAxes.length === 0) parts.push("規則上の除外軸なし");
  if (lens.blockingAxes.length) parts.push(`外れる軸 ${lens.blockingAxes.length}`);
  if (lens.supportingAxes.length) parts.push(`支える軸 ${lens.supportingAxes.length}`);
  if (lens.openAxes.length) parts.push(`未確定 ${lens.openAxes.length}`);
  return parts.join(" · ") || (lens.readAxisCount ? "この回答では規則が働かない" : "読む軸の登録なし");
}

export function LensLegend({ withProblem = true }: { withProblem?: boolean }) {
  return (
    <ul className="vs-legend" aria-label="記号の読み方">
      {withProblem && <li><span className="vs-legend-dot" aria-hidden="true" />この問題の値</li>}
      <li><span className="vs-legend-ring" aria-hidden="true" />手法を支える値（規則・前提・型）</li>
      <li><span className="vs-legend-slash" aria-hidden="true" />手法が外れる値</li>
      {withProblem && <li><span className="vs-legend-hatch" aria-hidden="true" />不明と回答</li>}
      {withProblem && <li><span className="vs-legend-missing" aria-hidden="true" />まだ答えていない</li>}
    </ul>
  );
}

const STATUS_TEXT: Record<LensAxis["status"], string> = {
  supports: "支える",
  blocks: "外れる",
  open: "未確定",
  silent: "この値では規則なし",
  unread: "",
};

function LensExplanation({ axes, entry, lens, renderMethodLink }: { axes: readonly SignatureAxis[]; entry: LensEntry; lens?: MethodLens; renderMethodLink?: (entry: LensEntry) => ReactNode }) {
  const axisByQuestion = new Map(axes.map((axis) => [axis.questionId, axis]));
  // Silent axes matter only when another value there would change the picture.
  const relevant = lens?.axes.filter((axis) => axis.status !== "unread" && (axis.status !== "silent" || axis.flipValues.length > 0)) ?? [];
  const againstCandidate = entry.disposition === "excluded" || entry.disposition === "conditional";
  const order: Record<LensAxis["status"], number> = againstCandidate
    ? { blocks: 0, open: 1, silent: 2, supports: 3, unread: 4 }
    : { blocks: 0, open: 1, supports: 2, silent: 3, unread: 4 };
  relevant.sort((a, b) => order[a.status] - order[b.status]);
  const ruleGap = entry.disposition === "excluded" && entry.origin === "case" && lens !== undefined && lens.blockingAxes.length === 0;
  return (
    <div className="vs-lens-explanation">
      <header>
        <DispositionMark kind={entry.disposition} />
        <h3>{renderMethodLink ? renderMethodLink(entry) : entry.href ? <Link to={entry.href}>{entry.name}</Link> : entry.name}</h3>
        <small>{entry.origin === "case" ? "Caseで判断（理由と出典つき）" : "診断規則による判断"}</small>
      </header>
      {entry.reason && <p className="vs-lens-reason">{entry.reason}</p>}
      {ruleGap && (
        <p className="vs-lens-gap">
          診断規則には、この回答でこの手法を外す規則がありません。除外は上のCaseの理由に基づきます。下の「↺」は、どの値なら規則がこの手法を支えるかを示します。
        </p>
      )}
      {relevant.length === 0 && (
        <p className="vs-lens-none">
          この手法を12軸のどれかに結びつける規則・前提は、まだ登録されていません。判断は上の理由だけに基づきます。
        </p>
      )}
      {relevant.length > 0 && (
        <ol className="vs-lens-axes">
          {relevant.map((axis) => {
            const signatureAxis = axisByQuestion.get(axis.questionId);
            const flip = axis.status === "supports" ? undefined : flipText(axis);
            return (
              <li className={`is-${axis.status}`} key={axis.questionId}>
                <span className="vs-lens-axis-name">{axis.name}</span>
                <span className="vs-lens-axis-value">{signatureAxis ? axisValueText(signatureAxis) : ""}</span>
                <strong className="vs-lens-axis-status">{STATUS_TEXT[axis.status]}{axis.conflict ? "（規則と前提が食い違う・要確認）" : ""}</strong>
                {axis.evidence.length > 0 && (
                  <ul>
                    {axis.evidence.map((item) => (
                      <li key={item.id}><code>{item.id}</code> {item.text}</li>
                    ))}
                  </ul>
                )}
                {flip && <p className="vs-lens-flip">{flip}</p>}
              </li>
            );
          })}
        </ol>
      )}
      {entry.sourceIds && entry.sourceIds.length > 0 && <EvidenceLinks sourceIds={entry.sourceIds} />}
    </div>
  );
}
