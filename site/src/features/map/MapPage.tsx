import { useEffect, useMemo, useRef, useState } from "react";

import { buildMapModel, parseViewSpec, type MapModel, type ViewSpec } from "../../contracts/viewspec";
import type { AtlasCompatibilityCatalog } from "../../state/atlas-state";
import { useAtlasNavigation } from "../../state/atlas-navigation";
import { useAtlasState } from "../../state/useAtlasState";
import { MapDetail } from "./MapDetail";
import { ancestorIds, applyAnswerBindings, matchingBindingNodeIds } from "./map-state";
import { MapTree } from "./MapTree";

type LoadState =
  | { status: "loading" }
  | { status: "error"; error: Error }
  | { status: "ready"; view: ViewSpec; model: MapModel };

function catalogFromView(view: ViewSpec): AtlasCompatibilityCatalog {
  const questions: AtlasCompatibilityCatalog["questions"] = Object.fromEntries(
    view.nodes.flatMap((node) => {
      if (!node.question_id || !node.answer_type) return [];
      return [[node.question_id, { answerType: node.answer_type, allowedAnswers: node.allowed_answers }]];
    }),
  );
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
      <h2>データ診断 {model.diagnostics.length}件</h2>
      <ul>{model.diagnostics.map((item, index) => <li key={`${item.kind}:${item.subjectId}:${index}`}>{item.message}</li>)}</ul>
    </section>
  );
}

function LoadedMap({ view, model }: { view: ViewSpec; model: MapModel }) {
  const catalog = useMemo(() => catalogFromView(view), [view]);
  const atlas = useAtlasState(catalog);
  const atlasNavigation = useAtlasNavigation();
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

  if (atlas.error) {
    return (
      <section className="map-state-panel" role="alert">
        <h2>URL の状態を復元できません</h2>
        <p>{atlas.error.message}</p>
        <button className="map-action-button" onClick={atlas.reset} type="button">状態をリセット</button>
      </section>
    );
  }

  if (model.rootNodes.length === 0) {
    return (
      <>
        <Diagnostics model={model} />
        <p className="map-state-panel">表示できる項目がありません。</p>
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
      <div aria-label="表示するペイン" className="map-pane-switch" role="group">
        <button aria-pressed={activePane === "map"} onClick={() => setActivePane("map")} type="button">地図</button>
        <button aria-pressed={activePane === "detail"} onClick={() => setActivePane("detail")} type="button">詳細</button>
      </div>
      <div className="map-toolbar" role="toolbar" aria-label="地図表示">
        <button aria-label="縮小" disabled={zoom <= 80} onClick={() => setZoom((value) => Math.max(80, value - 10))} type="button">−</button>
        <output aria-label="表示倍率">{zoom}%</output>
        <button aria-label="拡大" disabled={zoom >= 140} onClick={() => setZoom((value) => Math.min(140, value + 10))} type="button">＋</button>
        <button aria-label="倍率をリセット" onClick={() => setZoom(100)} type="button">100%</button>
        <button disabled={!atlas.state.selectedNodeId} onClick={focusCurrent} type="button">現在地へ</button>
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

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const baseUrl = (import.meta as ImportMeta & { env: { BASE_URL: string } }).env.BASE_URL;
        const response = await fetch(`${baseUrl}data/views/problem-structure.json`);
        if (!response.ok) throw new Error(`ViewSpec request failed (${response.status}).`);
        const view = parseViewSpec(await response.json());
        if (active) setLoadState({ status: "ready", view, model: buildMapModel(view) });
      } catch (caught) {
        const error = caught instanceof Error ? caught : new Error(String(caught));
        if (active) setLoadState({ status: "error", error });
      }
    };
    void load();
    return () => { active = false; };
  }, []);

  return (
    <section className="map-page">
      <header className="map-page-header">
        <p className="eyebrow">Problem Structure</p>
        <h1>問題構造マップ</h1>
        {loadState.status === "ready" && <p>{loadState.view.description}</p>}
      </header>
      {loadState.status === "loading" && <p className="map-state-panel" role="status">地図を読み込んでいます…</p>}
      {loadState.status === "error" && (
        <section className="map-state-panel" role="alert">
          <h2>地図データを読み込めませんでした</h2>
          <p>{loadState.error.message}</p>
        </section>
      )}
      {loadState.status === "ready" && <LoadedMap model={loadState.model} view={loadState.view} />}
    </section>
  );
}
