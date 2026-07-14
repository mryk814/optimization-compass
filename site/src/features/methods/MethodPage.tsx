import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { parseViewSpec, type ViewSpec } from "../../contracts/viewspec";
import type { AtlasCompatibilityCatalog } from "../../state/atlas-state";
import { useAtlasNavigation } from "../../state/atlas-navigation";
import { useAtlasState } from "../../state/useAtlasState";
import { resolveRelatedNodeId } from "../map/map-state";
import { EntityNotFoundError, NotFoundPage } from "../navigation/NotFoundPage";

function catalogFromView(view: ViewSpec): AtlasCompatibilityCatalog {
  return {
    datasetVersion: view.dataset_version,
    viewId: view.view_id,
    viewVersion: view.version,
    nodeIds: new Set(view.nodes.map((node) => node.node_id)),
    questions: Object.fromEntries(
      view.nodes.flatMap((node) =>
        node.question_id && node.answer_type
          ? [[node.question_id, { answerType: node.answer_type, allowedAnswers: node.allowed_answers }]]
          : [],
      ),
    ),
  };
}

function MapAction({ methodId, view }: { methodId: string; view: ViewSpec }) {
  const atlas = useAtlasState(useMemo(() => catalogFromView(view), [view]));
  const atlasNavigation = useAtlasNavigation();
  const nodeId = resolveRelatedNodeId(view.nodes, "method", methodId);
  if (atlas.error) return <p role="alert">{atlas.error.message}</p>;
  return (
    <>
      <button
        disabled={!nodeId}
        onClick={() => {
          if (!nodeId) return;
          atlasNavigation.navigateWithState("/map", { ...atlas.state, selectedNodeId: nodeId });
        }}
        type="button"
      >
        地図上で見る
      </button>
      {atlasNavigation.error && <p role="alert">{atlasNavigation.error.message}</p>}
    </>
  );
}

export function MethodPage() {
  const { methodId = "" } = useParams();
  const [view, setView] = useState<ViewSpec>();
  const [error, setError] = useState<Error>();
  useEffect(() => {
    let active = true;
    setView(undefined);
    setError(undefined);
    const baseUrl = (import.meta as ImportMeta & { env: { BASE_URL: string } }).env.BASE_URL;
    void fetch(`${baseUrl}data/views/problem-structure.json`).then(async (response) => {
      if (!response.ok) throw new Error(`ViewSpec request failed (${response.status}).`);
      const next = parseViewSpec(await response.json());
      const methodExists = next.entities.some(
        (entity) => entity.entity_type === "method" && entity.entity_id === methodId,
      );
      if (!methodExists) throw new EntityNotFoundError("手法ID", methodId);
      return next;
    }).then(
      (next) => { if (active) setView(next); },
      (caught: unknown) => { if (active) setError(caught instanceof Error ? caught : new Error(String(caught))); },
    );
    return () => { active = false; };
  }, [methodId]);
  if (error instanceof EntityNotFoundError) return <NotFoundPage detail={error.message} />;
  const method = view?.entities.find(
    (entity) => entity.entity_type === "method" && entity.entity_id === methodId,
  );
  return (
    <section className="page-panel method-detail-page">
      <p className="eyebrow">Method</p>
      <h1>{method?.label ?? "手法を読み込み中…"}</h1>
      {method && <p className="content-lead">{method.summary}</p>}
      {method?.label_en && <p lang="en">{method.label_en}</p>}
      <p className="route-parameter">Method ID: <strong>{methodId}</strong></p>
      {error && <p role="alert">{error.message}</p>}
      {view && <MapAction methodId={methodId} view={view} />}
      {methodId === "M_NELDER_MEAD" && <Link className="text-link" to="/theater/nelder-mead">Method Theaterを開く</Link>}
      {method && method.source_ids.length > 0 && <small>Sources: {method.source_ids.join(", ")}</small>}
    </section>
  );
}
