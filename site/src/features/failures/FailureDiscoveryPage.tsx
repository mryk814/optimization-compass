import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { findEntity } from "../../contracts/entity-links";
import {
  parseFailureDiscoveryIndex,
  type FailureDiscoveryEntry,
  type FailureDiscoveryIndex,
  type FailureDiscoveryKind,
} from "../../contracts/failure-discovery";
import { siteBaseUrl } from "../../data/base-url";
import { useEntityLinks } from "../../state/entity-links";

import "./failure-discovery.css";

type LoadState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; index: FailureDiscoveryIndex };

type KindFilter = "all" | FailureDiscoveryKind;

export function FailureDiscoveryPage() {
  const [state, setState] = useState<LoadState>({ status: "loading" });
  const [query, setQuery] = useState("");
  const [kind, setKind] = useState<KindFilter>("all");
  const [searchParams] = useSearchParams();
  const requestedEntry = searchParams.get("entry");
  const entityLinks = useEntityLinks();

  useEffect(() => {
    const controller = new AbortController();
    void loadFailureDiscovery(controller.signal).then(
      (index) => setState({ status: "ready", index }),
      (caught: unknown) => {
        if (!controller.signal.aborted) {
          const error = caught instanceof Error ? caught : new Error(String(caught));
          setState({ status: "error", message: error.message });
        }
      },
    );
    return () => controller.abort();
  }, []);

  const entries = useMemo(() => {
    if (state.status !== "ready") return [];
    const normalized = normalize(query);
    return state.index.entries.filter((entry) => {
      if (kind !== "all" && entry.kind !== kind) return false;
      if (requestedEntry && !entry.entry_id.endsWith(`:${requestedEntry}`)) return false;
      return normalized === "" || normalize(entry.search_text).includes(normalized);
    });
  }, [kind, query, requestedEntry, state]);

  const methodLabel = (methodId: string) => {
    if (entityLinks.status !== "ready") return methodId;
    return findEntity(entityLinks.index, "method", methodId)?.label ?? methodId;
  };

  return (
    <section className="failure-discovery-page">
      <header className="failure-discovery-hero">
        <p className="eyebrow">Failure & exclusion discovery</p>
        <h1>失敗の兆候から探す</h1>
        <p>
          観測された失敗profileと、特定のCaseで選ばない理由を区別したまま探します。
          ここにある除外は万能なblacklistではありません。
        </p>
      </header>

      <section aria-label="失敗・除外の絞り込み" className="failure-discovery-controls">
        <label>
          <span>症状・除外理由を検索</span>
          <input
            onChange={(event) => setQuery(event.currentTarget.value)}
            placeholder="例: constraint violation、noise、離散変数"
            type="search"
            value={query}
          />
        </label>
        <fieldset>
          <legend>情報の種類</legend>
          {([
            ["all", "すべて"],
            ["structured_failure", "失敗profile"],
            ["case_exclusion", "Case固有の除外"],
          ] as const).map(([value, label]) => (
            <label key={value}>
              <input
                checked={kind === value}
                name="failure-discovery-kind"
                onChange={() => setKind(value)}
                type="radio"
              />
              {label}
            </label>
          ))}
        </fieldset>
      </section>

      {state.status === "loading" && <p role="status">失敗・除外indexを読み込んでいます…</p>}
      {state.status === "error" && <p role="alert">読み込みに失敗しました: {state.message}</p>}
      {state.status === "ready" && (
        <>
          <p aria-live="polite" className="failure-discovery-count">
            {state.index.entries.length}件中 {entries.length}件を表示
          </p>
          {entries.length === 0 ? (
            <p>一致する項目がありません。表現を変えるか、種類の絞り込みを解除してください。</p>
          ) : (
            <div className="failure-discovery-list">
              {entries.map((entry) => (
                <FailureDiscoveryCard
                  entry={entry}
                  key={entry.entry_id}
                  methodLabel={methodLabel}
                />
              ))}
            </div>
          )}
        </>
      )}
    </section>
  );
}

function FailureDiscoveryCard({
  entry,
  methodLabel,
}: {
  entry: FailureDiscoveryEntry;
  methodLabel: (methodId: string) => string;
}) {
  const isExclusion = entry.kind === "case_exclusion";
  return (
    <article className={`failure-discovery-card failure-discovery-card-${entry.kind}`}>
      <header>
        <div>
          <p className="failure-discovery-kind">
            {isExclusion ? "Case固有の除外" : "構造化された失敗profile"}
          </p>
          <h2>{entry.title}</h2>
        </div>
        <span className="failure-discovery-disposition">
          {isExclusion ? "excluded" : entry.severity}
        </span>
      </header>

      <p className="failure-discovery-summary">{entry.summary}</p>

      {isExclusion ? (
        <div className="failure-discovery-core">
          <section>
            <h3>このCaseで選ばない理由</h3>
            <p>{entry.summary}</p>
          </section>
          <section>
            <h3>適用範囲</h3>
            <p>{entry.trigger}</p>
          </section>
        </div>
      ) : (
        <div className="failure-discovery-core">
          <section>
            <h3>まず確認すること</h3>
            <p>{entry.diagnostics[0]}</p>
          </section>
          <section>
            <h3>対処候補</h3>
            <p>{entry.mitigations[0]}</p>
          </section>
        </div>
      )}

      <details>
        <summary>関連情報と根拠</summary>
        <dl>
          <div><dt>trigger / scope</dt><dd>{entry.trigger}</dd></div>
          <div><dt>confidence</dt><dd>{entry.confidence}</dd></div>
          {entry.method_ids.length > 0 && (
            <div>
              <dt>Methods</dt>
              <dd>
                {entry.method_ids.map((methodId) => (
                  <Link key={methodId} to={`/methods/${methodId}`}>{methodLabel(methodId)}</Link>
                ))}
              </dd>
            </div>
          )}
          {entry.source_ids.length > 0 && (
            <div>
              <dt>Sources</dt>
              <dd>
                {entry.source_ids.map((sourceId) => (
                  <Link key={sourceId} to={`/sources/${sourceId}`}>{sourceId}</Link>
                ))}
              </dd>
            </div>
          )}
          {entry.scenario_ids.length > 0 && (
            <div><dt>Scenarios</dt><dd>{entry.scenario_ids.join(", ")}</dd></div>
          )}
        </dl>
        <Link className="failure-discovery-route" to={entry.canonical_url}>
          {isExclusion ? "Caseで前提を確認する" : "この項目を固定表示する"} →
        </Link>
      </details>
    </article>
  );
}

async function loadFailureDiscovery(signal: AbortSignal): Promise<FailureDiscoveryIndex> {
  const response = await fetch(`${siteBaseUrl()}data/failure-discovery.json`, { signal });
  if (!response.ok) throw new Error(`Failure discovery request failed (${response.status}).`);
  return parseFailureDiscoveryIndex(await response.json());
}

function normalize(value: string): string {
  return value.normalize("NFKC").toLocaleLowerCase("ja").replace(/\s+/gu, " ").trim();
}
