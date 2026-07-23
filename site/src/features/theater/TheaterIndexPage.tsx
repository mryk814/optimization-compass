import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { PageOrientation } from "../../components/PageOrientation";
import {
  parseVisualizationScenarioIndex,
  type VisualizationComparisonRole,
} from "../../contracts/visualization-scenarios";
import { siteBaseUrl } from "../../data/base-url";
import { useEntityLinks } from "../../state/entity-links";
import {
  buildTheaterCatalog,
  primaryObservableLabels,
  purposeLabels,
  rendererLabels,
  type TheaterCatalogEntry,
  type TheaterDomain,
} from "./scenario-catalog";

const structureReadingLenses = [
  {
    title: "Nested solve",
    titleJa: "内側の solve と外側の更新",
    body: "外側の目的値の改善だけでなく、内側の solve accuracy と停止条件を別の軸で追います。",
    observables: "outer progress · inner residual · solve tolerance",
  },
  {
    title: "Equilibrium / complementarity",
    titleJa: "平衡と complementarity",
    body: "目的値、残差、可行性を分けて表示し、exact な条件と penalty / smoothing の近似を混同しません。",
    observables: "residual · constraint violation · smoothing parameter",
  },
  {
    title: "Hybrid / mode",
    titleJa: "Hybrid と mode transition",
    body: "連続軌跡だけでなく、active mode の列、switching event、mode chattering を追います。",
    observables: "mode sequence · switching event · chattering",
  },
] as const;

export function TheaterIndexPage() {
  const links = useEntityLinks();
  const [scenarios, setScenarios] = useState<ReturnType<typeof parseVisualizationScenarioIndex>>();
  const [scope, setScope] = useState<"representative" | "all">("representative");
  const [purpose, setPurpose] = useState("all");
  const [domain, setDomain] = useState<"all" | TheaterDomain>("all");
  const [error, setError] = useState<Error>();
  useEffect(() => {
    const controller = new AbortController();
    void fetch(`${siteBaseUrl()}data/visualization-scenarios.json`, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error(`Visualization scenario request failed (${response.status}).`);
        return parseVisualizationScenarioIndex(await response.json());
      })
      .then(setScenarios, (caught: unknown) => {
        if (!controller.signal.aborted) setError(caught instanceof Error ? caught : new Error(String(caught)));
      });
    return () => controller.abort();
  }, []);
  const catalog = useMemo(() => (
    scenarios && links.status === "ready" ? buildTheaterCatalog(scenarios.scenarios, links.index) : []
  ), [links, scenarios]);
  const published = catalog.filter((entry) => entry.publicationStatus === "published");
  const matching = published.filter((entry) => (
    (purpose === "all" || entry.scenario.purpose === purpose)
    && (domain === "all" || entry.domain === domain)
  ));
  const visible = scope === "all" ? matching : rendererRepresentatives(matching);
  const featured = published.find((entry) => (
    entry.difficulty === "intro" && entry.scenario.lesson.comparison_role === "primary_example"
  )) ?? published[0];
  const families = visible.reduce((groups, entry) => {
    groups.set(entry.familyId, [...(groups.get(entry.familyId) ?? []), entry]);
    return groups;
  }, new Map<string, TheaterCatalogEntry[]>());
  return (
    <section className="atlas-page theater-index-page">
      <header className="atlas-page-header">
        <p className="eyebrow">動きを見る · まず1回再生する</p>
        <h1>手法の動きを見る</h1>
        <p>1回の実行を再生して、手法が何を観測し、次の点をどう決め、どこで止まったかを追います。条件をそろえて違いを見るなら「条件を比較」へ進みます。</p>
      </header>
      <PageOrientation
        limits="ここで見るのは固定した1回の実行です。この結果だけから、手法の一般的な優劣や順位は結論づけません。"
        next={[{ label: "条件を比較する", to: "/compare" }, { label: "事例から探す", to: "/gallery" }, { label: "手法の教材を読む", to: "/learn" }]}
        purpose="シナリオごとの一手を再生し、何を観測し、なぜ停止したかを追います。"
        readingSteps={["まず代表例を1つ開きます。", "再生して、観測・更新・停止の順に追います。", "条件を変えた違いを見たいときは、比較ページへ進みます。"]}
      />
      {featured && (
        <section className="theater-first-action" aria-labelledby="theater-first-action-title">
          <div>
            <p className="eyebrow">最初に押すところ</p>
            <h2 id="theater-first-action-title">代表例を1つ開いて、再生する</h2>
            <p>迷ったら入門の代表例から始めます。図を見ながら再生すると、手法の説明が一手ずつ表示されます。</p>
          </div>
          <Link className="primary-action" to={featured.route}>
            <span>代表例を再生する</span>
            <strong>{featured.scenario.title_ja}</strong>
          </Link>
        </section>
      )}
      <section className="theater-catalog-tools" aria-labelledby="theater-catalog-tools-title">
        <header>
          <p className="eyebrow">次に見る教材を選ぶ</p>
          <h2 id="theater-catalog-tools-title">見え方・目的・問題領域で絞る</h2>
        </header>
        <div className="theater-catalog-filters" aria-label="シナリオの絞り込み">
          <label>表示範囲<select aria-label="表示範囲" value={scope} onChange={(event) => setScope(event.target.value as typeof scope)}><option value="representative">見え方別の代表例</option><option value="all">すべてのシナリオ</option></select></label>
          <label>見る目的<select aria-label="見る目的" value={purpose} onChange={(event) => setPurpose(event.target.value)}><option value="all">すべて</option>{Object.entries(purposeLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
          <label>問題領域<select aria-label="問題領域" value={domain} onChange={(event) => setDomain(event.target.value as typeof domain)}><option value="all">すべて</option>{["continuous", "constrained", "discrete", "black-box", "multi-objective"].map((value) => <option key={value} value={value}>{domainLabel(value)}</option>)}</select></label>
          <span aria-live="polite">{visible.length}件を表示 · 条件一致 {matching.length}件 · 公開 {published.length}件</span>
        </div>
        <p className="atlas-note">最初は可視化方式ごとに代表例を1件ずつ表示します。すべての条件差や失敗例が必要なときだけ、表示範囲を広げます。</p>
      </section>
      {error && <p className="atlas-error" role="alert">{error.message}</p>}
      {(!scenarios || links.status === "loading") && !error && <p role="status">シナリオカタログを読み込み中…</p>}
      <div className="theater-family-list" aria-label="Theaterのシナリオカタログ">
        {[...families.entries()].map(([familyId, entries]) => {
          const primary = entries.find((entry) => entry.scenario.lesson.comparison_role === "primary_example") ?? entries[0];
          return (
            <section className="theater-family" key={familyId}>
              <header><span>{rendererLabels[primary.scenario.artifact.renderer_family]} · {domainLabel(primary.domain)}</span><h2>{primary.methods[0]?.label ?? primary.scenario.runs[0]?.method_id}</h2></header>
              <div className="theater-card-grid">
                {entries.map((entry) => <TheaterCard entry={entry} key={entry.scenario.scenario_id} />)}
              </div>
            </section>
          );
        })}
      </div>
      {scenarios && links.status === "ready" && visible.length === 0 && (
        <div className="theater-empty atlas-note">
          <p role="status">この条件に合う公開シナリオはありません。</p>
          <button type="button" onClick={() => { setScope("representative"); setPurpose("all"); setDomain("all"); }}>絞り込みを戻す</button>
        </div>
      )}
      <details className="theater-structure-guide">
        <summary>
          <span>読み方を深める</span>
          <strong>nested・equilibrium・hybrid の run で分けて見る値</strong>
          <small>高度な構造で、目的値以外に追う観測量</small>
        </summary>
        <div className="theater-structure-guide-body">
          <header>
            <p>同じ「目的値の履歴」でも、内側の solve、平衡条件、離散 mode が隠れていると読み方が変わります。Theater では、目的値と一緒に構造固有の観測量と限界を置きます。</p>
          </header>
          <div className="theater-structure-guide-grid">
            {structureReadingLenses.map((lens) => (
              <article key={lens.title}>
                <span>{lens.title}</span>
                <h3>{lens.titleJa}</h3>
                <p>{lens.body}</p>
                <small>見る値: {lens.observables}</small>
              </article>
            ))}
          </div>
          <p className="atlas-note">この3つは今後のシナリオで使う読み方の整理です。公開済みカードには、その run が宣言した primary observables だけを表示します。</p>
        </div>
      </details>
    </section>
  );
}

function TheaterCard({ entry }: { entry: TheaterCatalogEntry }) {
  const observables = primaryObservableLabels(entry);
  return (
    <Link
      className={`theater-card${entry.scenario.lesson.comparison_role === "primary_example" ? " theater-card-primary" : ""}`}
      to={entry.route}
    >
      {entry.scenario.lesson.comparison_role === "primary_example" && (
        <span className="theater-card-primary-label">まず見る代表例</span>
      )}
      <span>{purposeLabels[entry.scenario.purpose]} · {comparisonRoleLabel(entry.scenario.lesson.comparison_role)}</span>
      <h3>{entry.scenario.title_ja}</h3>
      <p>{entry.scenario.lesson.learning_objective.ja}</p>
      <small className="theater-card-observables">観測: {summarizeLabels(observables)}</small>
      {entry.journey && <small>ケース: {entry.journey.label}</small>}
      <div className="theater-card-footer">
        <small>{difficultyLabel(entry.difficulty)} · 評価 {entry.scenario.experiment.budget.value}回</small>
        <strong>再生する →</strong>
      </div>
    </Link>
  );
}

function rendererRepresentatives(entries: TheaterCatalogEntry[]): TheaterCatalogEntry[] {
  const representatives = new Map<string, TheaterCatalogEntry>();
  entries.forEach((entry) => {
    const renderer = entry.scenario.artifact.renderer_family;
    const current = representatives.get(renderer);
    if (!current || (
      entry.scenario.lesson.comparison_role === "primary_example"
      && current.scenario.lesson.comparison_role !== "primary_example"
    )) {
      representatives.set(renderer, entry);
    }
  });
  const representativeIds = new Set([...representatives.values()].map((entry) => entry.scenario.scenario_id));
  return entries.filter((entry) => representativeIds.has(entry.scenario.scenario_id));
}

function summarizeLabels(labels: string[]): string {
  return labels.length <= 2 ? labels.join(" · ") : `${labels.slice(0, 2).join(" · ")} · ほか${labels.length - 2}件`;
}

function comparisonRoleLabel(role: VisualizationComparisonRole): string {
  const labels: Record<VisualizationComparisonRole, string> = {
    primary_example: "代表例",
    sensitivity_variant: "条件差",
    failure_contrast: "失敗例",
    baseline: "基準",
  };
  return labels[role];
}

function difficultyLabel(difficulty: TheaterCatalogEntry["difficulty"]): string {
  return difficulty === "intro" ? "入門" : "中級";
}

function domainLabel(domain: string): string {
  return {
    continuous: "連続",
    constrained: "制約つき",
    discrete: "離散",
    "black-box": "ブラックボックス",
    "multi-objective": "多目的",
  }[domain] ?? domain;
}
