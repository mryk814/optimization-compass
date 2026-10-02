import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";

import type { AtlasContentPage } from "../../contracts/atlas-content";
import {
  compassNeighbors,
  formulationMatches,
  relationSentence,
  type CompassDirection,
  type CompassNeighbor,
  type Formulation,
  type FormulationAtlasIndex,
} from "../../contracts/formulation-atlas";
import { CompiledContent } from "../content/CompiledContent";
import { EvidenceLinks } from "../evidence/EvidenceLinks";
import { EntityNotFoundError, NotFoundPage } from "../navigation/NotFoundPage";
import { loadContentIndex, loadFormulationAtlas } from "./formulation-data";

import "./formulations.css";

const LENS_LABELS = {
  form: "式の形で分ける",
  oracle: "評価の事情で分ける",
  application: "使う場面で分ける",
} as const;

function useAtlas() {
  const [atlas, setAtlas] = useState<FormulationAtlasIndex>();
  const [error, setError] = useState<Error>();
  useEffect(() => {
    let active = true;
    void loadFormulationAtlas().then(
      (index) => { if (active) setAtlas(index); },
      (caught: unknown) => {
        if (active) setError(caught instanceof Error ? caught : new Error(String(caught)));
      },
    );
    return () => { active = false; };
  }, []);
  return { atlas, error };
}

function MaturityBadge({ item }: { item: Formulation }) {
  if (item.maturity === "skeleton") return <span className="formulation-badge formulation-badge-skeleton">標準形のみ</span>;
  return (
    <span className="formulation-badge formulation-badge-article">
      {item.maturity === "article_with_figure" ? "解説・動く図あり" : "解説あり"}
    </span>
  );
}

export function FormulationIndexPage() {
  const { atlas, error } = useAtlas();
  const { hash } = useLocation();
  const [query, setQuery] = useState("");
  const [onlyArticles, setOnlyArticles] = useState(false);

  useEffect(() => {
    document.title = "定式化の辞書 | Optimization Compass";
  }, []);

  useEffect(() => {
    if (atlas && hash) document.getElementById(hash.slice(1))?.scrollIntoView({ block: "start" });
  }, [atlas, hash]);

  const byId = useMemo(
    () => new Map(atlas?.formulations.map((item) => [item.problem_id, item]) ?? []),
    [atlas],
  );
  const visibleCount = atlas?.formulations.filter(
    (item) => formulationMatches(item, query) && (!onlyArticles || item.maturity !== "skeleton"),
  ).length ?? 0;

  return (
    <section className="atlas-page formulation-index">
      <header className="formulation-index-header">
        <p className="eyebrow">辞書</p>
        <h1>定式化の辞書</h1>
        <p>
          最適化の問題は、<strong>何を決め、何を良くし、何を守るか</strong>の「形」で分類できます。
          形が分かれば、使える解き方と、得られる保証の強さがおおよそ決まります。
        </p>
        {atlas && (
          <p className="formulation-index-stats">
            {atlas.summary.formulations}の形 · 解説つき {atlas.summary.with_article} · 形どうしの関係 {atlas.summary.relations}
          </p>
        )}
      </header>

      <div className="formulation-tools">
        <label>
          形を引く
          <input
            onChange={(event) => setQuery(event.target.value)}
            placeholder="線形計画、最小二乗、配分する、外れ値…"
            type="search"
            value={query}
          />
        </label>
        <label className="formulation-toggle">
          <input
            checked={onlyArticles}
            onChange={(event) => setOnlyArticles(event.target.checked)}
            type="checkbox"
          />
          解説のある形だけ
        </label>
        <output aria-live="polite">{visibleCount}件</output>
      </div>

      {error && <p className="atlas-error" role="alert">{error.message}</p>}
      {!atlas && !error && <p role="status">辞書を読み込んでいます…</p>}

      {atlas && (
        <nav aria-label="形の系統" className="formulation-family-nav">
          {atlas.families.map((family) => (
            <a href={`#family-${family.family_id}`} key={family.family_id} onClick={(event) => {
              event.preventDefault();
              document.getElementById(`family-${family.family_id}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
            }}>
              {family.title_ja}
            </a>
          ))}
        </nav>
      )}

      {atlas?.families.map((family) => {
        const members = family.problem_ids
          .map((id) => byId.get(id))
          .filter((item): item is Formulation => Boolean(item))
          .filter((item) => formulationMatches(item, query) && (!onlyArticles || item.maturity !== "skeleton"));
        if (members.length === 0) return null;
        return (
          <section aria-labelledby={`family-${family.family_id}`} className="formulation-family" key={family.family_id}>
            <header>
              <p className="formulation-lens">{LENS_LABELS[family.lens]}</p>
              <h2 id={`family-${family.family_id}`} tabIndex={-1}>{family.title_ja}</h2>
              <p>{family.summary_ja}</p>
            </header>
            <div className="formulation-card-grid">
              {members.map((item) => (
                <Link className={`formulation-card formulation-card-${item.maturity}`} key={item.problem_id} to={`/formulations/${item.problem_id}`}>
                  <span className="formulation-card-title">
                    <strong>{item.name_ja}</strong>
                    <small lang="en">{item.name_en}</small>
                  </span>
                  <span className="formulation-card-math" dangerouslySetInnerHTML={{ __html: item.standard_form_html }} />
                  <span className="formulation-card-reading">{item.reading_ja}</span>
                  <MaturityBadge item={item} />
                </Link>
              ))}
            </div>
          </section>
        );
      })}
    </section>
  );
}

export function FormulationPage() {
  const { problemId = "" } = useParams();
  const { atlas, error } = useAtlas();
  const [article, setArticle] = useState<AtlasContentPage | null>();
  const [articleError, setArticleError] = useState(false);
  const formulation = atlas?.formulations.find((item) => item.problem_id === problemId);

  useEffect(() => {
    setArticle(undefined);
    setArticleError(false);
    if (!formulation) return;
    if (!formulation.content_id) {
      setArticle(null);
      return;
    }
    let active = true;
    void loadContentIndex().then(
      (index) => {
        if (active) setArticle(index.pages.find((page) => page.content_id === formulation.content_id) ?? null);
      },
      () => { if (active) setArticleError(true); },
    );
    return () => { active = false; };
  }, [formulation]);

  useEffect(() => {
    if (formulation) document.title = `${formulation.name_ja} | 定式化の辞書 | Optimization Compass`;
  }, [formulation]);

  if (atlas && !formulation) {
    return <NotFoundPage detail={new EntityNotFoundError("定式化ID", problemId).message} />;
  }
  if (!atlas || !formulation) {
    return (
      <section className="atlas-page formulation-detail">
        {error ? <p className="atlas-error" role="alert">{error.message}</p> : <p role="status">定式化を読み込んでいます…</p>}
      </section>
    );
  }

  const family = atlas.families.find((item) => item.family_id === formulation.family_id);
  const neighbors = compassNeighbors(atlas, formulation.problem_id);
  const candidates = formulation.methods.filter((method) => method.role === "candidate");
  const avoided = formulation.methods.filter((method) => method.role === "avoid");

  return (
    <article className="atlas-page formulation-detail">
      <header className="formulation-hero">
        <p className="eyebrow">
          <Link to={`/formulations#family-${formulation.family_id}`}>定式化の辞書 / {family?.title_ja}</Link>
        </p>
        <h1>{formulation.name_ja}</h1>
        <p className="formulation-hero-en" lang="en">{formulation.name_en}</p>
        <p className="formulation-hero-reading">{formulation.reading_ja}</p>
        <figure className="formulation-standard-form">
          <figcaption>標準形</figcaption>
          <div dangerouslySetInnerHTML={{ __html: formulation.standard_form_html }} />
        </figure>
        <dl className="formulation-descriptors">
          {formulation.descriptors.map((descriptor) => (
            <div key={descriptor.field}>
              <dt>{descriptor.label_ja}</dt>
              <dd>{descriptor.value_label_ja}</dd>
            </div>
          ))}
        </dl>
      </header>

      {articleError && <p className="atlas-error" role="alert">解説の読み込みに失敗しました。ページを再読み込みしてください。</p>}
      {article === undefined && !articleError && <p role="status">解説を読み込んでいます…</p>}
      {article && (
        <section aria-label="解説" className="formulation-article content-detail">
          <CompiledContent page={article} />
        </section>
      )}
      {article === null && (
        <section className="formulation-stub">
          <h2>この形の解説はまだありません</h2>
          <p>
            標準形・見分け方・近い形・解き方の候補は、上と下に示したデータから読めます。
            問題文の手がかりを確かめ、近い形や候補手法の解説へ進めます。
          </p>
        </section>
      )}

      {!article && article !== undefined && (
      <section aria-labelledby="formulation-cues" className="formulation-cues">
        <h2 id="formulation-cues">この定式化を検討する課題</h2>
        <ul>{formulation.cues_ja.map((cue) => <li key={cue}>{cue}</li>)}</ul>
      </section>


      )}
      {neighbors.length > 0 && <FormulationCompass current={formulation} neighbors={neighbors} />}

      <details className="formulation-methods">
        <summary>この問題に対応するソルバー・手法</summary>
        {formulation.alternatives.length > 0 && (
          <p className="formulation-alternatives">
            <strong>汎用の最適化より先に確かめる:</strong>{" "}
            {formulation.alternatives.map((alternative) => alternative.name_ja).join(" / ")}
          </p>
        )}
        {candidates.length > 0 ? (
          <ul className="formulation-method-list">
            {candidates.map((method) => (
              <li key={method.method_id}>
                <Link to={`/methods/${method.method_id}`}>{method.name_ja}</Link>
                <span className={`formulation-fit formulation-fit-${method.fit_level}`}>{method.fit_label_ja}</span>
              </li>
            ))}
          </ul>
        ) : <p>この形に結び付いた手法の適合データはまだありません。</p>}
        {avoided.length > 0 && (
          <>
            <h3>既定の選択にしない手法</h3>
            <ul className="formulation-method-list formulation-method-list-avoid">
              {avoided.map((method) => (
                <li key={method.method_id}>
                  <Link to={`/methods/${method.method_id}`}>{method.name_ja}</Link>
                  <span className="formulation-fit formulation-fit-avoid">{method.fit_label_ja}</span>
                </li>
              ))}
            </ul>
          </>
        )}
        <p className="formulation-note">適合度は、この形の典型的な条件での目安です。一般的な手法の順位ではありません。</p>
      </details>

      {formulation.cases.length > 0 && (
        <section aria-labelledby="formulation-cases" className="formulation-cases">
          <h2 id="formulation-cases">この形の実例</h2>
          <ul>
            {formulation.cases.map((example) => (
              <li key={example.case_id}><Link to={`/gallery/${example.case_id}`}>{example.title_ja} →</Link></li>
            ))}
          </ul>
        </section>
      )}

      <footer className="formulation-footer">
        <small>根拠</small>
        <EvidenceLinks sourceIds={formulation.source_ids} />
      </footer>
    </article>
  );
}

const DIRECTION_TITLES: Record<CompassDirection, string> = {
  north: "一般化：条件を広げる",
  west: "元の問題からの変換",
  east: "緩和・等価な書き換え",
  south: "特殊化：条件を絞る",
  contrast: "比較：異なる目的・条件",
};

function FormulationCompass({ current, neighbors }: { current: Formulation; neighbors: CompassNeighbor[] }) {
  const group = (direction: CompassDirection) => neighbors.filter((item) => item.direction === direction);
  const cell = (direction: CompassDirection) => {
    const items = group(direction);
    return (
      <div className={`formulation-compass-cell formulation-compass-${direction}`} data-empty={items.length === 0 || undefined}>
        <h3>{DIRECTION_TITLES[direction]}</h3>
        <span className="formulation-compass-origin">{current.name_ja} {direction === "contrast" ? "≠" : direction === "west" ? "←" : "→"}</span>
        {items.length === 0 ? null : (
          <ul>
            {items.map(({ formulation, relation }) => {
              const outgoing = relation.from === current.problem_id;
              return (
                <li key={`${relation.type}:${relation.from}:${relation.to}`}>
                  <Link to={`/formulations/${formulation.problem_id}`}>{formulation.name_ja}</Link>
                  <span className="formulation-compass-verb">
                    {relationSentence(relation.type, outgoing, formulation.name_ja)}
                  </span>
                  <details className="formulation-compass-condition"><summary>関係が成り立つ条件</summary><span className="formulation-compass-note">{relation.note_ja}</span></details>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    );
  };
  return (
    <section aria-labelledby="formulation-compass-title" className="formulation-compass">
      <h2 id="formulation-compass-title">定式化のコンパス</h2>
      <p className="formulation-compass-lead">
        学んだ問題を中心に、条件を広げる・絞る・書き換える関係をたどれます。各リンクの「条件」で、関係が成り立つ範囲を確認できます。
      </p>
      <div className="formulation-compass-grid">
        {cell("north")}
        {cell("west")}
        <div className="formulation-compass-center" aria-hidden="true">
          <span>いま学んだ問題</span>
          <strong>{current.name_ja}</strong>
        </div>
        {cell("east")}
        {cell("south")}
      </div>
      {group("contrast").length > 0 && cell("contrast")}
    </section>
  );
}
