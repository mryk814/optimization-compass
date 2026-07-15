import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { parseContentIndex, type AtlasContentPage } from "../../contracts/atlas-content";
import { parseSiteData, type SiteData } from "../../contracts/site-data";
import { findEntity, relatedEntities, type LinkedEntity } from "../../contracts/entity-links";
import { parseViewSpec, type ViewSpec } from "../../contracts/viewspec";
import { parseFailureModeIndex, type FailureModeRecord } from "../../contracts/failure-modes";
import { siteBaseUrl } from "../../data/base-url";
import type { AtlasCompatibilityCatalog } from "../../state/atlas-state";
import { useAtlasNavigation } from "../../state/atlas-navigation";
import { useEntityLinks } from "../../state/entity-links";
import { useAtlasState } from "../../state/useAtlasState";
import { CompiledContent } from "../content/CompiledContent";
import { resolveRelatedNodeId } from "../map/map-state";
import { NotFoundPage } from "../navigation/NotFoundPage";
import { PageOrientation } from "../../components/PageOrientation";
import { MethodPredicates } from "./MethodPredicates";

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
        if (nodeId) atlasNavigation.navigateWithState("/map", { ...atlas.state, selectedNodeId: nodeId });
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
  const links = useEntityLinks();
  const [view, setView] = useState<ViewSpec>();
  const [content, setContent] = useState<AtlasContentPage>();
  const [siteData, setSiteData] = useState<SiteData>();
  const [failureModes, setFailureModes] = useState<FailureModeRecord[]>([]);
  const [loadError, setLoadError] = useState<Error>();
  const method = links.status === "ready" ? findEntity(links.index, "method", methodId) : undefined;
  const learning = links.status === "ready" && method
    ? relatedEntities(links.index, method, "learning")[0]
    : undefined;

  useEffect(() => {
    const controller = new AbortController();
    void fetch(`${siteBaseUrl()}data/views/problem-structure.json`, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error(`ViewSpec request failed (${response.status}).`);
        return parseViewSpec(await response.json());
      }).then(
      setView,
      (caught: unknown) => {
        if (!controller.signal.aborted) setLoadError(caught instanceof Error ? caught : new Error(String(caught)));
      },
    );
    return () => controller.abort();
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    void fetch(`${siteBaseUrl()}data/failure-modes.json`, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error(`Failure modes request failed (${response.status}).`);
        return parseFailureModeIndex(await response.json());
      }).then(
        (index) => setFailureModes(index.failure_modes.filter((failure) =>
          failure.affected_entities.some((entity) => entity.entity_type === "method" && entity.entity_id === methodId))),
        (caught: unknown) => {
          if (!controller.signal.aborted) setLoadError(caught instanceof Error ? caught : new Error(String(caught)));
        },
      );
    return () => controller.abort();
  }, [methodId]);
  useEffect(() => {
    const controller = new AbortController();
    void fetch(`${siteBaseUrl()}data/recommendation/site-data.json`, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error(`SiteData request failed (${response.status}).`);
        return parseSiteData(await response.json());
      }).then(
        setSiteData,
        (caught: unknown) => {
          if (!controller.signal.aborted) setLoadError(caught instanceof Error ? caught : new Error(String(caught)));
        },
      );
    return () => controller.abort();
  }, []);
  useEffect(() => {
    if (!learning) return;
    const controller = new AbortController();
    void fetch(`${siteBaseUrl()}data/content.json`, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error(`Content request failed (${response.status}).`);
        return parseContentIndex(await response.json());
      }).then(
        (index) => setContent(index.pages.find((page) => page.content_id === learning.entity_id)),
        (caught: unknown) => {
          if (!controller.signal.aborted) setLoadError(caught instanceof Error ? caught : new Error(String(caught)));
        },
      );
    return () => controller.abort();
  }, [learning]);

  if (links.status === "error") return <NotFoundPage detail={links.error.message} />;
  if (links.status === "ready" && !method) return <NotFoundPage detail={`手法ID「${methodId}」は登録されていません。`} />;
  const groups = links.status === "ready" && method
    ? {
        visualizations: relatedEntities(links.index, method, "visualization"),
        comparisons: relatedEntities(links.index, method, "comparison"),
        implementations: relatedEntities(links.index, method, "implementation"),
        cases: relatedEntities(links.index, method, "case"),
        sources: relatedEntities(links.index, method, "evidence"),
      }
    : undefined;

  return (
    <section className="page-panel method-detail-page">
      <p className="eyebrow">Method</p>
      <h1>{method?.label ?? "手法を読み込み中…"}</h1>
      {method?.summary && <p className="content-lead">{method.summary}</p>}
      <p className="route-parameter">Method ID: <strong>{methodId}</strong></p>
      <PageOrientation
        limits="教材は手法の考え方と登録済みの前提を説明します。データセットや実装、問題条件によって適否は変わります。"
        next={[{ label: "Mapで関連する問題型を見る", to: "/map" }, { label: "Compareで動きを比べる", to: "/compare" }, { label: "Theaterで一手を再生する", to: "/theater" }]}
        purpose="手法が何を仮定し、どのように動き、どこで使えるかを教材・地図・根拠から確認します。"
        readingSteps={["最初に要約と前提を読み、手法の適用範囲をつかみます。", "教材の手順・可視化・最小例でmechanismを確認します。", "MapやCompareで、問題条件や他手法との関係を照合します。"]}
      />
      {loadError && <p role="alert">{loadError.message}</p>}
      {view && <MapAction methodId={methodId} view={view} />}
      {siteData && <MethodPredicates data={siteData} methodId={methodId} />}
      {failureModes.length > 0 && <MethodFailures failures={failureModes} />}
      {content && (
        <section aria-label="教材" className="method-learning">
          <CompiledContent page={content} />
        </section>
      )}
      {groups && <MethodRelations groups={groups} />}
    </section>
  );
}

function MethodFailures({ failures }: { failures: FailureModeRecord[] }) {
  return (
    <section aria-label="症状・確認・対処" className="method-failures">
      <h2>症状・確認・対処</h2>
      {failures.map((failure) => (
        <article key={failure.failure_mode_id}>
          <h3>{failure.name_ja} <small>{failure.name_en}</small></h3>
          <p>{failure.failure_scope} · {failure.severity} · {failure.recoverability}</p>
          <dl>
            <dt>症状</dt><dd>{failure.symptoms.map((item) => item.description).join(" / ")}</dd>
            <dt>確認</dt><dd>{failure.diagnostics.map((item) => item.check_text).join(" / ")}</dd>
            <dt>対処</dt><dd>{failure.mitigations.map((item) => item.action).join(" / ")}</dd>
          </dl>
        </article>
      ))}
    </section>
  );
}

function MethodRelations({
  groups,
}: {
  groups: Record<"visualizations" | "comparisons" | "implementations" | "cases" | "sources", LinkedEntity[]>;
}) {
  const sections = [
    ["visualizations", "Method Theater / Trace"],
    ["comparisons", "比較"],
    ["implementations", "実装"],
    ["cases", "関連ケース"],
    ["sources", "根拠"],
  ] as const;
  return (
    <div className="method-relation-grid">
      {sections.map(([key, title]) => groups[key].length > 0 && (
        <section className="method-related-cases" key={key}>
          <h2>{title}</h2>
          <ul>{groups[key].map((entity) => <li key={`${entity.entity_type}:${entity.entity_id}`}><EntityDestination entity={entity} /></li>)}</ul>
        </section>
      ))}
    </div>
  );
}

function EntityDestination({ entity }: { entity: LinkedEntity }) {
  if (entity.canonical_url) return <Link to={entity.canonical_url}>{entity.label}</Link>;
  if (entity.external_url) return <a href={entity.external_url} rel="noreferrer" target="_blank">{entity.label}</a>;
  return <span>{entity.label}</span>;
}
