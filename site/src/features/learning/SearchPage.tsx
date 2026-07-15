import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { aliasTerms, findLearningEntity, searchTerminology, type LearningGraphIndex } from "../../contracts/learning-graph";
import { loadLearningGraph } from "./learning-data";

export function SearchPage() {
  const [params, setParams] = useSearchParams();
  const [index, setIndex] = useState<LearningGraphIndex>();
  const [error, setError] = useState<Error>();
  const query = params.get("q") ?? "";
  useEffect(() => { void loadLearningGraph().then(setIndex, (caught: unknown) => setError(caught instanceof Error ? caught : new Error(String(caught)))); }, []);
  const results = useMemo(() => index ? searchTerminology(index, query) : [], [index, query]);
  const suggestions = useMemo(() => index ? [...new Set(index.aliases.flatMap(aliasTerms))].sort((a, b) => a.localeCompare(b, "ja")) : [], [index]);
  return (
    <section className="atlas-page search-page">
      <header className="atlas-page-header"><p className="eyebrow">Search</p><h1>用語から探す</h1><p>日本語・英語・略語・実務用語からcanonical entityへ解決します。</p></header>
      <label className="atlas-search">用語<input aria-label="用語を検索" list="terminology-suggestions" onChange={(event) => setParams(event.target.value ? { q: event.target.value } : {})} placeholder="BO / 混合整数計画 / derivative-free" value={query} /></label>
      <datalist id="terminology-suggestions">{suggestions.map((term) => <option key={term} value={term} />)}</datalist>
      {error && <p className="atlas-error" role="alert">{error.message}</p>}
      {query && index && results.length === 0 && <p>一致するcanonical entityがありません。</p>}
      <div className="search-results">{results.map((alias) => {
        const entity = findLearningEntity(index!, alias.target_type, alias.target_id)!;
        const deprecated = alias.deprecated_terms.filter((term) => term.toLocaleLowerCase().includes(query.toLocaleLowerCase()));
        return <article key={alias.term_id}><p className="eyebrow">{alias.target_type} · {alias.target_id}</p><h2>{alias.label_ja} <small>{alias.label_en}</small></h2>{alias.disambiguation_note && <p>{alias.disambiguation_note}</p>}{deprecated.length > 0 && <p className="deprecated-term">非推奨語: {deprecated.join(" / ")}</p>}<p>{alias.rationale}</p>{entity.canonical_url ? <Link className="text-link" to={entity.canonical_url}>canonical pageを開く</Link> : entity.external_url ? <a className="text-link" href={entity.external_url} rel="noreferrer" target="_blank">公式ページを開く</a> : null}</article>;
      })}</div>
    </section>
  );
}
