import { entityKey, safeHttpUrl, type MapModel, type ViewEntity } from "../../contracts/viewspec";
import { Link } from "react-router-dom";
import { useEntityLinks } from "../../state/entity-links";
import { ancestorIds } from "./map-state";
import { THEATER_ROUTES } from "../theater/theater-routes";
import type { SiteData } from "../../contracts/site-data";
import { MethodPredicates } from "../methods/MethodPredicates";

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
        地図から項目を選択してください。
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

  return (
    <article aria-live="polite" className="map-detail-card">
      <p className="map-breadcrumb">{breadcrumbNodes.map((node) => node.label || node.node_id).join(" / ")}</p>
      <div className="map-detail-heading">
        <h2>{selected.label || selected.node_id}</h2>
        <span>{selected.node_type}</span>
      </div>
      <p className="map-detail-summary">{selected.summary || "概要は登録されていません。"}</p>
      {[...methodIds].map((methodId) => <MethodPredicates data={data} key={methodId} methodId={methodId} />)}
      {hasBayesianOptimization && <section className="bo-route-card"><strong>点選択を可視化</strong><p>surrogateの予測平均・不確実性・Expected Improvementを同じ図で確認します。</p><Link to={THEATER_ROUTES.bayesianOptimization}>Bayesian Optimization Theaterへ</Link></section>}

      {children.length > 0 && (
        <section className="map-detail-section">
          <h3>次の項目</h3>
          <ul className="map-child-preview">
            {children.map((child) => <li key={child.node_id}>{child.label || child.node_id}</li>)}
          </ul>
        </section>
      )}

      {selected.answer_bindings.length > 0 && (
        <section className="map-detail-section">
          <h3>回答の対応</h3>
          <ul className="map-binding-list">
            {selected.answer_bindings.map((binding) => (
              <li key={`${binding.question_id}:${binding.answer_value}`}>
                <code>{binding.question_id} = {binding.answer_value}</code>
              </li>
            ))}
          </ul>
          <p className="map-binding-note">探索中の選択です。診断回答は変更していません。</p>
          {onContinueDiagnosis && (
            <button className="map-action-button" onClick={onContinueDiagnosis} type="button">
              この条件で診断を続ける
            </button>
          )}
        </section>
      )}

      {[...grouped.entries()].map(([type, entities]) => (
        <section className="map-detail-section" key={type}>
          <h3>{entityTypeLabels[type] ?? `${type}（未分類）`}</h3>
          <ul className="map-entity-list">
            {entities.map((entity) => <EntityItem entity={entity} key={entity.entity_id} />)}
          </ul>
        </section>
      ))}

      {missingReferences.length > 0 && (
        <section className="map-detail-section map-reference-warning">
          <h3>参照エラー</h3>
          <p>{missingReferences.join("、")}</p>
        </section>
      )}
    </article>
  );
}
