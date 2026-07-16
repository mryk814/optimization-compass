import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import {
  SEARCH_ENTITY_TYPES,
  SEARCH_INTENTS,
  searchDocuments,
  type SearchEntityType,
  type SearchField,
  type SearchIndex,
  type SearchIntent,
} from "../../contracts/search-index";
import { loadSearchIndex } from "./search-data";

const TYPE_LABELS: Record<SearchEntityType, string> = {
  method: "手法", problem: "問題", implementation: "実装", content: "教材", case: "ケース",
  journey: "学習ジャーニー", scenario: "シナリオ", trace: "可視化", comparison: "比較", source: "根拠", glossary: "用語", feature: "特徴",
  feature_value: "特徴値", view: "マップ",
};

const INTENT_LABELS: Record<SearchIntent, string> = {
  classify_problem: "問題を整理", understand_method: "手法を理解", find_implementation: "実装を探す",
  compare_visualize: "比較・可視化", check_evidence: "根拠を確認", find_case: "事例を探す",
};

const FIELD_LABELS: Record<SearchField, string> = {
  canonical_label: "正式名", alias: "別名・略語", title: "タイトル", summary: "要約", keyword: "特徴", related: "関連語",
};

export function SearchPage() {
  const [params, setParams] = useSearchParams();
  const [index, setIndex] = useState<SearchIndex>();
  const [error, setError] = useState<Error>();
  const [draftQuery, setDraftQuery] = useState(() => params.get("q") ?? "");
  const inputRef = useRef<HTMLInputElement>(null);
  const isComposingRef = useRef(false);
  const query = params.get("q") ?? "";
  const intentParam = params.get("intent");
  const intent = SEARCH_INTENTS.find((value) => value === intentParam);
  const selectedTypes = useMemo(() => new Set(
    params.getAll("type").filter((value): value is SearchEntityType => SEARCH_ENTITY_TYPES.some((type) => type === value)),
  ), [params]);
  const directEntity = params.get("entity");

  useEffect(() => { void loadSearchIndex().then(setIndex, (caught: unknown) => setError(caught instanceof Error ? caught : new Error(String(caught)))); }, []);
  useEffect(() => {
    if (!isComposingRef.current) setDraftQuery(query);
  }, [query]);
  useEffect(() => {
    const handleKey = (event: KeyboardEvent) => {
      if ((event.key === "/" && !isTypingTarget(event.target)) || (event.key.toLocaleLowerCase() === "k" && (event.ctrlKey || event.metaKey))) {
        event.preventDefault(); inputRef.current?.focus(); inputRef.current?.select();
      }
    };
    window.addEventListener("keydown", handleKey); return () => window.removeEventListener("keydown", handleKey);
  }, []);

  const hits = useMemo(() => index ? searchDocuments(index, query, { entityTypes: selectedTypes, intent }) : [], [index, intent, query, selectedTypes]);
  const directDocument = useMemo(() => index && directEntity ? index.documents.find((document) => document.document_id === directEntity) : undefined, [directEntity, index]);
  const visibleHits = directDocument && !query ? [{ document: directDocument, score: 0, matchedFields: [] as SearchField[] }] : hits.slice(0, 80);
  const availableTypes = useMemo(() => {
    const documents = index?.documents ?? [];
    return SEARCH_ENTITY_TYPES.map((type) => ({ type, count: documents.filter((document) => document.entity_type === type).length })).filter((item) => item.count > 0);
  }, [index]);

  const updateParams = (mutate: (next: URLSearchParams) => void) => {
    const next = new URLSearchParams(params); mutate(next); setParams(next, { replace: true });
  };
  const commitQuery = (value: string) => updateParams((next) => {
    value ? next.set("q", value) : next.delete("q");
    next.delete("entity");
  });
  const toggleType = (type: SearchEntityType) => updateParams((next) => {
    const types = new Set(next.getAll("type")); types.has(type) ? types.delete(type) : types.add(type);
    next.delete("type"); [...types].sort().forEach((value) => next.append("type", value)); next.delete("entity");
  });

  return (
    <section className="atlas-page search-page">
      <header className="atlas-page-header search-header">
        <div><p className="eyebrow">Global Search</p><h1>Atlas全体から探す</h1></div>
        <p>手法名だけでなく、「勾配なしで高価な実験」のような状況、日本語・英語・略語からも探せます。</p>
        <Link className="text-link" to="/failures">失敗の兆候・診断から探す →</Link>
      </header>
      <div className="global-search-bar">
        <label htmlFor="global-search-input">検索</label>
        <div className="global-search-input-wrap">
          <input
            id="global-search-input"
            ref={inputRef}
            type="search"
            aria-describedby="search-shortcut search-status"
            autoComplete="off"
            onChange={(event) => {
              const value = event.target.value;
              setDraftQuery(value);
              if (!isComposingRef.current) commitQuery(value);
            }}
            onCompositionEnd={(event) => {
              isComposingRef.current = false;
              const value = event.currentTarget.value;
              setDraftQuery(value);
              commitQuery(value);
            }}
            onCompositionStart={() => { isComposingRef.current = true; }}
            placeholder="例: BO / 配送順を決めたい / gradient-free"
            value={draftQuery}
          />
          {draftQuery && <button aria-label="検索語を消去" onClick={() => { setDraftQuery(""); commitQuery(""); }} type="button">×</button>}
        </div>
        <span id="search-shortcut" className="search-shortcut" aria-hidden="true">/ または Ctrl K</span>
      </div>
      <div className="search-controls">
        <fieldset><legend>対象</legend><div className="search-filter-chips">{availableTypes.map(({ type, count }) => <label key={type} className={selectedTypes.has(type) ? "search-chip is-selected" : "search-chip"}><input checked={selectedTypes.has(type)} onChange={() => toggleType(type)} type="checkbox" /><span>{TYPE_LABELS[type]} <small>{count}</small></span></label>)}</div></fieldset>
        <label className="search-intent">目的<select aria-label="検索の目的" onChange={(event) => updateParams((next) => { event.target.value ? next.set("intent", event.target.value) : next.delete("intent"); next.delete("entity"); })} value={intent ?? ""}><option value="">すべて</option>{SEARCH_INTENTS.map((value) => <option key={value} value={value}>{INTENT_LABELS[value]}</option>)}</select></label>
      </div>
      {error && <p className="atlas-error" role="alert">検索indexを読み込めませんでした: {error.message}</p>}
      {!index && !error && <p id="search-status" aria-live="polite">検索indexを読み込み中…</p>}
      {index && <p id="search-status" className="search-result-summary" aria-live="polite">{query ? `${hits.length}件` : directDocument ? "用語を表示中" : `${index.documents.length}件を検索できます`}{selectedTypes.size || intent ? " · filter適用中" : ""}</p>}
      {index && (query || directEntity) && visibleHits.length === 0 && <div className="search-empty"><h2>一致する項目がありません</h2><p>表記を短くするか、対象・目的filterを外してみてください。</p></div>}
      <div className="search-results">{visibleHits.map(({ document, matchedFields }) => <article key={document.document_id} className="search-result-card">
        <div className="search-result-heading"><span className={`search-type search-type-${document.entity_type}`}>{TYPE_LABELS[document.entity_type]}</span><h2><Link to={document.canonical_route}>{document.title_ja}</Link></h2>{document.title_en !== document.title_ja && <p lang="en">{document.title_en}</p>}</div>
        {document.summary && <p className="search-result-copy">{document.summary}</p>}
        <div className="search-result-meta">{matchedFields.length > 0 && <span>一致: {matchedFields.map((field) => FIELD_LABELS[field]).join("・")}</span>}<code>{document.entity_id}</code>{document.last_reviewed && <span>確認 {document.last_reviewed}</span>}</div>
        <div className="search-result-actions"><Link className="text-link" to={document.canonical_route}>開く →</Link>{document.external_url && <a className="text-link" href={document.external_url} rel="noreferrer" target="_blank">公式資料 ↗</a>}{document.source_ids.slice(0, 3).map((sourceId) => <Link key={sourceId} className="search-source-link" to={`/sources/${sourceId}`}>{sourceId}</Link>)}</div>
      </article>)}</div>
      {hits.length > visibleHits.length && <p className="search-result-limit">上位{visibleHits.length}件を表示しています。検索語やfilterで絞り込めます。</p>}
    </section>
  );
}

function isTypingTarget(target: EventTarget | null): boolean {
  return target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement || target instanceof HTMLSelectElement || (target instanceof HTMLElement && target.isContentEditable);
}
