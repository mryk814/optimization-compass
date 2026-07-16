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
        <p className="eyebrow">Method Theater · One run, one mechanism</p>
        <h1>Method Theater</h1>
        <p>一つの固定runを再生し、更新・評価・停止の理由を読みます。条件を揃えた差の判断はCompareで行います。</p>
      </header>
      <PageOrientation
        limits="Theaterは固定scenarioの機構を理解する画面です。一つのrunから一般的な手法順位は結論づけません。"
        next={[{ label: "Compareで条件を揃えて比べる", to: "/compare" }, { label: "Caseから探す", to: "/gallery" }, { label: "手法の教材を読む", to: "/learn" }]}
        purpose="scenarioごとの一手を再生し、何が観測され、なぜ止まったかを目で追います。"
        readingSteps={["目的または問題domainでscenarioを絞ります。", "primaryとvariantを同じfamily内で選びます。", "runを再生し、Case・Compareへ同じcontextで戻ります。"]}
      />
      <div className="theater-catalog-filters" aria-label="Theater catalog filters">
        <label>見る目的<select aria-label="見る目的" value={purpose} onChange={(event) => setPurpose(event.target.value)}><option value="all">すべて</option>{Object.entries(purposeLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
        <label>問題domain<select aria-label="問題domain" value={domain} onChange={(event) => setDomain(event.target.value as typeof domain)}><option value="all">すべて</option>{["continuous", "constrained", "discrete", "black-box", "multi-objective"].map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
        <span aria-live="polite">{visible.length} / {catalog.filter((entry) => entry.publicationStatus === "published").length} scenarios</span>
      </div>
      <p className="atlas-note">Catalogはpublished scenarioのみ表示します。draft / hiddenは公開導線へ出しません。</p>
      {error && <p className="atlas-error" role="alert">{error.message}</p>}
      {(!scenarios || links.status === "loading") && !error && <p role="status">scenario catalogを読み込み中…</p>}
      <div className="theater-family-list" aria-label="Theaterのscenario catalog">
        {[...families.entries()].map(([familyId, entries]) => {
          const primary = entries.find((entry) => entry.scenario.lesson.comparison_role === "primary_example") ?? entries[0];
          return (
            <section className="theater-family" key={familyId}>
              <header><span>{rendererLabels[primary.scenario.artifact.renderer_family]} · {primary.domain}</span><h2>{primary.methods[0]?.label ?? primary.scenario.runs[0]?.method_id}</h2><small>{entries.length} scenario{entries.length === 1 ? "" : "s"}</small></header>
              <div className="theater-card-grid">
                {entries.map((entry) => <Link className="theater-card" key={entry.scenario.scenario_id} to={entry.route}>
                  <span>{purposeLabels[entry.scenario.purpose]} · {entry.scenario.lesson.comparison_role}</span>
                  <h3>{entry.scenario.title_ja}</h3>
                  <p>{entry.scenario.lesson.learning_objective.ja}</p>
                  <small>{entry.journey ? `Case: ${entry.journey.label}` : `Problem: ${entry.scenario.problem_instance_id}`}</small>
                  <small>{entry.difficulty} · {entry.publicationStatus} · {entry.scenario.experiment.budget.value} evaluations →</small>
                </Link>)}
              </div>
            </section>
          );
        })}
      </div>
      {scenarios && links.status === "ready" && visible.length === 0 && <p className="atlas-note">該当する公開scenarioはありません。</p>}
    </section>
  );
}
