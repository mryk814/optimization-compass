import { useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { parseSiteManifest } from "../../contracts/manifest";
import { buildMapModel, parseViewSpec, type MapModel, type ViewSpec } from "../../contracts/viewspec";
import { parseSiteData, type SiteData } from "../../contracts/site-data";
import { encodeAtlasState, type AtlasCompatibilityCatalog, type AtlasStateV1 } from "../../state/atlas-state";
import { useAtlasNavigation } from "../../state/atlas-navigation";
import { useAtlasState } from "../../state/useAtlasState";
import { OptimizationProblemPrimerDisclosure } from "../../components/OptimizationProblemPrimer";
import { MapDetail } from "./MapDetail";
import { ancestorIds, applyAnswerBindings, matchingBindingNodeIds } from "./map-state";
import { MapTree } from "./MapTree";

type LoadState =
  | { status: "loading" }
  | { status: "error"; error: Error }
  | { status: "ready"; view: ViewSpec; views: ViewSpec[]; model: MapModel; data: SiteData };

function catalogFromView(view: ViewSpec, data: SiteData): AtlasCompatibilityCatalog {
  const questions: AtlasCompatibilityCatalog["questions"] = Object.fromEntries([
    ...data.questions.map((question) => [question.question_id, {
      answerType: question.answer_type,
      allowedAnswers: question.allowed_answers,
    }] as const),
    ...view.nodes.flatMap((node) => node.question_id && node.answer_type ? [[node.question_id, {
      answerType: node.answer_type,
      allowedAnswers: node.allowed_answers,
    }] as const] : []),
  ]);
  return {
    datasetVersion: view.dataset_version,
    viewId: view.view_id,
    viewVersion: view.version,
    nodeIds: new Set(view.nodes.map((node) => node.node_id)),
    questions,
  };
}

function Diagnostics({ model }: { model: MapModel }) {
  if (model.diagnostics.length === 0) return null;
  return (
    <section className="map-diagnostics" role="status">
      <h2>データの確認 {model.diagnostics.length}件</h2>
      <ul>{model.diagnostics.map((item, index) => <li key={`${item.kind}:${item.subjectId}:${index}`}>{item.message}</li>)}</ul>
    </section>
  );
}

function MapLegend() {
  return (
    <details className="map-legend">
      <summary>地図の読み方</summary>
      <ul>
        <li><span aria-hidden="true" className="map-legend-swatch map-legend-swatch-root" />入口: 問題構造の起点</li>
        <li><span aria-hidden="true" className="map-legend-swatch map-legend-swatch-current" />現在地: キーボード操作や「現在地へ」で移動する項目</li>
        <li><span aria-hidden="true" className="map-legend-swatch map-legend-swatch-selected" />選択経路: 詳細パネルに表示中の項目と親</li>
        <li><span aria-hidden="true" className="map-legend-swatch map-legend-swatch-related" />関連候補: 診断回答に合う候補</li>
      </ul>
      <p className="map-view-help" role="note">
        倍率は文字の大きさです。地図は縦横にスクロールでき、「現在地へ」で選択中の項目に戻れます。
      </p>
    </details>
  );
}

function focusInView(currentView: ViewSpec, targetView: ViewSpec, state: AtlasStateV1): string | undefined {
  const selectedId = state.selectedNodeId;
  if (selectedId && targetView.nodes.some((node) => node.node_id === selectedId)) return selectedId;
  const selected = selectedId ? currentView.nodes.find((node) => node.node_id === selectedId) : undefined;
  const references = selected?.related_entities ?? [];
  for (const entityType of targetView.focus_fallback_entity_types) {
    for (const reference of references.filter((item) => item.entity_type === entityType)) {
      const match = targetView.nodes.find((node) => node.related_entities.some(
        (item) => item.entity_type === reference.entity_type && item.entity_id === reference.entity_id,
      ));
      if (match) return match.node_id;
    }
  }
  return targetView.root_node_ids[0];
}

function LoadedMap({ view, views, model, data }: { view: ViewSpec; views: ViewSpec[]; model: MapModel; data: SiteData }) {
  const catalog = useMemo(() => catalogFromView(view, data), [data, view]);
  const atlas = useAtlasState(catalog);
  const atlasNavigation = useAtlasNavigation();
  const location = useLocation();
  const navigate = useNavigate();
  const answerMatchIds = useMemo(
    () => new Set(matchingBindingNodeIds(view.nodes, atlas.state)),
    [atlas.state, view.nodes],
  );
  const [expanded, setExpanded] = useState<Set<string>>(
    () => new Set(view.nodes.filter((node) => !node.default_collapsed).map((node) => node.node_id)),
  );
  const [focusedId, setFocusedId] = useState<string | undefined>(
    atlas.state.selectedNodeId ?? model.rootNodes[0]?.node_id,
  );
  const [zoom, setZoom] = useState(100);
  const [activePane, setActivePane] = useState<"map" | "detail">("map");
  const [focusRequest, setFocusRequest] = useState<{ nodeId: string; sequence: number }>();
  const focusSequence = useRef(0);
  const nodeRefs = useRef(new Map<string, HTMLElement>());

  useEffect(() => {
    if (answerMatchIds.size === 0) return;
    setExpanded((current) => {
      const next = new Set(current);
      answerMatchIds.forEach((nodeId) => {
        ancestorIds(nodeId, model.parentByChild).forEach((ancestorId) => next.add(ancestorId));
      });
      return next;
    });
    if (!atlas.state.selectedNodeId) {
      const firstMatch = answerMatchIds.values().next().value as string | undefined;
      if (firstMatch) {
        atlas.setState((current) => ({ ...current, selectedNodeId: firstMatch }), { replace: true });
      }
    }
  }, [answerMatchIds, atlas.setState, atlas.state.selectedNodeId, model.parentByChild]);

  useEffect(() => {
    const selectedId = atlas.state.selectedNodeId;
    if (!selectedId) return;
    setFocusedId(selectedId);
    setExpanded((current) => {
      const next = new Set(current);
      ancestorIds(selectedId, model.parentByChild).forEach((nodeId) => next.add(nodeId));
      return next;
    });
  }, [atlas.state.selectedNodeId, model.parentByChild]);

  useEffect(() => {
    if (!focusRequest || activePane !== "map") return;
    const frame = requestAnimationFrame(() => {
      const element = nodeRefs.current.get(focusRequest.nodeId);
      element?.focus();
      element?.scrollIntoView({ block: "center", inline: "nearest" });
      setFocusRequest((current) =>
        current?.sequence === focusRequest.sequence ? undefined : current,
      );
    });
    return () => cancelAnimationFrame(frame);
  }, [activePane, expanded, focusRequest]);

  const toggle = (nodeId: string) => {
    setExpanded((current) => {
      const next = new Set(current);
      if (next.has(nodeId)) next.delete(nodeId);
      else next.add(nodeId);
      return next;
    });
  };
  const select = (nodeId: string) => {
    setFocusedId(nodeId);
    atlas.setState((current) => ({ ...current, selectedNodeId: nodeId }));
  };
  const focusCurrent = () => {
    const selectedId = atlas.state.selectedNodeId;
    if (!selectedId) return;
    setActivePane("map");
    setExpanded((current) => {
      const next = new Set(current);
      ancestorIds(selectedId, model.parentByChild).forEach((nodeId) => next.add(nodeId));
      return next;
    });
    setFocusedId(selectedId);
    focusSequence.current += 1;
    setFocusRequest({ nodeId: selectedId, sequence: focusSequence.current });
  };
  const continueDiagnosis = () => {
    const selected = atlas.state.selectedNodeId
      ? model.nodeById.get(atlas.state.selectedNodeId)
      : undefined;
    if (!selected || selected.answer_bindings.length === 0) return;
    const next = applyAnswerBindings(atlas.state, selected.answer_bindings, catalog);
    atlasNavigation.navigateWithState("/diagnose", next);
  };
  const switchView = (viewId: string) => {
    const target = views.find((candidate) => candidate.view_id === viewId);
    if (!target || target.view_id === view.view_id) return;
    const selectedNodeId = focusInView(view, target, atlas.state);
    const next: AtlasStateV1 = {
      ...atlas.state,
      datasetVersion: target.dataset_version,
      viewId: target.view_id,
      viewVersion: target.version,
    };
    if (selectedNodeId) next.selectedNodeId = selectedNodeId;
    else delete next.selectedNodeId;
    const params = new URLSearchParams(location.search);
    params.set("view", target.view_id);
    params.set("state", encodeAtlasState(next));
    navigate({ pathname: location.pathname, search: `?${params.toString()}` });
  };

  if (atlas.error) {
    return (
      <section className="map-state-panel" role="alert">
        <h2>URLの状態を復元できませんでした</h2>
        <p>{atlas.error.message}</p>
        <button className="map-action-button" onClick={atlas.reset} type="button">状態をリセット</button>
      </section>
    );
  }

  if (model.rootNodes.length === 0) {
    return (
      <>
        <Diagnostics model={model} />
        <p className="map-state-panel">表示する項目がありません。</p>
      </>
    );
  }

  return (
    <>
      {atlas.warnings.length > 0 && (
        <div className="map-warning-list" role="status">
          {atlas.warnings.map((warning) => <p key={warning}>{warning}</p>)}
        </div>
      )}
      {atlasNavigation.error && <p className="map-state-panel" role="alert">{atlasNavigation.error.message}</p>}
      <Diagnostics model={model} />
      <section aria-labelledby="map-reading-question" className="map-reading-question">
        <p className="eyebrow">この図が答える問い</p>
        <h2 id="map-reading-question">この条件は、どの問題構造に位置づく？</h2>
        <p>左で構造をたどり、選んだ項目の意味と次の操作を右で確認します。</p>
      </section>
      <section className="map-view-selector" aria-label="表示の種類">
        <label htmlFor="semantic-view">表示</label>
        <select id="semantic-view" onChange={(event) => switchView(event.target.value)} value={view.view_id}>
          {views.map((candidate, index) => <option key={`${candidate.view_id}:${index}`} value={candidate.view_id}>{candidate.title}</option>)}
        </select>
        <details className="map-view-context">
          <summary>表示の説明</summary>
          <div>
            <strong>{view.description}</strong>
            <span>注意: {view.limitations}</span>
          </div>
        </details>
      </section>
      <div aria-label="表示するペイン" className="map-pane-switch" role="group">
        <button aria-pressed={activePane === "map"} onClick={() => setActivePane("map")} type="button">地図</button>
        <button aria-pressed={activePane === "detail"} onClick={() => setActivePane("detail")} type="button">詳細</button>
      </div>
      <div className="map-utility-row">
        <MapLegend />
        <div className="map-toolbar" role="toolbar" aria-label="地図表示">
          <button aria-label="縮小" disabled={zoom <= 80} onClick={() => setZoom((value) => Math.max(80, value - 10))} type="button">−</button>
          <output aria-label="表示倍率">{zoom}%</output>
          <button aria-label="拡大" disabled={zoom >= 140} onClick={() => setZoom((value) => Math.min(140, value + 10))} type="button">＋</button>
          <button aria-label="倍率をリセット" onClick={() => setZoom(100)} type="button">リセット</button>
          <button disabled={!atlas.state.selectedNodeId} onClick={focusCurrent} type="button">現在地へ</button>
        </div>
      </div>
      <div className="map-workspace">
        <section className="map-tree-pane" data-active={activePane === "map"} data-testid="map-tree-pane">
          <MapTree
            answerMatchIds={answerMatchIds}
            expanded={expanded}
            focusedId={focusedId}
            model={model}
            nodeRefs={nodeRefs}
            onFocusChange={setFocusedId}
            onSelect={select}
            onToggle={toggle}
            selectedId={atlas.state.selectedNodeId}
            zoom={zoom}
          />
        </section>
        <aside className="map-detail-pane" data-active={activePane === "detail"} data-testid="map-detail-pane">
          <MapDetail
            data={data}
            model={model}
            onContinueDiagnosis={continueDiagnosis}
            selectedId={atlas.state.selectedNodeId}
          />
        </aside>
      </div>
    </>
  );
}

export function MapPage() {
  const [loadState, setLoadState] = useState<LoadState>({ status: "loading" });
  const location = useLocation();
  const requestedViewId = useMemo(
    () => new URLSearchParams(location.search).get("view") ?? "problem-structure",
    [location.search],
  );

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const baseUrl = (import.meta as ImportMeta & { env: { BASE_URL: string } }).env.BASE_URL;
        const manifestResponse = await fetch(`${baseUrl}data/manifest.json`);
        if (!manifestResponse.ok) throw new Error(`Manifest request failed (${manifestResponse.status}).`);
        const manifest = parseSiteManifest(await manifestResponse.json());
        const [viewResponses, dataResponse] = await Promise.all([
          Promise.all(manifest.views.map((item) => fetch(`${baseUrl}data/${item.path}`))),
          fetch(`${baseUrl}data/${manifest.recommendation.path}`),
        ]);
        const requestedIndex = Math.max(
          0,
          manifest.views.findIndex((item) => item.view_id === requestedViewId),
        );
        if (!viewResponses[requestedIndex]?.ok) {
          throw new Error(`ViewSpec request failed (${viewResponses[requestedIndex]?.status ?? "unknown"}).`);
        }
        if (!dataResponse.ok) throw new Error(`SiteData request failed (${dataResponse.status}).`);
        const parsedViews = await Promise.all(viewResponses.map(async (response) => (
          response.ok ? parseViewSpec(await response.json()) : undefined
        )));
        const views = parsedViews.filter((candidate): candidate is ViewSpec => candidate !== undefined);
        const expectedViewId = manifest.views[requestedIndex]?.view_id;
        const view = views.find((candidate) => candidate.view_id === expectedViewId);
        if (!view) throw new Error("No semantic View artifact could be loaded.");
        const data = parseSiteData(await dataResponse.json(), view.dataset_version);
        if (active) setLoadState({ status: "ready", view, views, model: buildMapModel(view), data });
      } catch (caught) {
        const error = caught instanceof Error ? caught : new Error(String(caught));
        if (active) setLoadState({ status: "error", error });
      }
    };
    void load();
    return () => { active = false; };
  }, [requestedViewId]);

  return (
    <section className="map-page">
      <header className="map-page-header">
        <p className="eyebrow">問題構造の見取り図</p>
        <h1>{loadState.status === "ready" ? loadState.view.title : requestedViewId === "problem-structure" ? "問題構造マップ" : "最適化マップ"}</h1>
        {loadState.status === "ready" && <p>{loadState.view.description}</p>}
      </header>
      <OptimizationProblemPrimerDisclosure />
      {loadState.status === "loading" && <p className="map-state-panel" role="status">地図を読み込み中…</p>}
      {loadState.status === "error" && (
        <section className="map-state-panel" role="alert">
          <h2>地図データを読み込めませんでした</h2>
          <p>{loadState.error.message}</p>
        </section>
      )}
      {loadState.status === "ready" && <LoadedMap key={loadState.view.view_id} data={loadState.data} model={loadState.model} view={loadState.view} views={loadState.views} />}
    </section>
  );
}
