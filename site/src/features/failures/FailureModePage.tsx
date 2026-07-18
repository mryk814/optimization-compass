import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { findEntity, type EntityType } from "../../contracts/entity-links";
import {
  parseFailureDiscoveryIndex,
  type FailureDiscoveryEntry,
  type FailureDiscoveryIndex,
  type FailureDiscoveryKind,
} from "../../contracts/failure-discovery";
import { siteBaseUrl } from "../../data/base-url";
import { useEntityLinks } from "../../state/entity-links";

import "./failure-mode.css";

type KindFilter = "all" | FailureDiscoveryKind;

export function FailureModePage() {
  const links = useEntityLinks();
  const [params] = useSearchParams();
  const [index, setIndex] = useState<FailureDiscoveryIndex>();
  const [query, setQuery] = useState("");
  const [kind, setKind] = useState<KindFilter>("all");
  const [error, setError] = useState<Error>();
  const requestedEntry = params.get("entry");

  useEffect(() => {
    const controller = new AbortController();
    void loadFailureDiscovery(controller.signal).then(
      setIndex,
      (caught: unknown) => {
        if (!(caught instanceof DOMException && caught.name === "AbortError")) {
          setError(caught instanceof Error ? caught : new Error(String(caught)));
        }
      },
    );
    return () => controller.abort();
  }, []);

  const filtered = useMemo(() => {
    if (!index) return [];
    const normalized = query.trim().toLocaleLowerCase();
    return index.entries.filter((entry) => {
      if (kind !== "all" && entry.entry_kind !== kind) return false;
      if (requestedEntry && entry.entry_id !== requestedEntry) return false;
      return !normalized || discoverySearchText(entry).includes(normalized);
    });
  }, [index, kind, query, requestedEntry]);

  const entity = (type: EntityType, id: string) => (
    links.status === "ready" ? findEntity(links.index, type, id) : undefined
  );

  return (
    <section className="atlas-page failure-page">
      <header className="atlas-page-header failure-header">
        <div>
          <p className="eyebrow">失敗の兆候・除外理由</p>
          <h1>失敗の兆候から探す</h1>
          <p>観測された失敗profileと、特定のCaseで選ばない理由を区別したまま、確認項目・対処候補・根拠へ進みます。</p>
        </div>
        <Link className="text-link" to="/search">名前やケースから探す →</Link>
      </header>

      <div className="failure-controls">
        <label>
          症状・除外理由を検索
          <input aria-label="失敗の兆候を検索" onChange={(event) => setQuery(event.target.value)} placeholder="例: noise / constraint / 離散変数" type="search" value={query} />
        </label>
        <label>
          情報の種類
          <select value={kind} onChange={(event) => setKind(event.target.value as KindFilter)}>
            <option value="all">すべて</option>
            <option value="structured_failure">失敗profile</option>
            <option value="case_exclusion">Case固有の除外</option>
          </select>
        </label>
      </div>

      {error && <p className="atlas-error" role="alert">失敗・除外データを読み込めませんでした: {error.message}</p>}
      {!error && !index && <p role="status">失敗・除外indexを読み込み中…</p>}
      {index && <p className="failure-result-count" aria-live="polite">{index.entries.length}件中 {filtered.length}件を表示</p>}
      {index && filtered.length === 0 && <div className="failure-empty"><h2>一致する項目がありません</h2><p>検索語を短くするか、情報の種類をすべてへ戻してください。</p></div>}

      <div className="failure-grid">
        {filtered.map((entry) => <FailureDiscoveryCard entry={entry} entity={entity} key={entry.entry_id} />)}
      </div>
    </section>
  );
}

function FailureDiscoveryCard({
  entry,
  entity,
}: {
  entry: FailureDiscoveryEntry;
  entity: (type: EntityType, id: string) => { canonical_url: string | null; label: string } | undefined;
}) {
  const exclusion = entry.entry_kind === "case_exclusion";
  return (
    <article className="failure-card" id={entry.entry_id}>
      <header>
        <div className="failure-badges">
          <span>{exclusion ? "Case固有の除外" : "失敗profile"}</span>
          <span>{exclusion ? "excluded" : entry.disposition}</span>
          {!exclusion && <span className={`failure-severity is-${entry.severity}`}>{severityLabel(entry.severity)}</span>}
        </div>
        <h2>{entry.title_ja}</h2>
        <p lang="en">{entry.title_en}</p>
      </header>

      <p className="failure-summary">{entry.summary}</p>
      {exclusion ? (
        <section className="failure-primary-facts" aria-label="Caseの前提">
          <div><h3>このCaseで選ばない理由</h3><p>{entry.summary}</p></div>
          {entry.case_context && <div><h3>Caseの問い</h3><p>{entry.case_context.question}</p></div>}
        </section>
      ) : (
        <section className="failure-primary-facts" aria-label={`${entry.title_ja}の確認事項`}>
          <div><h3>見える兆候</h3><ul>{entry.symptoms.map((item) => <li key={item}>{item}</li>)}</ul></div>
          <div><h3>まず確認</h3><ol>{entry.diagnostics.map((item) => <li key={item}>{item}</li>)}</ol></div>
          <div><h3>対処候補</h3><ul>{entry.mitigations.map((item) => <li key={item.action}>{item.action}<small>{item.applicability}</small></li>)}</ul></div>
        </section>
      )}

      <details className="failure-detail">
        <summary>適用範囲・関連情報・根拠</summary>
        <div className="failure-detail-grid">
          <section><h3>適用範囲</h3><p>{entry.scope}</p><p><small>confidence: {entry.confidence} · 確認 {entry.last_verified}</small></p></section>
          <section><h3>関連対象</h3><ul>
            {entry.case_id && <li><EntityReference entity={entity("case", entry.case_id)} fallback={entry.case_id} /></li>}
            {entry.method_ids.map((id) => <li key={`method:${id}`}><EntityReference entity={entity("method", id)} fallback={id} /></li>)}
            {entry.implementation_ids.map((id) => <li key={`implementation:${id}`}><EntityReference entity={entity("implementation", id)} fallback={id} /></li>)}
          </ul></section>
          <section><h3>根拠・可視化</h3><ul>
            {entry.source_ids.map((id) => <li key={`source:${id}`}><EntityReference entity={entity("source", id)} fallback={id} /></li>)}
            {entry.scenario_ids.map((id) => <li key={`scenario:${id}`}><EntityReference entity={entity("scenario", id)} fallback={id} /></li>)}
          </ul></section>
        </div>
      </details>
    </article>
  );
}

async function loadFailureDiscovery(signal: AbortSignal): Promise<FailureDiscoveryIndex> {
  const response = await fetch(`${siteBaseUrl()}data/failure-discovery.json`, { signal });
  if (!response.ok) throw new Error(`Failure discovery request failed (${response.status}).`);
  return parseFailureDiscoveryIndex(await response.json());
}

function discoverySearchText(entry: FailureDiscoveryEntry): string {
  return [entry.entry_id, entry.title_ja, entry.title_en, entry.summary, entry.disposition, entry.scope, ...entry.symptoms, ...entry.diagnostics, ...entry.mitigations.flatMap((item) => [item.action, item.applicability, item.tradeoff])].join(" ").toLocaleLowerCase();
}

function severityLabel(severity: FailureDiscoveryEntry["severity"]): string {
  if (severity === "critical") return "重大";
  if (severity === "high") return "高";
  if (severity === "warning") return "注意";
  return "情報";
}

function EntityReference({ entity, fallback }: { entity?: { canonical_url: string | null; label: string }; fallback: string }) {
  return entity?.canonical_url ? <Link className="text-link" to={entity.canonical_url}>{entity.label}</Link> : <code>{entity?.label ?? fallback}</code>;
}
