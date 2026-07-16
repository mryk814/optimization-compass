import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { parseSiteManifest } from "../../contracts/manifest";
import {
  parseVisualizationScenarioIndex,
  type GuidedStoryStep,
  type VisualizationScenario,
  type VisualizationScenarioIndex,
} from "../../contracts/visualization-scenarios";
import {
  parseSearchTreeArtifact,
  parseSearchTreeIndex,
  type SearchTreeArtifact,
  type SearchTreeIndex,
} from "../../contracts/search-tree";
import { siteBaseUrl } from "../../data/base-url";
import { PlaybackControls } from "../playback/PlaybackControls";
import { usePlayback } from "../playback/usePlayback";
import { EntityNotFoundError, NotFoundPage } from "../navigation/NotFoundPage";
import { renderVisualizationArtifact } from "./renderer-registry";
import { ScenarioLessonPanel } from "../visualization/ScenarioLessonPanel";
import { GuidedStoryPanel } from "../visualization/GuidedStoryPanel";
import { ScenarioContextPanel } from "../theater/ScenarioContextPanel";

type Loaded = {
  artifact: SearchTreeArtifact;
  index: SearchTreeIndex;
  scenario: VisualizationScenario;
  scenarioIndex: VisualizationScenarioIndex;
};

export function SearchTreeTheaterPage() {
  const { artifactId = "" } = useParams();
  const [loaded, setLoaded] = useState<Loaded>();
  const [error, setError] = useState<Error>();
  useEffect(() => {
    const controller = new AbortController();
    setLoaded(undefined); setError(undefined);
    void loadArtifact(artifactId, controller.signal).then(setLoaded, (caught: unknown) => {
      if (!controller.signal.aborted) setError(caught instanceof Error ? caught : new Error(String(caught)));
    });
    return () => controller.abort();
  }, [artifactId]);
  if (error instanceof EntityNotFoundError) return <NotFoundPage detail={error.message} />;
  if (error) return <section className="trace-page"><h1>Search-tree Theaterを開けません</h1><p role="alert">{error.message}</p></section>;
  if (!loaded) return <p role="status">Search-tree artifactを読み込み中…</p>;
  return <SearchTreePlayer key={loaded.artifact.artifact_id} {...loaded} />;
}

function SearchTreePlayer({ artifact, index, scenario, scenarioIndex }: Loaded) {
  const playback = usePlayback(artifact.trace.trace_id, artifact.trace.frames);
  const [guidedStep, setGuidedStep] = useState<GuidedStoryStep | null>(null);
  const alternate = index.artifacts.find((item) => item.artifact_id !== artifact.artifact_id);
  const alternateScenario = alternate
    ? scenarioIndex.scenarios.find((item) => item.scenario_id === alternate.scenario_id)
    : undefined;
  const fallbackUrl = `${siteBaseUrl()}data/${artifact.static_fallback.path}`;
  return (
    <article className="trace-page search-tree-page">
      <header className="trace-header">
        <div>
          <p className="eyebrow">Discrete Optimization Theater</p>
          <h1>{scenario.title_ja}</h1>
          <p>{scenario.title_en}</p>
          <div className="artifact-badges">
            <span>実行Trace / Executable</span><span>search_tree {artifact.renderer_contract_version}</span>
          </div>
        </div>
        <dl className="trace-identity">
          <div><dt>Method</dt><dd><Link to="/learn/branch-and-bound">{artifact.trace.method_id}</Link></dd></div>
          <div><dt>Instance</dt><dd>{scenario.problem_instance_id}</dd></div>
          <div><dt>Seed / strategy</dt><dd>0 / depth-first include-first</dd></div>
        </dl>
      </header>
      <ScenarioContextPanel scenario={scenario} />
      <aside className="artifact-limitations" aria-label="artifactの種別と制約">
        <strong>教材としての制約</strong><p>{scenario.lesson.limitations_ja}</p>
      </aside>
      <ScenarioLessonPanel scenario={scenario} />
      <GuidedStoryPanel
        activeStep={guidedStep}
        onStepChange={setGuidedStep}
        playback={playback}
        scenario={scenario}
      />
      <PlaybackControls playback={playback} />
      {renderVisualizationArtifact(
        artifact,
        playback.currentFrameIndex,
        guidedStep?.visible_layers,
        guidedStep?.focus_target,
      )}
      <section className="search-tree-learning" aria-labelledby="search-tree-learning-heading">
        <h2 id="search-tree-learning-heading">Enumeration・MIP・CP-SATを混同しない</h2>
        <p>naive enumerationは全16割当を調べますが、Branch-and-Boundは実行不可能性と上界で、改善不能なsubtreeを丸ごと探索しません。</p>
        <p>MIPのBranch-and-Cutは連続緩和とcutを使います。CP-SATはSAT/CP伝播などを統合するため、同じ探索木表示でも内部機構を同一視できません。</p>
        {alternate && <Link className="text-link" to={`/theater/search-tree/${alternate.artifact_id}`}>
          {alternateScenario?.purpose === "failure_contrast" ? "node予算で止まる場合を見る" : "最適性証明まで見る"}
        </Link>}
      </section>
      <details className="search-tree-fallback">
        <summary>静止画 fallback</summary>
        <p>JavaScript再生を使えない場合にも、最終状態と枝刈りを確認できます。</p>
        <img alt={artifact.static_fallback.alt_ja} src={fallbackUrl} />
        <a href={fallbackUrl}>SVGを直接開く</a>
      </details>
      <footer className="trace-summary">
        <span>{artifact.trace.terminal_status}</span>
        <p>{artifact.trace.terminal_summary_ja}</p>
        <small>Sources: {scenario.source_ids.join(", ")} · Reviewed {scenario.last_verified}</small>
      </footer>
    </article>
  );
}

async function loadArtifact(artifactId: string, signal: AbortSignal): Promise<Loaded> {
  if (!artifactId.trim()) throw new Error("Artifact IDが指定されていません。");
  const baseUrl = siteBaseUrl();
  const manifestResponse = await fetch(`${baseUrl}data/manifest.json`, { signal });
  if (!manifestResponse.ok) throw new Error(`Manifest request failed (${manifestResponse.status}).`);
  const manifest = parseSiteManifest(await manifestResponse.json());
  const scenarioResponse = await fetch(`${baseUrl}data/${manifest.visualization_scenarios.path}`, { signal });
  if (!scenarioResponse.ok) throw new Error(`Visualization scenario request failed (${scenarioResponse.status}).`);
  const scenarioIndex = parseVisualizationScenarioIndex(await scenarioResponse.json());
  if (scenarioIndex.dataset_version !== manifest.dataset_version) {
    throw new Error("Visualization scenario dataset version does not match the manifest.");
  }
  const canonicalScenario = scenarioIndex.scenarios.find((candidate) =>
    candidate.runs.some((run) => run.artifact_id === artifactId),
  );
  if (!canonicalScenario || canonicalScenario.artifact.renderer_family !== "search_tree") {
    throw new EntityNotFoundError("Search-tree artifact ID", artifactId);
  }
  const payloadResponse = await fetch(`${baseUrl}data/${canonicalScenario.artifact.payload_path}`, { signal });
  if (!payloadResponse.ok) throw new Error(`Canonical scenario payload request failed (${payloadResponse.status}).`);
  const payloadBytes = new Uint8Array(await payloadResponse.arrayBuffer());
  if (payloadBytes.byteLength !== canonicalScenario.artifact.payload_bytes) {
    throw new Error("Canonical scenario payload byte length does not match the scenario index.");
  }
  if (await sha256Hex(payloadBytes) !== canonicalScenario.artifact.payload_sha256) {
    throw new Error("Canonical scenario payload SHA-256 does not match the scenario index.");
  }
  const indexResponse = await fetch(`${baseUrl}data/search-trees/index.json`, { signal });
  if (!indexResponse.ok) throw new Error(`Search-tree index request failed (${indexResponse.status}).`);
  const indexBytes = new Uint8Array(await indexResponse.arrayBuffer());
  const index = parseSearchTreeIndex(JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(indexBytes)));
  if (index.dataset_version !== manifest.dataset_version) throw new Error("Search-tree index dataset version does not match the manifest.");
  const entry = index.artifacts.find((candidate) => candidate.artifact_id === artifactId);
  if (!entry) throw new EntityNotFoundError("Search-tree artifact ID", artifactId);
  const response = await fetch(`${baseUrl}data/${entry.path}`, { signal });
  if (!response.ok) throw new Error(`Search-tree artifact request failed (${response.status}).`);
  const artifact = parseSearchTreeArtifact(await response.json());
  const references = {
    artifact_id: entry.artifact_id, dataset_version: index.dataset_version,
    renderer_family: entry.renderer_family, renderer_contract_version: entry.renderer_contract_version,
  } as const;
  for (const [field, expected] of Object.entries(references)) {
    if (artifact[field as keyof typeof references] !== expected) throw new Error(`Search-tree artifact ${field} does not match its index entry.`);
  }
  if (artifact.trace.trace_id !== entry.trace_id || artifact.scenario_id !== entry.scenario_id) {
    throw new Error("Search-tree artifact identity does not match its index entry.");
  }
  const scenario = canonicalScenario;
  if (scenario.scenario_id !== artifact.scenario_id) {
    throw new Error("Visualization scenario does not match the search-tree artifact identity.");
  }
  if (scenario.artifact.artifact_kind !== artifact.artifact_kind
      || scenario.artifact.renderer_family !== artifact.renderer_family
      || scenario.artifact.renderer_contract_version !== artifact.renderer_contract_version
      || !scenario.runs.some((run) => run.artifact_id === artifact.artifact_id)) {
    throw new Error("Visualization scenario does not match the search-tree artifact.");
  }
  if (scenario.problem_instance_id !== artifact.trace.objective_id
      || JSON.stringify(scenario.source_ids) !== JSON.stringify(artifact.trace.source_ids)) {
    throw new Error("Visualization scenario provenance does not match the search-tree trace.");
  }
  return { artifact, index, scenario, scenarioIndex };
}

async function sha256Hex(bytes: Uint8Array): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", Uint8Array.from(bytes).buffer);
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}
