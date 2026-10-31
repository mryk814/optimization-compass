import { LensLegend } from "./LensBoard";
import { buildMethodLens, type LensCatalog } from "./method-lens";
import { ProblemSignature } from "./ProblemSignature";
import { blankSignature, shortValueLabel } from "./signature";

/**
 * The method's own lens with no problem placed on it: which axes it reads, which values support
 * it and which exclude it. The same card a Case or Diagnose overlays with a problem's dots.
 */
export function MethodReading({ methodId, catalog }: { methodId: string; catalog: LensCatalog }) {
  const lens = buildMethodLens(methodId, {}, catalog);
  const read = lens.axes.filter((axis) => axis.status !== "unread");
  return (
    <section className="vs-method-reading" aria-labelledby="method-reading-title">
      <header>
        <p className="eyebrow">この手法の目</p>
        <h2 id="method-reading-title">問題のどの軸を読むか</h2>
      </header>
      {read.length === 0 ? (
        <p className="vs-lens-gap">
          この手法を診断の12軸に結びつける規則・前提は、まだ登録されていません。未登録は「関係がない」ではなく、「まだ分からない」です。
        </p>
      ) : (
        <>
          <ProblemSignature axes={blankSignature()} lens={lens} showReading={false} label="この手法が読む軸と値" />
          <LensLegend withProblem={false} />
          <ul className="vs-method-reading-list">
            {read.map((axis) => (
              <li key={axis.questionId}>
                <strong>{axis.name}</strong>
                {axis.flipValues.length > 0 && <span className="is-supports">支える: {axis.flipValues.map((value) => shortValueLabel(axis.questionId, value)).join("・")}</span>}
                {axis.blockValues.length > 0 && <span className="is-blocks">外れる: {axis.blockValues.map((value) => shortValueLabel(axis.questionId, value)).join("・")}</span>}
              </li>
            ))}
          </ul>
          <p className="vs-method-reading-note">診断規則と前提（predicate）から作った図です。問題を当てはめると、Caseと診断で同じ軸に点が重なります。</p>
        </>
      )}
    </section>
  );
}
