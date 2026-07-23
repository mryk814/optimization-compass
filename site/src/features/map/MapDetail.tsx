import { entityKey, safeHttpUrl, type MapModel, type ViewEntity } from "../../contracts/viewspec";
import { Link } from "react-router-dom";
import { useEntityLinks } from "../../state/entity-links";
import { ancestorIds } from "./map-state";
import { THEATER_ROUTES } from "../theater/theater-routes";
import type { SiteData } from "../../contracts/site-data";
import { MethodPredicates } from "../methods/MethodPredicates";
import { CanonicalTermReferences } from "../../components/OptimizationProblemPrimer";

interface MapDetailProps {
  model: MapModel;
  data: SiteData;
  selectedId?: string;
  onContinueDiagnosis?(): void;
}

const entityTypeLabels: Record<string, string> = {
  method: "関連手法",
  problem: "問題型",
  feature: "特徴",
  alternative: "代替解法",
  source: "根拠",
};

function EntityItem({ entity }: { entity: ViewEntity }) {
  const links = useEntityLinks();
  const safeUrl = safeHttpUrl(entity.url);
  const canonical = links.status === "ready"
    ? links.index.entities.find((candidate) => candidate.entity_type === entity.entity_type && candidate.entity_id === entity.entity_id)?.canonical_url
    : undefined;
  return (
    <li className="map-entity-item">
      {canonical ? (
        <Link to={canonical}>{entity.label || entity.entity_id}</Link>
      ) : safeUrl ? (
        <a href={safeUrl} rel="noreferrer" target="_blank">{entity.label || entity.entity_id}</a>
      ) : (
        <strong>{entity.label || entity.entity_id}</strong>
      )}
      {entity.summary && <span>{entity.summary}</span>}
      <code>{entity.entity_id}</code>
    </li>
  );
}

export function MapDetail({ model, data, selectedId, onContinueDiagnosis }: MapDetailProps) {
  const selected = selectedId ? model.nodeById.get(selectedId) : undefined;
  if (!selected) {
    return (
      <div aria-live="polite" className="map-detail-empty">
        地図から項目を選ぶと、ここに詳細を表示します。
      </div>
    );
  }

  const breadcrumbNodes = [...ancestorIds(selected.node_id, model.parentByChild), selected.node_id]
    .map((nodeId) => model.nodeById.get(nodeId))
    .filter((node): node is NonNullable<typeof node> => node !== undefined);
  const children = model.childrenByParent.get(selected.node_id) ?? [];
  const grouped = new Map<string, ViewEntity[]>();
  const missingReferences: string[] = [];
  for (const reference of selected.related_entities) {
    const entity = model.entityByKey.get(entityKey(reference.entity_type, reference.entity_id));
    if (!entity) {
      missingReferences.push(`${reference.entity_type}:${reference.entity_id}`);
      continue;
    }
    const items = grouped.get(reference.entity_type) ?? [];
    items.push(entity);
    grouped.set(reference.entity_type, items);
  }
  const sources = selected.source_ids.flatMap((sourceId) => {
    const source = model.entityByKey.get(entityKey("source", sourceId));
    if (!source) {
      missingReferences.push(`source:${sourceId}`);
      return [];
    }
    return [source];
  });
  if (sources.length > 0) grouped.set("source", sources);
  const hasBayesianOptimization = selected.related_entities.some(
    (reference) => reference.entity_type === "method" && reference.entity_id === "M_BAYESIAN_OPT_GP",
  );
  const methodIds = new Set(
    selected.related_entities
      .filter((reference) => reference.entity_type === "method")
      .map((reference) => reference.entity_id),
  );
  if (selected.node_id.startsWith("method:")) methodIds.add(selected.node_id.slice("method:".length));
  const learningSliceLinks: { label: string; to: string }[] = [];
  if (methodIds.has("M_SLSQP")) learningSliceLinks.push({ label: "feasible regionで制約違反を確認", to: THEATER_ROUTES.constrainedContinuous });
  if (methodIds.has("M_NSGA_II") || methodIds.has("M_WEIGHTED_SUM")) learningSliceLinks.push({ label: "Pareto frontでトレードオフを確認", to: THEATER_ROUTES.multiObjective });

  return (
    <article aria-live="polite" className="map-detail-card">
      <p className="map-breadcrumb">{breadcrumbNodes.map((node) => node.label || node.node_id).join(" / ")}</p>
      <div className="map-detail-heading">
        <h2>{selected.label || selected.node_id}</h2>
        <span>{selected.node_type}</span>
      </div>
      <p className="map-detail-summary">{selected.summary || "概要は登録されていません。"}</p>
      <CanonicalTermReferences questionIds={selected.answer_bindings.map((binding) => binding.question_id)} />
      {[...methodIds].map((methodId) => <MethodPredicates data={data} key={methodId} methodId={methodId} />)}
      {hasBayesianOptimization && <section className="bo-route-card"><strong>点の選び方を可視化</strong><p>予測モデル（surrogate）の予測平均・不確実性・Expected Improvementを同じ図で確認します。</p><Link to={THEATER_ROUTES.bayesianOptimization}>Bayesian Optimization Theaterへ</Link></section>}
      {learningSliceLinks.map((item) => <section className="bo-route-card" key={item.to}><strong>学習用の可視化</strong><p>問題設定と表示形式に沿って可視化します。</p><Link to={item.to}>{item.label}</Link></section>)}

      {children.length > 0 && (
        <details className="map-detail-section map-detail-disclosure">
          <summary>関連項目 <span>{children.length}</span></summary>
          <ul className="map-child-preview">
            {children.map((child) => <li key={child.node_id}>{child.label || child.node_id}</li>)}
          </ul>
        </details>
      )}

      {selected.answer_bindings.length > 0 && (
        <section className="map-detail-section">
          {onContinueDiagnosis && (
            <button className="map-action-button" onClick={onContinueDiagnosis} type="button">
              この条件で診断する
            </button>
          )}
          <details className="map-binding-details">
            <summary>診断回答との対応を確認</summary>
            <ul className="map-binding-list">
              {selected.answer_bindings.map((binding) => (
                <li key={`${binding.question_id}:${binding.answer_value}`}>
                  <code>{binding.question_id} = {binding.answer_value}</code>
                </li>
              ))}
            </ul>
            <p className="map-binding-note">この条件を診断へ引き継ぎます。ほかの回答は変更しません。</p>
          </details>
        </section>
      )}

      {[...grouped.entries()].map(([type, entities]) => (
        <details className="map-detail-section map-detail-disclosure" key={type}>
          <summary>{entityTypeLabels[type] ?? `${type}（未分類）`} <span>{entities.length}</span></summary>
          <ul className="map-entity-list">
            {entities.map((entity) => <EntityItem entity={entity} key={entity.entity_id} />)}
          </ul>
        </details>
      ))}

      {missingReferences.length > 0 && (
        <section className="map-detail-section map-reference-warning">
          <h3>参照できません</h3>
          <p>{missingReferences.join("、")}</p>
        </section>
      )}
    </article>
  );
}
