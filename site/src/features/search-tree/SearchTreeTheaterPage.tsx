import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { parseSiteManifest } from "../../contracts/manifest";
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

type Loaded = { artifact: SearchTreeArtifact; index: SearchTreeIndex };

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

function SearchTreePlayer({ artifact, index }: Loaded) {
  const playback = usePlayback(artifact.trace.trace_id, artifact.trace.frames);
  const alternate = index.artifacts.find((item) => item.artifact_id !== artifact.artifact_id);
  const fallbackUrl = `${siteBaseUrl()}data/${artifact.static_fallback.path}`;
  return (
    <article className="trace-page search-tree-page">
      <header className="trace-header">
        <div>
          <p className="eyebrow">Discrete Optimization Theater</p>
          <h1>{artifact.scenario.title_ja}</h1>
          <p>{artifact.scenario.title_en}</p>
          <div className="artifact-badges">
            <span>実行Trace / Executable</span><span>search_tree {artifact.renderer_contract_version}</span>
          </div>
        </div>
        <dl className="trace-identity">
          <div><dt>Method</dt><dd><Link to="/learn/branch-and-bound">{artifact.trace.method_id}</Link></dd></div>
          <div><dt>Instance</dt><dd>{artifact.scenario.problem_instance_id}</dd></div>
          <div><dt>Seed / strategy</dt><dd>0 / depth-first include-first</dd></div>
        </dl>
      </header>
      <aside className="artifact-limitations" aria-label="artifactの種別と制約">
        <strong>教材としての制約</strong><p>{artifact.scenario.lesson.limitations_ja}</p>
      </aside>
      <PlaybackControls playback={playback} />
      {renderVisualizationArtifact(artifact, playback.currentFrameIndex)}
      <section className="search-tree-learning" aria-labelledby="search-tree-learning-heading">
        <h2 id="search-tree-learning-heading">Enumeration・MIP・CP-SATを混同しない</h2>
        <p>{artifact.scenario.lesson.enumeration_contrast_ja}</p>
        <p>{artifact.scenario.lesson.solver_distinction_ja}</p>
        {alternate && <Link className="text-link" to={`/theater/search-tree/${alternate.artifact_id}`}>
          {alternate.purpose === "failure_contrast" ? "node予算で止まる場合を見る" : "最適性証明まで見る"}
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
        <small>Sources: {artifact.source_ids.join(", ")} · Reviewed {artifact.last_verified}</small>
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
  const indexResponse = await fetch(`${baseUrl}data/${manifest.search_trees.path}`, { signal });
  if (!indexResponse.ok) throw new Error(`Search-tree index request failed (${indexResponse.status}).`);
  const indexBytes = new Uint8Array(await indexResponse.arrayBuffer());
  if (indexBytes.byteLength !== manifest.search_trees.bytes) throw new Error("Search-tree index byte length does not match the manifest.");
  if (await sha256Hex(indexBytes) !== manifest.search_trees.sha256) throw new Error("Search-tree index SHA-256 does not match the manifest.");
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
  if (artifact.trace.trace_id !== entry.trace_id || artifact.scenario.scenario_id !== entry.scenario_id) throw new Error("Search-tree artifact identity does not match its index entry.");
  return { artifact, index };
}

async function sha256Hex(bytes: Uint8Array): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", Uint8Array.from(bytes).buffer);
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}
