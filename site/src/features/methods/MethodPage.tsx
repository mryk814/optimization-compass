import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { parseGalleryIndex, type GalleryCase } from "../../contracts/gallery";
import { parseViewSpec, type ViewSpec } from "../../contracts/viewspec";
import { siteBaseUrl } from "../../data/base-url";
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
  const [relatedCases, setRelatedCases] = useState<GalleryCase[]>([]);
  const [error, setError] = useState<Error>();
  useEffect(() => {
    let active = true;
    setView(undefined);
    setRelatedCases([]);
    setError(undefined);
    void loadMethod(methodId).then(
      (loaded) => { if (active) { setView(loaded.view); setRelatedCases(loaded.relatedCases); } },
      (caught: unknown) => { if (active) setError(caught instanceof Error ? caught : new Error(String(caught))); },
    );
    return () => { active = false; };
  }, [methodId]);
  if (error instanceof EntityNotFoundError) return <NotFoundPage detail={error.message} />;
  const method = view?.entities.find(
    (entity) => entity.entity_type === "method" && entity.entity_id === methodId,
  );
  const sourceIds = method?.source_ids ?? [
    ...new Set(relatedCases.flatMap((item) => item.source_ids)),
  ];
  return (
    <section className="page-panel method-detail-page">
      <p className="eyebrow">Method</p>
      <h1>{method?.label ?? (relatedCases.length > 0 ? methodId : "手法を読み込み中…")}</h1>
      {method ? (
        <p className="content-lead">{method.summary}</p>
      ) : relatedCases.length > 0 ? (
        <p className="content-lead">実問題の候補として掲載されている手法です。関連ケースから適用条件を確認できます。</p>
      ) : null}
      {method?.label_en && <p lang="en">{method.label_en}</p>}
      <p className="route-parameter">Method ID: <strong>{methodId}</strong></p>
      {error && <p role="alert">{error.message}</p>}
      {view && <MapAction methodId={methodId} view={view} />}
      {methodId === "M_NELDER_MEAD" && <Link className="text-link" to="/theater/nelder-mead">Method Theaterを開く</Link>}
      {relatedCases.length > 0 && <section className="method-related-cases"><h2>関連ケース</h2><ul>{relatedCases.map((item) => <li key={item.case_id}><Link to={`/gallery/${item.case_id}`}>{item.title_ja}</Link><span>{item.question}</span></li>)}</ul></section>}
      {sourceIds.length > 0 && <small>Sources: {sourceIds.join(", ")}</small>}
    </section>
  );
}

async function loadMethod(methodId: string): Promise<{ view: ViewSpec; relatedCases: GalleryCase[] }> {
  const viewResponse = await fetch(`${siteBaseUrl()}data/views/problem-structure.json`);
  if (!viewResponse.ok) throw new Error(`ViewSpec request failed (${viewResponse.status}).`);
  const view = parseViewSpec(await viewResponse.json());
  const methodExists = view.entities.some(
    (entity) => entity.entity_type === "method" && entity.entity_id === methodId,
  );
  if (methodExists) return { view, relatedCases: [] };

  const galleryResponse = await fetch(`${siteBaseUrl()}data/gallery.json`);
  if (!galleryResponse.ok) throw new Error(`Gallery request failed (${galleryResponse.status}).`);
  const gallery = parseGalleryIndex(await galleryResponse.json());
  const relatedCases = gallery.cases.filter(
    (item) => item.candidate_method_ids.includes(methodId)
      || item.excluded_methods.some((entry) => entry.method_id === methodId),
  );
  if (relatedCases.length === 0) throw new EntityNotFoundError("手法ID", methodId);
  return { view, relatedCases };
}
