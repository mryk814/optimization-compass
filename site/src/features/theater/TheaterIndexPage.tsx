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
  const families = visible.reduce((groups, entry) => {
    groups.set(entry.familyId, [...(groups.get(entry.familyId) ?? []), entry]);
    return groups;
  }, new Map<string, TheaterCatalogEntry[]>());
  return (
    <section className="atlas-page theater-index-page">
      <header className="atlas-page-header">
        <p className="eyebrow">Method Theater · 1回の実行で機構を見る</p>
        <h1>Method Theater</h1>
        <p>固定した1回の実行 (run) を再生し、更新・評価・停止の理由を読み取ります。条件を揃えた比較は Compare で行います。</p>
      </header>
      <PageOrientation
        limits="Theaterは固定したシナリオ (scenario) の機構を理解する画面です。1回のrunだけから、手法の一般的な順位は結論づけません。"
        next={[{ label: "Compareで条件を揃えて比べる", to: "/compare" }, { label: "ケースから探す", to: "/gallery" }, { label: "手法の教材を読む", to: "/learn" }]}
        purpose="シナリオごとの一手を再生し、何を観測し、なぜ停止したかを追います。"
        readingSteps={["目的または問題領域でシナリオを絞ります。", "同じ分類の主シナリオと別条件を選びます。", "実行を再生し、同じ条件のままケース・Compareへ戻ります。"]}
      />
      <div className="theater-catalog-filters" aria-label="Theaterのシナリオ絞り込み">
        <label>見る目的<select aria-label="見る目的" value={purpose} onChange={(event) => setPurpose(event.target.value)}><option value="all">すべて</option>{Object.entries(purposeLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
        <label>問題領域<select aria-label="問題領域" value={domain} onChange={(event) => setDomain(event.target.value as typeof domain)}><option value="all">すべて</option>{["continuous", "constrained", "discrete", "black-box", "multi-objective"].map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
        <span aria-live="polite">{visible.length} / {catalog.filter((entry) => entry.publicationStatus === "published").length} シナリオ</span>
      </div>
      <p className="atlas-note">カタログには公開済みシナリオだけを表示します。draft / hiddenは公開導線に出しません。</p>
      {error && <p className="atlas-error" role="alert">{error.message}</p>}
      {(!scenarios || links.status === "loading") && !error && <p role="status">シナリオカタログを読み込み中…</p>}
      <div className="theater-family-list" aria-label="Theaterのシナリオカタログ">
        {[...families.entries()].map(([familyId, entries]) => {
          const primary = entries.find((entry) => entry.scenario.lesson.comparison_role === "primary_example") ?? entries[0];
          return (
            <section className="theater-family" key={familyId}>
              <header><span>{rendererLabels[primary.scenario.artifact.renderer_family]} · {primary.domain}</span><h2>{primary.methods[0]?.label ?? primary.scenario.runs[0]?.method_id}</h2><small>{entries.length}シナリオ</small></header>
              <div className="theater-card-grid">
                {entries.map((entry) => <Link className="theater-card" key={entry.scenario.scenario_id} to={entry.route}>
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
