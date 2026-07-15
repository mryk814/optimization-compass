import type { SiteData, SitePredicate } from "../../contracts/site-data";

function expectedValue(predicate: SitePredicate, data: SiteData): string {
  const values = Array.isArray(predicate.value) ? predicate.value : [predicate.value];
  const labels = new Map(
    [
      ...data.feature_values
        .filter((item) => item.feature_id === predicate.feature_id)
        .map((item) => [item.value_code, item.label_ja] as const),
      ...data.questions
        .filter((item) => item.mapped_feature_id === predicate.feature_id)
        .flatMap((item) => item.choices.map((choice) => [choice.value, choice.label_ja] as const)),
    ],
  );
  return values.map((value) => labels.get(String(value)) ?? String(value)).join(" / ");
}

export function MethodPredicates({ data, methodId }: { data: SiteData; methodId: string }) {
  const predicates = data.predicates.filter(
    (predicate) => predicate.subject_type === "method" && predicate.subject_id === methodId,
  );
  if (predicates.length === 0) return null;
  const features = new Map(data.features.map((feature) => [feature.feature_id, feature]));
  const coverage = data.predicate_coverage.find(
    (item) => item.subject_type === "method" && item.subject_id === methodId,
  );
  return (
    <section aria-label="機械評価できる前提" className="method-predicates">
      <div className="method-predicate-heading">
        <h2>機械評価できる前提</h2>
        {coverage && <span>{coverage.status}</span>}
      </div>
      <ul>
        {predicates.map((predicate) => (
          <li key={predicate.predicate_id}>
            <strong>{features.get(predicate.feature_id)?.name_ja ?? predicate.feature_id}</strong>
            <span><code>{predicate.operator}</code> {expectedValue(predicate, data)}</span>
            <small>{predicate.predicate_kind} · confidence {predicate.confidence}</small>
          </li>
        ))}
      </ul>
      {coverage && (
        <p>
          {coverage.status === "complete"
            ? "推薦で使う前提・非対応条件を移行済みです。"
            : "一部を移行済みです。未移行条件はrelease reportで追跡しています。"}
        </p>
      )}
    </section>
  );
}
