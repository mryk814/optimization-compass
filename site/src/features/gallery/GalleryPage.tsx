import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";

import { OptimizationProblemPrimer } from "../../components/OptimizationProblemPrimer";
import { PageOrientation } from "../../components/PageOrientation";
import { findEntity, type EntityType, type LinkedEntity } from "../../contracts/entity-links";
import { parseGalleryIndex, type GalleryCase } from "../../contracts/gallery";
import {
  parseLearningJourneyIndex,
  type LearningJourney,
} from "../../contracts/learning-journeys";
import { siteBaseUrl } from "../../data/base-url";
import { encodeAtlasState, type AtlasStateV1 } from "../../state/atlas-state";
import { useEntityLinks } from "../../state/entity-links";
import { EvidenceLinks } from "../evidence/EvidenceLinks";
import { EntityNotFoundError, NotFoundPage } from "../navigation/NotFoundPage";
import { PromptExportLauncher } from "../prompt-export/PromptExportLauncher";

export function GalleryPage() {
  const [cases, setCases] = useState<GalleryCase[]>([]);
  const [domain, setDomain] = useState("all");
  const [error, setError] = useState<Error>();
  useEffect(() => {
    void loadGallery().then(
      (index) => setCases(index.cases),
      (caught: unknown) => setError(asError(caught)),
    );
  }, []);
  const domains = ["all", ...new Set(cases.map((item) => item.domain))];
  const filtered = useMemo(
    () => cases.filter((item) => domain === "all" || item.domain === domain),
    [cases, domain],
  );

  return (
    <section className="atlas-page gallery-page">
      <header className="atlas-page-header">
        <p className="eyebrow">Problem Gallery</p>
        <h1>ケースギャラリー</h1>
        <p>現実の問いから、定式化・1 run・比較・実装へ進む学習journeyです。</p>
      </header>
      <PageOrientation
        limits="Galleryは代表的な問題設定を学ぶためのcurated casesです。教材instanceや固定runを、そのまま実問題の保証として扱いません。"
        next={[
          { label: "この条件で診断する", to: "/diagnose" },
          { label: "問題構造Mapを見る", to: "/map" },
          { label: "手法の教材を読む", to: "/learn" },
        ]}
        purpose="実問題の問いを共通の記号で定式化し、Theater・Compare・実装へ同じケース文脈で進みます。"
        readingSteps={[
          "Domainで近い問題設定を絞ります。",
          "ケース詳細で定式化と見るべき判断を読みます。",
          "Theaterで1 runを追い、Compareで条件差を確かめます。",
        ]}
      />
      <label className="gallery-filter">
        Domain
        <select value={domain} onChange={(event) => setDomain(event.target.value)}>
          {domains.map((item) => (
            <option key={item} value={item}>{item === "all" ? "すべて" : item}</option>
          ))}
        </select>
      </label>
      {error && <p className="atlas-error" role="alert">{error.message}</p>}
      <div className="gallery-card-grid">
        {filtered.map((item) => (
          <Link className="gallery-card" key={item.case_id} to={`/gallery/${item.case_id}`}>
            <span>{item.domain} · {item.difficulty}</span>
            <h2>{item.title_ja}</h2>
            <p>{item.question}</p>
            <small>候補 {item.candidate_method_ids.length}件 · Reviewed {item.last_reviewed}</small>
          </Link>
        ))}
      </div>
    </section>
  );
}

export function GalleryCasePage() {
  const links = useEntityLinks();
  const { caseId = "" } = useParams();
  const [item, setItem] = useState<GalleryCase>();
  const [journey, setJourney] = useState<LearningJourney>();
  const [datasetVersion, setDatasetVersion] = useState<string>();
  const [error, setError] = useState<Error>();

  useEffect(() => {
    setItem(undefined);
    setJourney(undefined);
    setDatasetVersion(undefined);
    setError(undefined);
    void loadGalleryCase(caseId).then(
      ({ item: found, journey: foundJourney, datasetVersion: version }) => {
        setItem(found);
        setJourney(foundJourney);
        setDatasetVersion(version);
      },
      (caught: unknown) => setError(asError(caught)),
    );
  }, [caseId]);

  const state = item && datasetVersion ? caseState(item, datasetVersion) : undefined;
  const stateQuery = state ? `?state=${encodeAtlasState(state)}` : "";
  const entity = (type: EntityType, id: string) => (
    links.status === "ready" ? findEntity(links.index, type, id) : undefined
  );

  if (error instanceof EntityNotFoundError) return <NotFoundPage detail={error.message} />;

  const primaryScenario = journey?.scenarios.find((scenario) => scenario.role === "primary");
  const alternateScenarios = journey?.scenarios.filter((scenario) => scenario.role !== "primary") ?? [];
  const canonicalComparison = journey?.comparisons[0];
  const problemArchetype = journey ? entity("problem", journey.problem_archetype_id) : undefined;
  const sourceIds = journey && item ? [...new Set([...journey.source_ids, ...item.source_ids])] : [];

  return (
    <section className="atlas-page gallery-detail">
      <header className="gallery-detail-header">
        <div>
          <p className="eyebrow">Case learning journey</p>
          <h1>{item?.title_ja ?? "ケース詳細"}</h1>
          <p className="route-parameter">Case ID: <strong>{caseId}</strong></p>
        </div>
        {journey && <JourneyStatus journey={journey} />}
      </header>
      {error && <p className="atlas-error" role="alert">{error.message}</p>}
      {item && journey && (
        <>
          <section aria-labelledby="real-question-title" className="gallery-question-panel">
            <div>
              <p className="eyebrow">1. Real-world question</p>
              <h2 id="real-question-title">現実には、何を決めたい？</h2>
              <p>{item.question}</p>
            </div>
            {datasetVersion && (
              <PromptExportLauncher source={{ kind: "gallery", item, datasetVersion }} />
            )}
          </section>

          <OptimizationProblemPrimer
            caseFormulation={{
              decisionVariables: journey.formulation.decision_variables,
              variableDomain: journey.formulation.variable_domain_summary,
              objective: journey.formulation.objective,
              constraints: journey.formulation.constraints,
            }}
          />

          <section aria-labelledby="context-levels-title" className="gallery-hub-section">
            <header className="gallery-section-heading">
              <p className="eyebrow">3. Context</p>
              <h2 id="context-levels-title">同じ問題でも、3つの粒度を分ける</h2>
            </header>
            <div className="gallery-context-grid">
              <ContextCard label="現実の問題" title="あなたが解きたい問い">
                <p>{journey.learning_objective}</p>
                <small>現場のdata・制約・budgetは、教材には自動で引き継がれません。</small>
              </ContextCard>
              <ContextCard label="Teaching instance" title="教材用に小さく固定した問題">
                {journey.problem_instance_ids.length > 0 ? (
                  <ul>
                    {journey.problem_instance_ids.map((id) => (
                      <li key={id}>
                        {primaryScenario?.problem_instance_id === id ? (
                          <Link className="text-link" to={primaryScenario.canonical_url}><code>{id}</code></Link>
                        ) : <code>{id}</code>}
                      </li>
                    ))}
                  </ul>
                ) : <p className="gallery-missing">まだ教材instanceが接続されていません。</p>}
                <p>問題型: <EntityReference entity={problemArchetype} fallback={journey.problem_archetype_id} /></p>
              </ContextCard>
              <ContextCard label="Fixed run" title="条件を固定した1回の実行">
                {primaryScenario ? (
                  <EntityRouteLink
                    entity={entity("scenario", primaryScenario.scenario_id)}
                    fallback={`Theater: ${primaryScenario.scenario_id}`}
                    to={primaryScenario.canonical_url}
                  />
                ) : <p className="gallery-missing">このケースのprimary runは未接続です。</p>}
                <small>runの結果は、手法全体の優劣や実問題での成功保証ではありません。</small>
              </ContextCard>
            </div>
          </section>

          <section aria-labelledby="inspect-title" className="gallery-hub-section gallery-inspect-panel">
            <header className="gallery-section-heading">
              <p className="eyebrow">4. Judgment</p>
              <h2 id="inspect-title">このケースで見るべきこと</h2>
            </header>
            <div className="gallery-inspect-grid">
              <div><strong>見る</strong><p>{journey.learning_objective}</p></div>
              <div><strong>持ち帰る</strong><p>{journey.takeaway}</p></div>
              <div><strong>言い過ぎない</strong><ul>{journey.limitations.map((text) => <li key={text}>{text}</li>)}</ul></div>
            </div>
          </section>

          <section aria-labelledby="journey-actions-title" className="gallery-hub-section">
            <header className="gallery-section-heading">
              <p className="eyebrow">5–6. Observe & compare</p>
              <h2 id="journey-actions-title">次の画面へ、同じcase文脈で進む</h2>
            </header>
            <div className="gallery-action-grid">
              <JourneyAction
                available={Boolean(primaryScenario)}
                eyebrow="THEATER · ONE RUN"
                fallbackTo="/theater"
                href={primaryScenario?.canonical_url}
                missing="primary Theaterが未接続です。Theater一覧から近い動きを探せます。"
                title="固定した1 runを追う"
              >
                初期値・反復・制約違反・停止理由を、順番に観察します。
              </JourneyAction>
              <JourneyAction
                available={Boolean(canonicalComparison)}
                eyebrow="COMPARE · FIXED / CHANGED"
                fallbackTo="/compare"
                href={canonicalComparison?.canonical_url}
                missing="canonical Compareが未接続です。比較一覧から条件差を確認できます。"
                title="固定条件と変えた条件を比べる"
              >
                何を固定し、何だけを変えた比較なのかを先に確認します。
              </JourneyAction>
            </div>
            {alternateScenarios.length > 0 && (
              <div className="gallery-alternate-runs">
                <strong>補助run</strong>
                {alternateScenarios.map((scenario) => (
                  <Link className="text-link" key={scenario.scenario_id} to={scenario.canonical_url}>
                    {scenarioRoleLabel(scenario.role)}: {entity("scenario", scenario.scenario_id)?.label ?? scenario.scenario_id}
                  </Link>
                ))}
              </div>
            )}
          </section>

          <section aria-labelledby="method-roles-title" className="gallery-hub-section">
            <header className="gallery-section-heading">
              <p className="eyebrow">7. Method roles</p>
              <h2 id="method-roles-title">候補・条件付き・除外を理由で分ける</h2>
            </header>
            <div className="gallery-method-grid">
              <MethodGroup
                className="is-candidate"
                empty="候補手法は未登録です。"
                ids={journey.candidate_method_ids}
                label="候補"
                method={entity}
                reasons={new Map()}
              />
              <MethodGroup
                className="is-conditional"
                empty="条件付き候補はありません。"
                ids={journey.conditional_method_ids}
                label="条件付き"
                method={entity}
                reasons={new Map(item.conditional_methods.map((entry) => [entry.method_id, entry.reason]))}
              />
              <MethodGroup
                className="is-excluded"
                empty="明示的な除外手法はありません。"
                ids={journey.excluded_method_ids}
                label="避ける"
                method={entity}
                reasons={new Map(item.excluded_methods.map((entry) => [entry.method_id, entry.reason]))}
              />
            </div>
          </section>

          <section aria-labelledby="implementation-title" className="gallery-hub-section gallery-resource-grid">
            <div>
              <header className="gallery-section-heading">
                <p className="eyebrow">8. Implementation</p>
                <h2 id="implementation-title">実装と最小例</h2>
              </header>
              <ResourceList ids={journey.implementation_ids} type="implementation" entity={entity} />
              <details className="gallery-disclosure">
                <summary>最小Python例を見る</summary>
                <pre><code>{item.python_example}</code></pre>
              </details>
              <p className="atlas-note">{item.practical_notes}</p>
            </div>
            <div>
              <header className="gallery-section-heading">
                <p className="eyebrow">Evidence & next</p>
                <h2>根拠・限界・次の道</h2>
              </header>
              <ResourceList ids={journey.content_ids} type="content" entity={entity} />
              <nav aria-label="このケースの次の導線" className="gallery-next-links">
                <Link to={{ pathname: "/map", search: stateQuery }}>問題構造Mapで位置を確認</Link>
                <Link to={{ pathname: "/diagnose", search: stateQuery }}>この特徴で診断する</Link>
                <Link to="/gallery">別のcaseを選ぶ</Link>
              </nav>
              <small>Last reviewed {journey.last_reviewed}</small>
              <EvidenceLinks sourceIds={sourceIds} />
            </div>
          </section>
        </>
      )}
    </section>
  );
}

function JourneyStatus({ journey }: { journey: LearningJourney }) {
  return (
    <aside aria-label="学習journeyの接続状況" className={`gallery-journey-status is-${journey.status}`}>
      <strong>{journey.status === "complete" ? "Journey complete" : "Journey partial"}</strong>
      {journey.completion_reasons.length > 0 && (
        <ul>{journey.completion_reasons.map((reason) => <li key={reason}>{journeyCompletionLabel(reason)}</li>)}</ul>
      )}
    </aside>
  );
}

function ContextCard({ children, label, title }: { children: ReactNode; label: string; title: string }) {
  return <article><span>{label}</span><h3>{title}</h3>{children}</article>;
}

function JourneyAction({
  available,
  children,
  eyebrow,
  fallbackTo,
  href,
  missing,
  title,
}: {
  available: boolean;
  children: ReactNode;
  eyebrow: string;
  fallbackTo: string;
  href?: string;
  missing: string;
  title: string;
}) {
  const content = (
    <>
      <span>{eyebrow}</span>
      <h3>{title}</h3>
      <p>{available ? children : missing}</p>
      <strong>{available ? "開く →" : "一覧で探す →"}</strong>
    </>
  );
  return <Link className={`gallery-journey-action${available ? "" : " is-missing"}`} to={href ?? fallbackTo}>{content}</Link>;
}

function MethodGroup({
  className,
  empty,
  ids,
  label,
  method,
  reasons,
}: {
  className: string;
  empty: string;
  ids: string[];
  label: string;
  method: (type: EntityType, id: string) => LinkedEntity | undefined;
  reasons: Map<string, string>;
}) {
  return (
    <article className={className}>
      <h3>{label}</h3>
      {ids.length === 0 ? <p>{empty}</p> : (
        <ul>
          {ids.map((id) => {
            const target = method("method", id);
            const reason = reasons.get(id) || target?.summary || "このcaseの定式化と前提に合う主要候補です。";
            return (
              <li key={id}>
                <EntityReference entity={target} fallback={id} />
                <p>{reason}</p>
              </li>
            );
          })}
        </ul>
      )}
    </article>
  );
}

function ResourceList({
  ids,
  type,
  entity,
}: {
  ids: string[];
  type: EntityType;
  entity: (type: EntityType, id: string) => LinkedEntity | undefined;
}) {
  if (ids.length === 0) return <p className="gallery-missing">接続済みの資料はありません。</p>;
  return (
    <ul className="gallery-resource-list">
      {ids.map((id) => {
        const target = entity(type, id);
        return (
          <li key={id}>
            <EntityReference entity={target} fallback={id} />
            {target?.summary && <p>{target.summary}</p>}
          </li>
        );
      })}
    </ul>
  );
}

function EntityRouteLink({ entity, fallback, to }: { entity?: LinkedEntity; fallback: string; to: string }) {
  return <Link className="text-link" to={to}>{entity?.label ?? fallback}</Link>;
}

function EntityReference({ entity, fallback }: { entity?: LinkedEntity; fallback: string }) {
  if (entity?.canonical_url) return <Link className="text-link" to={entity.canonical_url}>{entity.label}</Link>;
  if (entity?.external_url) {
    return <a className="text-link" href={entity.external_url} rel="noreferrer" target="_blank">{entity.label}</a>;
  }
  return <strong>{entity?.label ?? fallback}</strong>;
}

export function journeyCompletionLabel(reason: string): string {
  if (reason === "missing_primary_scenario") return "primary Theater 未接続";
  if (reason === "missing_comparison") return "canonical Compare 未接続";
  return reason.replaceAll("_", " ");
}

function scenarioRoleLabel(role: LearningJourney["scenarios"][number]["role"]): string {
  if (role === "failure_contrast") return "失敗contrast";
  if (role === "sensitivity") return "感度確認";
  return "別条件";
}

export function caseState(
  item: Pick<GalleryCase, "map_node_id" | "question_answers">,
  datasetVersion: string,
): AtlasStateV1 {
  return {
    stateVersion: 1,
    datasetVersion,
    viewId: "problem-structure",
    viewVersion: "1.0.0",
    selectedNodeId: item.map_node_id,
    answers: Object.fromEntries(
      Object.entries(item.question_answers).map(([questionId, value]) => [
        questionId,
        value === "unknown"
          ? { status: "unknown", values: ["unknown"] }
          : { status: "answered", values: [value] },
      ]),
    ),
  };
}

async function loadGalleryCase(caseId: string) {
  const gallery = await loadGallery();
  const item = gallery.cases.find((candidate) => candidate.case_id === caseId);
  if (!item) throw new EntityNotFoundError("ケースID", caseId);
  const journeys = await loadLearningJourneys();
  if (journeys.dataset_version !== gallery.dataset_version) {
    throw new Error("Gallery and learning journey dataset versions do not match.");
  }
  const journey = journeys.journeys.find((candidate) => candidate.case_id === caseId);
  if (!journey) throw new Error(`ケース ${caseId} のlearning journeyが見つかりません。`);
  return { item, journey, datasetVersion: gallery.dataset_version };
}

async function loadGallery() {
  const response = await fetch(`${siteBaseUrl()}data/gallery.json`);
  if (!response.ok) throw new Error(`Gallery request failed (${response.status}).`);
  return parseGalleryIndex(await response.json());
}

async function loadLearningJourneys() {
  const response = await fetch(`${siteBaseUrl()}data/learning-journeys.json`);
  if (!response.ok) throw new Error(`Learning journey request failed (${response.status}).`);
  return parseLearningJourneyIndex(await response.json());
}

function asError(caught: unknown): Error {
  return caught instanceof Error ? caught : new Error(String(caught));
}
