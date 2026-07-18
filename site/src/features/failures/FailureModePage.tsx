import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import {
  parseFailureModeIndex,
  type FailureModeRecord,
} from "../../contracts/failure-modes";
import { findEntity, type EntityType } from "../../contracts/entity-links";
import { siteBaseUrl } from "../../data/base-url";
import { useEntityLinks } from "../../state/entity-links";

import "./failure-mode.css";

const severityOrder: Record<FailureModeRecord["severity"], number> = {
  critical: 0,
  high: 1,
  warning: 2,
  info: 3,
};

export function FailureModePage() {
  const links = useEntityLinks();
  const [failures, setFailures] = useState<FailureModeRecord[]>([]);
  const [query, setQuery] = useState("");
  const [severity, setSeverity] = useState("all");
  const [scope, setScope] = useState("all");
  const [error, setError] = useState<Error>();

  useEffect(() => {
    const controller = new AbortController();
    void loadFailureModes(controller.signal).then(
      (items) => setFailures(items),
      (caught: unknown) => {
        if (!(caught instanceof DOMException && caught.name === "AbortError")) {
          setError(caught instanceof Error ? caught : new Error(String(caught)));
        }
      },
    );
    return () => controller.abort();
  }, []);

  const filtered = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase();
    return failures
      .filter((item) => severity === "all" || item.severity === severity)
      .filter((item) => scope === "all" || item.failure_scope === scope)
      .filter((item) => !normalized || failureSearchText(item).includes(normalized))
      .sort((left, right) => (
        severityOrder[left.severity] - severityOrder[right.severity]
        || left.name_ja.localeCompare(right.name_ja, "ja")
      ));
  }, [failures, query, scope, severity]);

  const entity = (type: EntityType, id: string) => (
    links.status === "ready" ? findEntity(links.index, type, id) : undefined
  );

  return (
    <section className="atlas-page failure-page">
      <header className="atlas-page-header failure-header">
        <div>
          <p className="eyebrow">失敗の兆候</p>
          <h1>失敗の兆候から探す</h1>
          <p>
            何が起きているかから、確認項目・対処候補・影響する手法・根拠へ進みます。
          </p>
        </div>
        <Link className="text-link" to="/search">名前やケースから探す →</Link>
      </header>

      <div className="failure-controls">
        <label>
          症状・用語を検索
          <input
            aria-label="失敗の兆候を検索"
            onChange={(event) => setQuery(event.target.value)}
            placeholder="例: gradient符号 / scale / constraint"
            type="search"
            value={query}
          />
        </label>
        <label>
          重大度
          <select value={severity} onChange={(event) => setSeverity(event.target.value)}>
            <option value="all">すべて</option>
            <option value="critical">重大</option>
            <option value="high">高</option>
            <option value="warning">注意</option>
            <option value="info">情報</option>
          </select>
        </label>
        <label>
          対象範囲
          <select value={scope} onChange={(event) => setScope(event.target.value)}>
            <option value="all">すべて</option>
            <option value="method_theory">手法理論</option>
            <option value="implementation_specific">実装固有</option>
            <option value="mixed">混合</option>
          </select>
        </label>
      </div>

      {error && <p className="atlas-error" role="alert">失敗データを読み込めませんでした: {error.message}</p>}
      {!error && failures.length === 0 && <p role="status">失敗データを読み込み中…</p>}
      {failures.length > 0 && (
        <p className="failure-result-count" aria-live="polite">{filtered.length}件を表示</p>
      )}
      {failures.length > 0 && filtered.length === 0 && (
        <div className="failure-empty">
          <h2>一致する失敗モードがありません</h2>
          <p>検索語を短くするか、絞り込み条件をすべてへ戻してください。</p>
        </div>
      )}

      <div className="failure-grid">
        {filtered.map((item) => (
          <article className="failure-card" id={item.failure_mode_id} key={item.failure_mode_id}>
            <header>
              <div className="failure-badges">
              <span className={`failure-severity is-${item.severity}`}>{severityLabel(item.severity)}</span>
                <span>{scopeLabel(item.failure_scope)}</span>
                <span>{item.recoverability}</span>
              </div>
              <h2>{item.name_ja}</h2>
              <p lang="en">{item.name_en}</p>
            </header>

            <section className="failure-primary-facts" aria-label={`${item.name_ja}の確認事項`}>
              <div>
                <h3>見える兆候</h3>
                <ul>{item.symptoms.map((symptom) => <li key={symptom.description}>{symptom.description}</li>)}</ul>
              </div>
              <div>
                <h3>まず確認</h3>
                <ol>{item.diagnostics.map((diagnostic) => <li key={diagnostic.diagnostic_id}>{diagnostic.check_text}</li>)}</ol>
              </div>
              <div>
                <h3>対処候補</h3>
                <ul>{item.mitigations.map((mitigation) => <li key={mitigation.action}>{mitigation.action}<small>{mitigation.applicability}</small></li>)}</ul>
              </div>
            </section>

            <details className="failure-detail">
              <summary>影響する手法・可視化・根拠</summary>
              <div className="failure-detail-grid">
                <section>
                  <h3>影響する対象</h3>
                  <ul>
                    {item.affected_entities.map((affected) => (
                      <li key={`${affected.entity_type}:${affected.entity_id}`}>
                        <EntityReference
                          entity={entity(affected.entity_type, affected.entity_id)}
                          fallback={affected.entity_id}
                        />
                        <small>{affected.specificity}</small>
                      </li>
                    ))}
                  </ul>
                </section>
                <section>
                  <h3>関連シナリオ</h3>
                  {item.scenario_ids.length === 0 ? <p>公開シナリオは未接続です。</p> : (
                    <ul>
                      {item.scenario_ids.map((scenarioId) => (
                        <li key={scenarioId}>
                          <EntityReference entity={entity("scenario", scenarioId)} fallback={scenarioId} />
                        </li>
                      ))}
                    </ul>
                  )}
                </section>
                <section>
                  <h3>根拠</h3>
                  <ul>
                    {item.source_ids.map((sourceId) => (
                      <li key={sourceId}>
                        <EntityReference entity={entity("source", sourceId)} fallback={sourceId} />
                      </li>
                    ))}
                  </ul>
                  <p><small>confidence: {item.confidence}</small></p>
                </section>
              </div>
            </details>
          </article>
        ))}
      </div>
    </section>
  );
}

async function loadFailureModes(signal: AbortSignal): Promise<FailureModeRecord[]> {
  const response = await fetch(`${siteBaseUrl()}data/failure-modes.json`, { signal });
  if (!response.ok) throw new Error(`Failure mode request failed (${response.status}).`);
  return parseFailureModeIndex(await response.json()).failure_modes;
}

function failureSearchText(item: FailureModeRecord): string {
  return [
    item.failure_mode_id,
    item.name_ja,
    item.name_en,
    item.failure_scope,
    item.severity,
    ...item.symptoms.flatMap((symptom) => [
      symptom.description,
      symptom.observable_id ?? "",
      symptom.non_visual_state ?? "",
    ]),
    ...item.diagnostics.flatMap((diagnostic) => [diagnostic.diagnostic_id, diagnostic.check_text]),
    ...item.mitigations.flatMap((mitigation) => [
      mitigation.action,
      mitigation.applicability,
      mitigation.tradeoff,
    ]),
    ...item.affected_entities.map((affected) => affected.entity_id),
  ].join(" ").toLocaleLowerCase();
}

function scopeLabel(scope: FailureModeRecord["failure_scope"]): string {
  if (scope === "method_theory") return "手法理論";
  if (scope === "implementation_specific") return "実装固有";
  return "混合";
}

function severityLabel(severity: FailureModeRecord["severity"]): string {
  if (severity === "critical") return "重大";
  if (severity === "high") return "高";
  if (severity === "warning") return "注意";
  return "情報";
}

function EntityReference({
  entity,
  fallback,
}: {
  entity?: { canonical_url: string | null; label: string };
  fallback: string;
}) {
  return entity?.canonical_url
    ? <Link className="text-link" to={entity.canonical_url}>{entity.label}</Link>
    : <code>{entity?.label ?? fallback}</code>;
}
