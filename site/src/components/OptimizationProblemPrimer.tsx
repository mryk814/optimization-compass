import rawPrimer from "../../public/data/formulation-primer.json";
import {
  parseFormulationPrimerIndex,
  type PrimerTerm,
} from "../contracts/formulation-primer";

export interface CaseFormulation {
  decisionVariables: string;
  variableDomain: string;
  objective: string;
  constraints: string;
}

export const formulationPrimer = parseFormulationPrimerIndex(rawPrimer);
const termById = new Map(formulationPrimer.terms.map((term) => [term.term_id, term]));

export function termsForQuestion(questionId: string): PrimerTerm[] {
  const ids = formulationPrimer.diagnosis_mappings.find(
    (mapping) => mapping.question_id === questionId,
  )?.term_ids ?? [];
  return ids.flatMap((id) => termById.get(id) ?? []);
}

export function diagnosisFieldCue(questionId: string): string | undefined {
  return formulationPrimer.diagnosis_mappings.find(
    (mapping) => mapping.question_id === questionId,
  )?.cue_ja;
}

export function OptimizationProblemPrimer({
  caseFormulation,
}: {
  caseFormulation?: CaseFormulation;
}) {
  const formulaFields = formulationPrimer.fields.slice(0, 4);
  const caseValues: Record<string, string | undefined> = {
    decision_variables: caseFormulation?.decisionVariables,
    variable_domain: caseFormulation?.variableDomain,
    objective: caseFormulation?.objective,
    constraints: caseFormulation?.constraints,
  };
  return (
    <section aria-labelledby="optimization-problem-primer-title" className="problem-primer">
      <header className="problem-primer-header">
        <p className="problem-primer-eyebrow">Formulation / 共通のものさし</p>
        <h2 id="optimization-problem-primer-title">
          {caseFormulation ? "このケースを定式化すると" : "現実の問題を、この形にそろえる"}
        </h2>
        <p>この3つをそろえてから、手法を選びます。</p>
      </header>

      <div className="problem-primer-main">
        <div className="problem-primer-formula">
          <div aria-label={formulationPrimer.formula_aria_label_ja} className="problem-primer-equation" role="img">
            <span>minimize</span><strong>f(x)</strong><small>x ∈ X</small>
          </div>
          <p><span>subject to / 制約</span><strong>gᵢ(x) ≤ 0　hⱼ(x) = 0</strong></p>
          <small>最大化（maximize）の場合は、目的の向きを明記します。</small>
        </div>

        <div className="problem-primer-terms">
          {formulaFields.map((field) => (
            <article key={field.field_id}>
              <code>{field.symbol}</code>
              <div>
                <strong>{field.label_ja} <small>({field.label_en})</small></strong>
                <p>{caseValues[field.field_id] ? <span dangerouslySetInnerHTML={{ __html: caseValues[field.field_id] ?? "" }} /> : field.beginner_description}</p>
              </div>
            </article>
          ))}
        </div>
      </div>

      <details className="problem-primer-glossary">
        <summary>用語の意味を確認する</summary>
        {formulationPrimer.terminology_groups.map((group) => (
          <section key={group.group_id}>
            <h3>{group.title_ja}</h3>
            <dl>
              {group.term_ids.map((termId) => termById.get(termId)).filter((term): term is PrimerTerm => term !== undefined).map((term) => (
                <div id={`term-${term.term_id}`} key={term.term_id}>
                  <dt>{term.term_ja} <small>({term.term_en})</small></dt>
                  <dd>{term.definition}<span>混同注意: {term.common_confusion}</span></dd>
                </div>
              ))}
            </dl>
          </section>
        ))}
      </details>
    </section>
  );
}

export function OptimizationProblemPrimerDisclosure() {
  return (
    <details className="problem-primer-disclosure">
      <summary>
        <span>共通の定式化を確認</span>
        <small>変数・目的・制約</small>
      </summary>
      <OptimizationProblemPrimer />
    </details>
  );
}

export function CanonicalTermReferences({ questionIds }: { questionIds: string[] }) {
  const terms = [...new Map(
    questionIds.flatMap(termsForQuestion).map((term) => [term.term_id, term]),
  ).values()];
  if (terms.length === 0) return null;
  return (
    <details className="canonical-term-references">
      <summary>この項目の用語を確認</summary>
      <dl>{terms.map((term) => <div key={term.term_id}><dt>{term.term_ja} <small>({term.term_en})</small></dt><dd>{term.definition}</dd></div>)}</dl>
    </details>
  );
}
