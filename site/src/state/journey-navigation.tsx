import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, type LinkProps } from "react-router-dom";

import {
  parseLearningJourneyIndex,
  type LearningJourney,
  type LearningJourneyIndex,
} from "../contracts/learning-journeys";
import { siteBaseUrl } from "../data/base-url";
import {
  decodeAtlasStateToken,
  type AtlasJourneyContext,
  type AtlasStateV1,
} from "./atlas-state";
import { buildAtlasNavigation } from "./atlas-navigation";

export type AtlasJourneyPatch = Partial<Omit<AtlasJourneyContext, "journeyId" | "caseId">>;

function decodeStateFromSearch(search: string): { state?: AtlasStateV1; error?: Error } {
  const token = new URLSearchParams(search).get("state");
  if (!token) return {};
  try {
    return { state: decodeAtlasStateToken(token) };
  } catch (caught) {
    return { error: caught instanceof Error ? caught : new Error(String(caught)) };
  }
}

export function atlasStateFromSearch(search: string): AtlasStateV1 | undefined {
  return decodeStateFromSearch(search).state;
}

export function patchJourneyState(
  state: AtlasStateV1,
  patch: AtlasJourneyPatch,
): AtlasStateV1 {
  if (!state.journey) return state;
  return { ...state, journey: { ...state.journey, ...patch } };
}

type JourneyLinkProps = Omit<LinkProps, "to"> & {
  to: string;
  atlasState?: AtlasStateV1;
  journeyPatch?: AtlasJourneyPatch;
};

export function JourneyLink({
  atlasState,
  journeyPatch,
  to,
  ...props
}: JourneyLinkProps) {
  const location = useLocation();
  const inheritedState = useMemo(
    () => atlasStateFromSearch(location.search),
    [location.search],
  );
  const baseState = atlasState ?? inheritedState;
  const nextState = baseState && journeyPatch
    ? patchJourneyState(baseState, journeyPatch)
    : baseState;
  const destination = nextState
    ? buildAtlasNavigation(to, location.search, nextState)
    : undefined;
  return <Link {...props} to={destination?.ok ? destination.to : to} />;
}

interface JourneyContextResult {
  state?: AtlasStateV1;
  journey?: LearningJourney;
  error?: Error;
}

function useJourneyContext(): JourneyContextResult {
  const { search } = useLocation();
  const decoded = useMemo(() => decodeStateFromSearch(search), [search]);
  const state = decoded.state;
  const [index, setIndex] = useState<LearningJourneyIndex>();
  const [loadError, setLoadError] = useState<Error>();
  useEffect(() => {
    if (!state?.journey) return;
    const controller = new AbortController();
    setLoadError(undefined);
    void fetch(`${siteBaseUrl()}data/learning-journeys.json`, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error(`Learning journey request failed (${response.status}).`);
        return parseLearningJourneyIndex(await response.json());
      })
      .then(setIndex, (caught: unknown) => {
        if (!controller.signal.aborted) {
          setLoadError(caught instanceof Error ? caught : new Error(String(caught)));
        }
      });
    return () => controller.abort();
  }, [state?.journey]);
  if (decoded.error) return { error: decoded.error };
  if (!state?.journey) return { state };
  if (loadError) return { state, error: loadError };
  if (!index) return { state };
  if (state.datasetVersion !== index.dataset_version) {
    return { state, error: new Error("共有URLのdataset版が現在版と異なるため、Case journeyを復元できません。Caseを開き直してください。") };
  }
  const journey = index.journeys.find((item) => item.journey_id === state.journey?.journeyId);
  if (!journey || journey.case_id !== state.journey.caseId) {
    return { state, error: new Error("共有URLのCase journeyは現在のdatasetに存在しません。") };
  }
  // A comparison may intentionally open a related scenario outside the canonical
  // journey. The Case identity is strict; selected artifacts remain navigable context.
  return { state, journey };
}

function currentStep(pathname: string): number {
  if (pathname.startsWith("/theater/") || pathname.startsWith("/traces/")) return 2;
  if (pathname.startsWith("/compare/")) return 3;
  if (pathname.startsWith("/methods/") || pathname.startsWith("/sources/")) return 4;
  return 1;
}

export function JourneyNavigation() {
  const { pathname } = useLocation();
  const { state, journey, error } = useJourneyContext();
  if (error) {
    return <p className="journey-navigation-error" role="alert">共有URLの状態を復元できません: {error.message}</p>;
  }
  if (!state?.journey) return null;
  if (!journey) {
    return <p className="journey-navigation-loading" role="status">Case journeyを復元中…</p>;
  }

  const context = state.journey;
  const scenario = journey.scenarios.find((item) => item.scenario_id === context.scenarioId)
    ?? journey.scenarios.find((item) => item.role === "primary")
    ?? journey.scenarios[0];
  const comparison = journey.comparisons.find((item) => item.comparison_id === context.comparisonId)
    ?? journey.comparisons[0];
  const methodId = context.methodId ?? journey.candidate_method_ids[0];
  const step = currentStep(pathname);
  const next = step === 1 && scenario
    ? { label: "次はTheaterで1 runを見る", to: scenario.canonical_url, patch: { scenarioId: scenario.scenario_id } }
    : step === 2 && comparison
      ? { label: "次はCompareで条件差を見る", to: comparison.canonical_url, patch: { comparisonId: comparison.comparison_id } }
      : step === 3 && methodId
        ? { label: "次は手法の前提を読む", to: `/methods/${methodId}`, patch: { methodId } }
        : { label: "このCaseへ戻る", to: journey.canonical_url, patch: {} };

  return (
    <aside className="journey-navigation" aria-label="Case learning journey">
      <div className="journey-navigation-heading">
        <span>Case journey · Step {step}/4</span>
        <strong>{journey.title_ja}</strong>
      </div>
      <nav aria-label="Case journey breadcrumb">
        <JourneyLink aria-current={step === 1 ? "page" : undefined} to={journey.canonical_url}>Case</JourneyLink>
        {scenario && <><span aria-hidden="true">›</span><JourneyLink aria-current={step === 2 ? "page" : undefined} journeyPatch={{ scenarioId: scenario.scenario_id }} to={scenario.canonical_url}>Theater</JourneyLink></>}
        {comparison && <><span aria-hidden="true">›</span><JourneyLink aria-current={step === 3 ? "page" : undefined} journeyPatch={{ comparisonId: comparison.comparison_id }} to={comparison.canonical_url}>Compare</JourneyLink></>}
        {methodId && <><span aria-hidden="true">›</span><JourneyLink aria-current={step === 4 ? "page" : undefined} journeyPatch={{ methodId }} to={`/methods/${methodId}`}>Method</JourneyLink></>}
      </nav>
      <JourneyLink className="journey-navigation-next" journeyPatch={next.patch} to={next.to}>{next.label} →</JourneyLink>
    </aside>
  );
}
