import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

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
      if (!journeyResponse.ok || !scenarioResponse.ok) throw new Error("Scenario context request failed.");
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
    <section className="scenario-context-panel" aria-label="Caseとscenarioのcontext">
      <header><span>One run / mechanism</span><h2>このrunで見るもの</h2><p>{scenario.lesson.learning_objective.ja}</p></header>
      <dl className="scenario-context-grid">
        <div><dt>Problem</dt><dd>{scenario.problem_definition_id}</dd></div>
        <div><dt>Instance</dt><dd>{scenario.problem_instance_id}</dd></div>
        <div><dt>Method</dt><dd>{[...new Set(scenario.runs.map((run) => run.method_id))].join(" / ")}</dd></div>
        <div><dt>Observables</dt><dd>{scenario.lesson.primary_observables.map((item) => item.label_ja).join(" / ")}</dd></div>
      </dl>
      {context?.journey ? <div className="scenario-case-formulation">
        <h3>Case: {context.journey.title_ja}</h3>
        <p>{context.journey.learning_objective}</p>
        <p><strong>x</strong> {context.journey.formulation.decision_variables}</p>
        <p><strong>f(x)</strong> {context.journey.formulation.objective}</p>
        <p><strong>制約</strong> {context.journey.formulation.constraints}</p>
      </div> : <p className="atlas-note">この教材runはCase journeyへ未接続です。問題instanceの範囲で読みます。</p>}
      <nav className="scenario-context-links" aria-label="同じjourneyの導線">
        {context?.journey && <Link to={context.journey.canonical_url}>Caseへ戻る</Link>}
        {[...comparisonLinks.entries()].map(([id, url]) => <Link key={id} to={url}>Compare: {id}</Link>)}
        {alternates.map((item) => <Link key={item.scenario_id} to={scenarioRoute(item)}>Alternate: {item.title_ja}</Link>)}
      </nav>
      <p className="scenario-run-limit"><strong>Limit</strong> {scenario.lesson.limitations_ja}</p>
    </section>
  );
}
