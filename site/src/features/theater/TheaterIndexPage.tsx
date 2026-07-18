import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { PageOrientation } from "../../components/PageOrientation";
import { parseVisualizationScenarioIndex } from "../../contracts/visualization-scenarios";
import { siteBaseUrl } from "../../data/base-url";
import { useEntityLinks } from "../../state/entity-links";
import {
  buildTheaterCatalog,
  purposeLabels,
  rendererLabels,
  type TheaterCatalogEntry,
  type TheaterDomain,
} from "./scenario-catalog";

export function TheaterIndexPage() {
  const links = useEntityLinks();
  const [scenarios, setScenarios] = useState<ReturnType<typeof parseVisualizationScenarioIndex>>();
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
  const visible = catalog.filter((entry) => (
    entry.publicationStatus === "published"
    && (purpose === "all" || entry.scenario.purpose === purpose)
    && (domain === "all" || entry.domain === domain)
  ));
  const featured = visible.find((entry) => (
    entry.difficulty === "intro" && entry.scenario.lesson.comparison_role === "primary_example"
  )) ?? visible[0];
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
          <p className="eyebrow">別のシナリオを探す</p>
          <h2 id="theater-catalog-tools-title">目的や問題領域で絞る</h2>
        </header>
        <div className="theater-catalog-filters" aria-label="シナリオの絞り込み">
          <label>見る目的<select aria-label="見る目的" value={purpose} onChange={(event) => setPurpose(event.target.value)}><option value="all">すべて</option>{Object.entries(purposeLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
          <label>問題領域<select aria-label="問題領域" value={domain} onChange={(event) => setDomain(event.target.value as typeof domain)}><option value="all">すべて</option>{["continuous", "constrained", "discrete", "black-box", "multi-objective"].map((value) => <option key={value} value={value}>{domainLabel(value)}</option>)}</select></label>
          <span aria-live="polite">{visible.length} / {catalog.filter((entry) => entry.publicationStatus === "published").length} シナリオ</span>
        </div>
        <p className="atlas-note">公開済みシナリオだけを表示しています。まず代表例を見てから、条件差や失敗の対比へ進めます。</p>
      </section>
      {error && <p className="atlas-error" role="alert">{error.message}</p>}
      {(!scenarios || links.status === "loading") && !error && <p role="status">シナリオカタログを読み込み中…</p>}
      <div className="theater-family-list" aria-label="Theaterのシナリオカタログ">
        {[...families.entries()].map(([familyId, entries]) => {
          const primary = entries.find((entry) => entry.scenario.lesson.comparison_role === "primary_example") ?? entries[0];
          return (
            <section className="theater-family" key={familyId}>
              <header><span>{rendererLabels[primary.scenario.artifact.renderer_family]} · {domainLabel(primary.domain)}</span><h2>{primary.methods[0]?.label ?? primary.scenario.runs[0]?.method_id}</h2><small>{entries.length}シナリオ</small></header>
              <div className="theater-card-grid">
                {entries.map((entry) => <Link className={`theater-card${entry === primary ? " theater-card-primary" : ""}`} key={entry.scenario.scenario_id} to={entry.route}>
                  <span>{purposeLabels[entry.scenario.purpose]} · {comparisonRoleLabel(entry.scenario.lesson.comparison_role)}</span>
                  <h3>{entry.scenario.title_ja}</h3>
                  <p>{entry.scenario.lesson.learning_objective.ja}</p>
                  <small>{entry.journey ? `ケース: ${entry.journey.label}` : `問題: ${entry.scenario.problem_instance_id}`}</small>
                  <small>{difficultyLabel(entry.difficulty)} · 公開済み · 評価 {entry.scenario.experiment.budget.value}回 →</small>
                </Link>)}
              </div>
            </section>
          );
        })}
      </div>
      {scenarios && links.status === "ready" && visible.length === 0 && <p className="atlas-note">該当する公開シナリオはありません。</p>}
    </section>
  );
}

function comparisonRoleLabel(role: string): string {
  return { primary_example: "代表例", contrast: "対比", sensitivity: "条件差" }[role] ?? role;
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
