import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import {
  findLearningEntity,
  type LearningEdge,
  type LearningEntity,
  type LearningEntityType,
  type LearningGraphIndex,
} from "../../contracts/learning-graph";
import { loadLearningGraph } from "./learning-data";

export function LearningRelations({ entityType, entityId }: { entityType: LearningEntityType; entityId: string }) {
  const [index, setIndex] = useState<LearningGraphIndex>();
  const [error, setError] = useState<Error>();
  useEffect(() => {
    const controller = new AbortController();
    void loadLearningGraph(controller.signal).then(setIndex, (caught: unknown) => {
      if (!controller.signal.aborted) setError(caught instanceof Error ? caught : new Error(String(caught)));
    });
    return () => controller.abort();
  }, []);
  const groups = useMemo(() => index ? relationGroups(index, entityType, entityId) : [], [index, entityType, entityId]);
  if (error) return null;
  if (groups.length === 0) return null;
  return (
    <section aria-label="学習グラフ" className="learning-relations">
      <h2>学習経路 (Learning path)</h2>
      <div className="learning-relation-grid">
        {groups.map((group) => (
          <section key={group.title}>
            <h3>{group.title}</h3>
            <ul>{group.items.map(({ edge, entity }) => (
              <li key={edge.edge_id}>
                <Destination entity={entity} />
                <span>{edge.rationale}</span>
              </li>
            ))}</ul>
          </section>
        ))}
      </div>
    </section>
  );
}

type RelationItem = { edge: LearningEdge; entity: LearningEntity };

function relationGroups(index: LearningGraphIndex, entityType: LearningEntityType, entityId: string) {
  const current = `${entityType}:${entityId}`;
  const incoming = index.edges.filter((edge) => `${edge.target_type}:${edge.target_id}` === current);
  const outgoing = index.edges.filter((edge) => `${edge.source_type}:${edge.source_id}` === current);
  const resolve = (edge: LearningEdge, incomingEdge: boolean): RelationItem | undefined => {
    const entity = incomingEdge
      ? findLearningEntity(index, edge.source_type, edge.source_id)
      : findLearningEntity(index, edge.target_type, edge.target_id);
    return entity ? { edge, entity } : undefined;
  };
  const groups = [
    { title: "前提", items: incoming.filter((edge) => edge.relation === "prerequisite_for").map((edge) => resolve(edge, true)) },
    { title: "次に見る", items: outgoing.filter((edge) => ["prerequisite_for", "next_step", "see_visualization", "see_comparison", "see_case", "implemented_by"].includes(edge.relation)).map((edge) => resolve(edge, false)) },
    { title: "関連・対比", items: outgoing.filter((edge) => ["contrast_with", "special_case_of", "generalizes", "applied_in", "common_misconception_for"].includes(edge.relation)).map((edge) => resolve(edge, false)) },
  ];
  return groups.map((group) => ({ ...group, items: group.items.filter((item): item is RelationItem => Boolean(item)) })).filter((group) => group.items.length > 0);
}

function Destination({ entity }: { entity: LearningEntity }) {
  if (entity.canonical_url) return <Link to={entity.canonical_url}>{entity.label_ja}</Link>;
  if (entity.external_url) return <a href={entity.external_url} rel="noreferrer" target="_blank">{entity.label_ja}</a>;
  return <strong>{entity.label_ja}</strong>;
}
