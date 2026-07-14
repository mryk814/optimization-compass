import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { parseSiteManifest, type SiteManifest } from "../../contracts/manifest";
import { parseSiteData, type SiteData, type SiteQuestion } from "../../contracts/site-data";
import {
  parseViewSpec,
  safeHttpUrl,
  type ViewSpec,
} from "../../contracts/viewspec";
import {
  toRecommendationAnswers,
  type AtlasCompatibilityCatalog,
} from "../../state/atlas-state";
import { useAtlasState } from "../../state/useAtlasState";
import { useAtlasNavigation } from "../../state/atlas-navigation";
import { resolveRelatedNodeId } from "../map/map-state";
import { findEntity } from "../../contracts/entity-links";
import { useEntityLinks } from "../../state/entity-links";
import { updateDiagnosticAnswer } from "./diagnose-state";
import { EvidenceLinks } from "../evidence/EvidenceLinks";
import {
  recommend,
  type EntityRecommendation,
  type RecommendationResult,
} from "./recommend";

interface DiagnoseArtifacts {
  manifest: SiteManifest;
  data: SiteData;
  view: ViewSpec;
}

const SUPPORTED_VIEW_VERSION = "1.0.0";
const RECOMMENDATION_PATH = "recommendation/site-data.json";
const VIEW_PATH = "views/problem-structure.json";

type LoadState =
  | { status: "loading" }
  | { status: "error"; error: Error }
  | ({ status: "ready" } & DiagnoseArtifacts);

async function json(url: string): Promise<unknown> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url} の読み込みに失敗しました (${response.status})。`);
  return response.json() as Promise<unknown>;
}

async function loadArtifacts(): Promise<DiagnoseArtifacts> {
  const baseUrl = (import.meta as ImportMeta & { env: { BASE_URL: string } }).env.BASE_URL;
  const [rawManifest, rawData, rawView] = await Promise.all([
    json(`${baseUrl}data/manifest.json`),
    json(`${baseUrl}data/recommendation/site-data.json`),
    json(`${baseUrl}data/views/problem-structure.json`),
  ]);
  let parsedManifest: SiteManifest;
  try {
    parsedManifest = parseSiteManifest(rawManifest);
  } catch (caught) {
    const detail = caught instanceof Error ? caught.message : String(caught);
    const scope = detail.startsWith("views[") ? "manifest ViewSpec" : "manifest";
    throw new Error(`${scope} の検証に失敗しました: ${detail}`);
  }
  const data = parseSiteData(rawData);
  const view = parseViewSpec(rawView);
  const manifestView = parsedManifest.views.find((item) => item.view_id === view.view_id);
  if (parsedManifest.recommendation.path !== RECOMMENDATION_PATH) {
    throw new Error(`manifest recommendation path が許可値 ${RECOMMENDATION_PATH} と一致しません。`);
  }
  if (!manifestView || manifestView.path !== VIEW_PATH) {
    throw new Error(`manifest ViewSpec path が許可値 ${VIEW_PATH} と一致しません。`);
  }
  if (
    parsedManifest.dataset_version !== data.dataset_version ||
    view.dataset_version !== data.dataset_version
  ) {
    throw new Error(
      `manifest・SiteData・ViewSpec のデータ版が一致しません (${parsedManifest.dataset_version} / ${data.dataset_version} / ${view.dataset_version})。`,
    );
  }
  if (parsedManifest.recommendation.version !== data.contract_version) {
    throw new Error("manifest と SiteData のartifact版が一致しません。");
  }
  if (manifestView.version !== SUPPORTED_VIEW_VERSION || view.version !== SUPPORTED_VIEW_VERSION) {
    throw new Error(`manifest / ViewSpec version は ${SUPPORTED_VIEW_VERSION} である必要があります。`);
  }
  return { manifest: parsedManifest, data, view };
}

function catalogFromArtifacts(data: SiteData, view: ViewSpec): AtlasCompatibilityCatalog {
  return {
    datasetVersion: data.dataset_version,
    viewId: view.view_id,
    viewVersion: view.version,
    nodeIds: new Set(view.nodes.map((node) => node.node_id)),
    questions: Object.fromEntries(
      data.questions.map((question) => [
        question.question_id,
        { answerType: question.answer_type, allowedAnswers: question.allowed_answers },
      ]),
    ),
  };
}

function Question({
  question,
  answer,
  onChange,
}: {
  question: SiteQuestion;
  answer: ReturnType<typeof useAtlasState>["state"]["answers"][string] | undefined;
  onChange(action: "set" | "toggle" | "not_applicable" | "clear", value?: string): void;
}) {
  const selected = (value: string) =>
    answer?.status === "unknown"
      ? value === "unknown"
      : answer?.status === "answered" && answer.values.includes(value);
  return (
    <fieldset className="diagnose-question">
      <legend>{question.question_ja}</legend>
      {question.beginner_wording !== question.question_ja && <p>{question.beginner_wording}</p>}
      <div className="diagnose-choice-list">
        {question.choices.map((choice) => (
          <button
            aria-pressed={selected(choice.value)}
            key={choice.value}
            onClick={() =>
              onChange(question.answer_type === "multi_choice" ? "toggle" : "set", choice.value)
            }
            type="button"
          >
            {choice.label_ja}
          </button>
        ))}
        <button
          aria-pressed={answer?.status === "not_applicable"}
          onClick={() => onChange("not_applicable")}
          type="button"
        >
          該当なし
        </button>
        <button disabled={answer === undefined} onClick={() => onChange("clear")} type="button">
          回答をクリア
        </button>
      </div>
    </fieldset>
  );
}

function SourceLinks({ sourceIds, data }: { sourceIds: readonly string[]; data: SiteData }) {
  void data;
  return <EvidenceLinks sourceIds={sourceIds} />;
}

function ResultCard({
  item,
  data,
  onMap,
}: {
  item: EntityRecommendation;
  data: SiteData;
  onMap?(methodId: string): void;
}) {
  const links = useEntityLinks();
  const canonicalMethod = links.status === "ready"
    ? findEntity(links.index, "method", item.entity_id)
    : undefined;
  return (
    <article className="diagnose-result-card">
      <div className="diagnose-result-heading">
        <h3>{canonicalMethod?.canonical_url ? <Link to={canonicalMethod.canonical_url}>{item.name}</Link> : item.name}</h3>
        {onMap && <button onClick={() => onMap(item.entity_id)} type="button">地図で見る</button>}
      </div>
      {item.summary && <p>{item.summary}</p>}
      {item.reasons.length > 0 && <ul>{item.reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul>}
      {item.warnings.map((warning) => <p className="diagnose-warning" key={warning}>{warning}</p>)}
      {item.implementations.length > 0 && (
        <div className="diagnose-implementations">
          <strong>実装候補</strong>
          <ul>
            {item.implementations.map((implementation) => {
              const docs = safeHttpUrl(implementation.official_docs_url);
              return (
                <li key={implementation.implementation_id}>
                  {docs ? <a href={docs} rel="noreferrer" target="_blank">{implementation.library_name || implementation.solver_name}</a> : (implementation.library_name || implementation.solver_name)}
                </li>
              );
            })}
          </ul>
        </div>
      )}
      <SourceLinks data={data} sourceIds={item.source_ids} />
    </article>
  );
}

function ResultBand({
  title,
  items,
  data,
  onMap,
}: {
  title: string;
  items: EntityRecommendation[];
  data: SiteData;
  onMap?(methodId: string): void;
}) {
  return (
    <section className="diagnose-result-band">
      <h2>{title}</h2>
      {items.length === 0 ? <p className="diagnose-empty">該当なし</p> : items.map((item) => <ResultCard data={data} item={item} key={item.entity_id} onMap={onMap} />)}
    </section>
  );
}

function Results({
  result,
  data,
  onMethodMap,
}: {
  result: RecommendationResult;
  data: SiteData;
  onMethodMap(methodId: string): void;
}) {
  return (
    <div className="diagnose-results">
      <ResultBand data={data} items={result.alternatives_first} title="代替解法" />
      <ResultBand data={data} items={result.first_choices} onMap={onMethodMap} title="第一候補" />
      <ResultBand data={data} items={result.conditional_choices} onMap={onMethodMap} title="条件付き候補" />
      <ResultBand data={data} items={result.excluded_methods} onMap={onMethodMap} title="除外候補" />
      <section className="diagnose-result-band">
        <h2>関連する問題型</h2>
        {result.candidate_problem_archetypes.map((item) => <ResultCard data={data} item={item} key={item.entity_id} />)}
      </section>
      <section className="diagnose-result-band">
        <h2>追加確認</h2>
        <ul>{result.followups.map((item, index) => <li key={`${item.question_id}:${index}`}>{item.explanation}</li>)}</ul>
      </section>
      <section className="diagnose-trace">
        <h2>判定トレース</h2>
        <p>{result.trace.map((item) => item.rule_id).join(" · ") || "一致規則なし"}</p>
        <SourceLinks data={data} sourceIds={[...new Set(result.trace.flatMap((item) => item.source_ids))]} />
      </section>
      {result.warnings.map((warning) => <p className="diagnose-warning" key={warning}>{warning}</p>)}
      <p className="diagnose-disclaimer">{result.disclaimer}</p>
    </div>
  );
}

function LoadedDiagnose({ data, view }: Pick<DiagnoseArtifacts, "data" | "view">) {
  const catalog = useMemo(() => catalogFromArtifacts(data, view), [data, view]);
  const atlas = useAtlasState(catalog);
  const atlasNavigation = useAtlasNavigation();
  const result = useMemo(
    () => recommend(data, toRecommendationAnswers(atlas.state), { expected_dataset_version: view.dataset_version }),
    [atlas.state, data, view.dataset_version],
  );
  const navigateMap = (selectedNodeId?: string) => {
    const next = selectedNodeId ? { ...atlas.state, selectedNodeId } : atlas.state;
    atlasNavigation.navigateWithState("/map", next);
  };
  const methodMap = (methodId: string) => navigateMap(resolveRelatedNodeId(view.nodes, "method", methodId));
  const expensiveBlackBox = Object.values(atlas.state.answers).some(
    (answer) => answer.status === "answered" && answer.values.includes("hours_or_more"),
  ) || result.first_choices.some((item) => item.entity_id === "M_BAYESIAN_OPT_GP");

  if (atlas.error) {
    return (
      <section className="diagnose-error" role="alert">
        <h2>URL の状態を復元できません</h2>
        <p>{atlas.error.message}</p>
        <button onClick={atlas.reset} type="button">状態をリセット</button>
      </section>
    );
  }
  return (
    <>
      {atlas.warnings.length > 0 && <div className="diagnose-warning-list" role="status">{atlas.warnings.map((warning) => <p key={warning}>{warning}</p>)}</div>}
      {atlasNavigation.error && <p className="diagnose-error" role="alert">{atlasNavigation.error.message}</p>}
      <div className="diagnose-layout">
        <section className="diagnose-form" aria-label="診断条件">
          {data.questions.map((question) => (
            <Question
              answer={atlas.state.answers[question.question_id]}
              key={question.question_id}
              onChange={(action, value) => atlas.setState((current) => updateDiagnosticAnswer(current, question.question_id, question.answer_type, action, value))}
              question={question}
            />
          ))}
        </section>
        <aside className="diagnose-result-pane">
          <div className="diagnose-result-toolbar"><button onClick={() => navigateMap()} type="button">地図上で見る</button></div>
          {expensiveBlackBox && <aside className="bo-route-card"><strong>高価なblack-boxを選ぶ流れを見る</strong><p>観測からsurrogateとExpected Improvementが更新される様子を固定予算で再生できます。</p><Link to="/theater/bayesian-optimization">Bayesian Optimization Theaterへ</Link></aside>}
          <Results data={data} onMethodMap={methodMap} result={result} />
        </aside>
      </div>
    </>
  );
}

export function DiagnosePage() {
  const [loadState, setLoadState] = useState<LoadState>({ status: "loading" });
  useEffect(() => {
    let active = true;
    void loadArtifacts().then(
      (artifacts) => { if (active) setLoadState({ status: "ready", ...artifacts }); },
      (caught: unknown) => { if (active) setLoadState({ status: "error", error: caught instanceof Error ? caught : new Error(String(caught)) }); },
    );
    return () => { active = false; };
  }, []);
  return (
    <section className="diagnose-page">
      <header className="diagnose-header"><p className="eyebrow">Offline Diagnosis</p><h1>診断</h1><p>条件を選ぶと候補と除外理由をURLだけで共有できます。</p></header>
      {loadState.status === "loading" && <p role="status">診断データを読み込んでいます…</p>}
      {loadState.status === "error" && <section className="diagnose-error" role="alert"><h2>診断データを読み込めませんでした</h2><p>{loadState.error.message}</p></section>}
      {loadState.status === "ready" && <LoadedDiagnose data={loadState.data} view={loadState.view} />}
    </section>
  );
}
