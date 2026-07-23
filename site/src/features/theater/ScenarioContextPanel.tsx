import { useEffect, useMemo, useState } from "react";

import { findEntity, relatedEntities } from "../../contracts/entity-links";
import {
  parseLearningJourneyIndex,
  type LearningJourney,
} from "../../contracts/learning-journeys";
import {
  parseVisualizationScenarioIndex,
  type VisualizationScenario,
} from "../../contracts/visualization-scenarios";
import { siteBaseUrl } from "../../data/base-url";
import { useEntityLinks } from "../../state/entity-links";
import { JourneyLink } from "../../state/journey-navigation";
import { scenarioFamilyId, scenarioRoute } from "./scenario-catalog";

type Context = { journey?: LearningJourney; scenarios: VisualizationScenario[] };

export function ScenarioContextPanel({ scenario }: { scenario: VisualizationScenario }) {
  const links = useEntityLinks();
  const [context, setContext] = useState<Context>();
  useEffect(() => {
    const controller = new AbortController();
    const load = async () => {
      const [journeyResponse, scenarioResponse] = await Promise.all([
        fetch(`${siteBaseUrl()}data/learning-journeys.json`, { signal: controller.signal }),
        fetch(`${siteBaseUrl()}data/visualization-scenarios.json`, { signal: controller.signal }),
      ]);
      if (!journeyResponse.ok || !scenarioResponse.ok) throw new Error("シナリオの関連情報を読み込めませんでした。");
      const journeys = parseLearningJourneyIndex(await journeyResponse.json());
      const scenarios = parseVisualizationScenarioIndex(await scenarioResponse.json());
      setContext({
        journey: journeys.journeys.find((journey) => journey.scenarios.some((item) => item.scenario_id === scenario.scenario_id)),
        scenarios: scenarios.scenarios,
      });
    };
    void load().catch(() => {
      if (!controller.signal.aborted) setContext({ scenarios: [] });
    });
    return () => controller.abort();
  }, [scenario.scenario_id]);
  const relatedComparisons = useMemo(() => {
    if (links.status !== "ready") return [];
    const entity = findEntity(links.index, "scenario", scenario.scenario_id);
    return entity ? relatedEntities(links.index, entity, "comparison") : [];
  }, [links, scenario.scenario_id]);
  const alternates = context?.scenarios.filter((candidate) => (
    candidate.scenario_id !== scenario.scenario_id
    && scenarioFamilyId(candidate) === scenarioFamilyId(scenario)
  )) ?? [];
  const comparisonLinks = new Map([
    ...(context?.journey?.comparisons ?? []).map((item) => [item.comparison_id, item.canonical_url] as const),
    ...relatedComparisons.flatMap((item) => item.canonical_url ? [[item.entity_id, item.canonical_url] as const] : []),
  ]);
  return (
    <section className="scenario-context-panel" aria-label="ケースとシナリオの関連情報">
      <header><span>1回の実行で機構を見る</span><h2>このrunで見るもの</h2><p>{scenario.lesson.learning_objective.ja}</p></header>
      <dl className="scenario-context-grid">
        <div><dt>観測する値 (Observables)</dt><dd>{scenario.lesson.primary_observables.map((item) => item.label_ja).join(" / ")}</dd></div>
        <div>
          <dt>実行の範囲</dt>
          <dd>{new Set(scenario.runs.map((run) => run.method_id)).size}手法 · 1問題インスタンス · {scenario.runs.length}run</dd>
        </div>
      </dl>
      <details className="scenario-identifiers">
        <summary>識別子を確認</summary>
        <dl>
          <div><dt>問題 (Problem)</dt><dd>{scenario.problem_definition_id}</dd></div>
          <div><dt>問題インスタンス (Instance)</dt><dd>{scenario.problem_instance_id}</dd></div>
          <div><dt>手法 (Method)</dt><dd>{[...new Set(scenario.runs.map((run) => run.method_id))].join(" / ")}</dd></div>
        </dl>
      </details>
      {context?.journey ? <div className="scenario-case-formulation" tabIndex={0}>
        <h3>ケース: {context.journey.title_ja}</h3>
        <p>{context.journey.learning_objective}</p>
        <p><strong>x</strong> <span dangerouslySetInnerHTML={{ __html: context.journey.formulation.decision_variables }} /></p>
        <p><strong>f(x)</strong> <span dangerouslySetInnerHTML={{ __html: context.journey.formulation.objective }} /></p>
        <p><strong>制約</strong> <span dangerouslySetInnerHTML={{ __html: context.journey.formulation.constraints }} /></p>
      </div> : <p className="atlas-note">この教材runはケースの学習経路に未接続です。問題インスタンスの範囲で読みます。</p>}
      <nav className="scenario-context-links" aria-label="同じ学習経路への導線">
        {context?.journey && <JourneyLink to={context.journey.canonical_url}>Caseへ戻る</JourneyLink>}
        {[...comparisonLinks.entries()].map(([id, url]) => <JourneyLink journeyPatch={{ comparisonId: id }} key={id} to={url}>Compareへ: {id}</JourneyLink>)}
        {alternates.map((item) => <JourneyLink journeyPatch={{ scenarioId: item.scenario_id }} key={item.scenario_id} to={scenarioRoute(item)}>別のシナリオ: {item.title_ja}</JourneyLink>)}
      </nav>
      <p className="scenario-run-limit"><strong>適用範囲の限界</strong> {scenario.lesson.limitations_ja}</p>
    </section>
  );
}
