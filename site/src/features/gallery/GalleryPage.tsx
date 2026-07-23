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
import {
  JourneyLink,
  type AtlasJourneyPatch,
} from "../../state/journey-navigation";
import { EvidenceLinks } from "../evidence/EvidenceLinks";
import { EntityNotFoundError, NotFoundPage } from "../navigation/NotFoundPage";
import { PromptExportLauncher } from "../prompt-export/PromptExportLauncher";

export function GalleryPage() {
  const [cases, setCases] = useState<GalleryCase[]>([]);
  const [journeys, setJourneys] = useState<LearningJourney[]>([]);
  const [domain, setDomain] = useState("all");
  const [query, setQuery] = useState("");
  const [error, setError] = useState<Error>();
  useEffect(() => {
    void Promise.all([loadGallery(), loadLearningJourneys()]).then(
      ([gallery, journeyIndex]) => {
        if (gallery.dataset_version !== journeyIndex.dataset_version) {
          throw new Error("Gallery and learning journey dataset versions do not match.");
        }
        setCases(gallery.cases);
        setJourneys(journeyIndex.journeys);
      },
      (caught: unknown) => setError(asError(caught)),
    );
  }, []);
  const domains = ["all", ...new Set(cases.map((item) => item.domain))];
  const domainCounts = useMemo(() => countCasesByDomain(cases), [cases]);
  const featuredDomainCounts = domainCounts.slice(0, 3);
  const remainingDomainCounts = domainCounts.slice(3);
  const largestDomainCount = Math.max(1, ...domainCounts.map((item) => item.count));
  const journeyByCase = useMemo(
    () => new Map(journeys.map((journey) => [journey.case_id, journey])),
    [journeys],
  );
  const normalizedQuery = query.trim().toLocaleLowerCase();
  const filtered = useMemo(
    () => cases.filter((item) => (
      (domain === "all" || item.domain === domain)
      && (
        normalizedQuery.length === 0
        || `${item.title_ja} ${item.title_en} ${item.question} ${item.domain}`
          .toLocaleLowerCase()
          .includes(normalizedQuery)
      )
    )),
    [cases, domain, normalizedQuery],
  );

  return (
    <section className="atlas-page gallery-page">
      <header className="atlas-page-header">
        <p className="eyebrow">問題事例</p>
        <h1>ケースギャラリー</h1>
        <p>現実の問いから、定式化・1回の実行・比較・実装へ進む学習の流れです。</p>
      </header>
      <PageOrientation
        limits="ここでは代表的な問題設定を学びます。教材用の問題や固定した実行を、そのまま実問題の保証として扱いません。"
        next={[
          { label: "この条件で診断する", to: "/diagnose" },
          { label: "問題構造マップを見る", to: "/map" },
          { label: "手法の教材を読む", to: "/learn" },
        ]}
        purpose="実問題の問いを共通の記号で定式化し、Theater・Compare・実装へ同じケースの条件で進みます。"
        readingSteps={[
          "問題領域で近い問題設定を絞ります。",
          "ケース詳細で定式化と見るべき判断を読みます。",
          "Theaterで1回の実行を追い、Compareで条件差を確かめます。",
        ]}
      />
      <section aria-labelledby="gallery-domain-overview-title" className="gallery-domain-overview">
        <header>
          <div>
            <p className="eyebrow">Use case coverage</p>
            <h2 id="gallery-domain-overview-title">どの分野から探す？</h2>
          </div>
          <p>掲載数です。選ぶとケースを絞り込みます。</p>
        </header>
        <div className="gallery-domain-primary">
          <DomainButtons
            activeDomain={domain}
            items={featuredDomainCounts}
            largestDomainCount={largestDomainCount}
            onSelect={setDomain}
          />
        </div>
        {remainingDomainCounts.length > 0 && (
          <details className="gallery-domain-more">
            <summary>ほか{remainingDomainCounts.length}領域を見る</summary>
            <div>
              <DomainButtons
                activeDomain={domain}
                items={remainingDomainCounts}
                largestDomainCount={largestDomainCount}
                onSelect={setDomain}
              />
            </div>
          </details>
        )}
      </section>
      <div className="gallery-toolbar">
        <label className="gallery-filter">
          領域
          <select value={domain} onChange={(event) => setDomain(event.target.value)}>
            {domains.map((item) => (
              <option key={item} value={item}>{domainLabel(item)}</option>
            ))}
          </select>
        </label>
        <label className="gallery-search">
          問いで絞る
          <input
            onChange={(event) => setQuery(event.target.value)}
            placeholder="配送、材料、実験…"
            type="search"
            value={query}
          />
        </label>
        <output aria-live="polite">{filtered.length}件</output>
      </div>
      {error && <p className="atlas-error" role="alert">{error.message}</p>}
      <div className="gallery-card-grid">
        {filtered.map((item) => {
          const journey = journeyByCase.get(item.case_id);
          return (
            <Link className="gallery-card" key={item.case_id} to={`/gallery/${item.case_id}`}>
              <span>{domainLabel(item.domain)} · {difficultyLabel(item.difficulty)}</span>
              <h2>{item.title_ja}</h2>
              <p>{item.question}</p>
              <footer>
                <small className={`gallery-card-status is-${journey?.status ?? "draft"}`}>
                  {journeyStatusLabel(journey?.status)}
                </small>
                <strong>ケースを開く →</strong>
              </footer>
            </Link>
          );
        })}
      </div>
      {filtered.length === 0 && (
        <p className="gallery-empty">条件に合うケースはありません。領域か検索語を変えてください。</p>
      )}
    </section>
  );
}

function DomainButtons({
  activeDomain,
  items,
  largestDomainCount,
  onSelect,
}: {
  activeDomain: string;
  items: Array<{ domain: string; count: number }>;
  largestDomainCount: number;
  onSelect: (domain: string) => void;
}) {
  return items.map((item) => (
    <button
      aria-pressed={activeDomain === item.domain}
      key={item.domain}
      onClick={() => onSelect(item.domain)}
      type="button"
    >
      <span>{domainLabel(item.domain)}</span>
      <span aria-hidden="true" className="gallery-domain-bar">
        <span style={{ width: `${(item.count / largestDomainCount) * 100}%` }} />
      </span>
      <strong>{item.count}</strong>
    </button>
  ));
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

  const state = item && journey && datasetVersion
    ? caseState(item, datasetVersion, journey)
    : undefined;
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
          <p className="eyebrow">ケースの学習の流れ</p>
          <h1>{item?.title_ja ?? "ケース詳細"}</h1>
        </div>
        {journey && <JourneyStatus journey={journey} />}
      </header>
      {error && <p className="atlas-error" role="alert">{error.message}</p>}
      {item && journey && (
        <>
          <section aria-labelledby="real-question-title" className="gallery-question-panel">
            <div>
              <p className="eyebrow">1. 現実の問い</p>
              <h2 id="real-question-title">現実には、何を決めたい？</h2>
              <p>{item.question}</p>
            </div>
          </section>

          <section aria-labelledby="journey-actions-title" className="gallery-hub-section">
            <header className="gallery-section-heading">
              <p className="eyebrow">2. 次に進む</p>
              <h2 id="journey-actions-title">実行を見てから、条件差を比べる</h2>
            </header>
            <div className="gallery-action-grid">
              <JourneyAction
                available={Boolean(primaryScenario)}
                eyebrow="THEATER · ONE RUN"
                fallbackTo="/theater"
                href={primaryScenario?.canonical_url}
                journeyPatch={primaryScenario ? { scenarioId: primaryScenario.scenario_id } : undefined}
                missing="主なTheaterが未接続です。Theater一覧から近い動きを探せます。"
                state={state}
                title="固定した1回の実行を追う"
              >
                初期値・反復・制約違反・停止理由を、順番に観察します。
              </JourneyAction>
              <JourneyAction
                available={Boolean(canonicalComparison)}
                eyebrow="COMPARE · FIXED / CHANGED"
                fallbackTo="/compare"
                href={canonicalComparison?.canonical_url}
                journeyPatch={canonicalComparison ? { comparisonId: canonicalComparison.comparison_id } : undefined}
                missing="比較ページが未接続です。比較一覧から条件差を確認できます。"
                state={state}
                title="固定条件と変えた条件を比べる"
              >
                何を固定し、何だけを変えた比較なのかを先に確認します。
              </JourneyAction>
            </div>
            {alternateScenarios.length > 0 && (
              <div className="gallery-alternate-runs">
                <strong>補助の実行</strong>
                {alternateScenarios.map((scenario) => (
                  <JourneyLink atlasState={state} className="text-link" journeyPatch={{ scenarioId: scenario.scenario_id }} key={scenario.scenario_id} to={scenario.canonical_url}>
                    {scenarioRoleLabel(scenario.role)}: {entity("scenario", scenario.scenario_id)?.label ?? scenario.scenario_id}
                  </JourneyLink>
                ))}
              </div>
            )}
          </section>

          <details className="gallery-formulation-disclosure">
            <summary>
              <span>3. 定式化</span>
              <strong>変数・目的・制約を確認する</strong>
              <small>必要なときに展開</small>
            </summary>
            <OptimizationProblemPrimer
              caseFormulation={{
                decisionVariables: journey.formulation.decision_variables,
                variableDomain: journey.formulation.variable_domain_summary,
                objective: journey.formulation.objective,
                constraints: journey.formulation.constraints,
              }}
            />
          </details>

          <section aria-labelledby="context-levels-title" className="gallery-hub-section">
            <header className="gallery-section-heading">
              <p className="eyebrow">4. 問題の粒度</p>
              <h2 id="context-levels-title">同じ問題でも、3つの粒度を分ける</h2>
            </header>
            <div className="gallery-context-grid">
              <ContextCard label="現実の問題" title="あなたが解きたい問い">
                <p>現場のデータ・制約・予算を加え、教材の前提との差を確認します。</p>
                <small>教材の結果を、そのまま実問題の答えにはできません。</small>
              </ContextCard>
              <ContextCard label="教材用の問題" title="教材用に小さく固定した問題">
                {journey.problem_instance_ids.length > 0 ? (
                  <ul>
                    {journey.problem_instance_ids.map((id, index) => (
                      <li key={id}>
                        {primaryScenario?.problem_instance_id === id ? (
                          <JourneyLink atlasState={state} className="text-link" journeyPatch={{ scenarioId: primaryScenario.scenario_id }} to={primaryScenario.canonical_url}>
                            {journey.problem_instance_ids.length === 1 ? "教材用の問題を開く" : `教材用の問題 ${index + 1} を開く`}
                          </JourneyLink>
                        ) : `補助の教材用問題 ${index + 1}`}
                      </li>
                    ))}
                  </ul>
                ) : <p className="gallery-missing">まだ教材用の問題が接続されていません。</p>}
                <p>問題型: <EntityReference entity={problemArchetype} fallback={journey.problem_archetype_id} /></p>
              </ContextCard>
              <ContextCard label="固定した実行" title="条件を固定した1回の実行">
                {primaryScenario ? (
                  <EntityRouteLink
                    atlasState={state}
                    entity={entity("scenario", primaryScenario.scenario_id)}
                    fallback={`Theater: ${primaryScenario.scenario_id}`}
                    journeyPatch={{ scenarioId: primaryScenario.scenario_id }}
                    to={primaryScenario.canonical_url}
                  />
                ) : <p className="gallery-missing">このケースの主な実行は未接続です。</p>}
                <small>実行結果は、手法全体の優劣や実問題での成功保証ではありません。</small>
              </ContextCard>
            </div>
          </section>

          <section aria-labelledby="inspect-title" className="gallery-hub-section gallery-inspect-panel">
            <header className="gallery-section-heading">
              <p className="eyebrow">5. 判断のポイント</p>
              <h2 id="inspect-title">このケースで見るべきこと</h2>
            </header>
            <div className="gallery-inspect-grid">
              <div><strong>持ち帰る</strong><GalleryTakeaway>{journey.takeaway}</GalleryTakeaway></div>
              <div><strong>言い過ぎない</strong><ul>{journey.limitations.map((text) => <li key={text}>{text}</li>)}</ul></div>
            </div>
          </section>

          <section aria-labelledby="method-roles-title" className="gallery-hub-section">
            <header className="gallery-section-heading">
              <p className="eyebrow">6. 手法の役割</p>
              <h2 id="method-roles-title">候補・条件付き・除外を理由で分ける</h2>
            </header>
            <div className="gallery-method-grid">
              <MethodGroup
                className="is-candidate"
                empty="候補手法は未登録です。"
                ids={journey.candidate_method_ids}
                label="候補"
                method={entity}
                openByDefault
                reasons={new Map(item.candidate_methods.map((entry) => [entry.method_id, entry.reason]))}
                state={state}
              />
              <MethodGroup
                className="is-conditional"
                empty="条件付き候補はありません。"
                ids={journey.conditional_method_ids}
                label="条件付き"
                method={entity}
                reasons={new Map(item.conditional_methods.map((entry) => [entry.method_id, entry.reason]))}
                state={state}
              />
              <MethodGroup
                className="is-excluded"
                empty="明示的な除外手法はありません。"
                ids={journey.excluded_method_ids}
                label="避ける"
                method={entity}
                reasons={new Map(item.excluded_methods.map((entry) => [entry.method_id, entry.reason]))}
                state={state}
              />
            </div>
          </section>

          <section aria-labelledby="implementation-title" className="gallery-hub-section gallery-resource-grid">
            <div>
              <header className="gallery-section-heading">
                <p className="eyebrow">7. 実装と根拠</p>
                <h2 id="implementation-title">実装と最小例</h2>
              </header>
              <ResourceList atlasState={state} ids={journey.implementation_ids} type="implementation" entity={entity} />
              {datasetVersion && (
                <PromptExportLauncher source={{ kind: "gallery", item, datasetVersion }} />
              )}
              <details className="gallery-disclosure">
                <summary>最小Python例を見る</summary>
                <pre><code>{item.python_example}</code></pre>
              </details>
              {item.practical_notes.trim() !== journey.takeaway.trim() && (
                <details className="gallery-disclosure gallery-additional-note">
                  <summary>追加の実務メモを見る</summary>
                  <p><GalleryNote>{item.practical_notes}</GalleryNote></p>
                </details>
              )}
              {!sameStringSet(item.limitations, journey.limitations) && (
                <details className="gallery-disclosure gallery-additional-note">
                  <summary>追加の限界を見る</summary>
                  <ul>{item.limitations.map((text) => <li key={text}>{text}</li>)}</ul>
                </details>
              )}
            </div>
            <div>
              <header className="gallery-section-heading">
                <p className="eyebrow">根拠と次の導線</p>
                <h2>根拠・次の導線</h2>
              </header>
              <ResourceList atlasState={state} ids={journey.content_ids} type="content" entity={entity} />
              <nav aria-label="このケースの次の導線" className="gallery-next-links">
                <Link to={{ pathname: "/map", search: stateQuery }}>問題構造Mapで位置を確認</Link>
                <Link to={{ pathname: "/diagnose", search: stateQuery }}>この特徴で診断する</Link>
                <Link to="/gallery">別のケースを選ぶ</Link>
              </nav>
              <small>確認日 {journey.last_reviewed}</small>
              <EvidenceLinks atlasState={state} sourceIds={sourceIds} />
              <details className="gallery-reference-disclosure">
                <summary>参照情報を表示</summary>
                <dl>
                  <div><dt>Case ID</dt><dd><code>{caseId}</code></dd></div>
                  <div><dt>Dataset</dt><dd><code>{datasetVersion}</code></dd></div>
                  <div>
                    <dt>Problem instance</dt>
                    <dd>{journey.problem_instance_ids.map((id) => <code key={id}>{id}</code>)}</dd>
                  </div>
                </dl>
              </details>
            </div>
          </section>
        </>
      )}
    </section>
  );
}

export function JourneyStatus({
  journey,
}: {
  journey: Pick<LearningJourney, "status" | "completion_reasons">;
}) {
  return (
    <aside
      aria-label={`学習の流れの接続状況。${journeyStatusSummary(journey.status)}`}
      className={`gallery-journey-status is-${journey.status}`}
    >
      <strong>{journeyStatusLabel(journey.status)}</strong>
      {journey.completion_reasons.length > 0 && (
        <details>
          <summary>接続状況を確認（{journey.completion_reasons.length}）</summary>
          <ul>{journey.completion_reasons.map((reason) => <li key={reason}>{journeyCompletionLabel(reason)}</li>)}</ul>
        </details>
      )}
    </aside>
  );
}

export function domainLabel(domain: string): string {
  const labels: Record<string, string> = {
    all: "すべて",
    business: "事業・施策",
    control: "制御",
    energy: "エネルギー",
    engineering: "設計・工学",
    finance: "金融",
    logistics: "物流",
    "machine-learning": "機械学習",
    manufacturing: "製造",
    operations: "運用・計画",
    "public-policy": "公共政策",
    science: "科学・推定",
  };
  return labels[domain] ?? domain;
}

export function journeyStatusLabel(status?: LearningJourney["status"]): string {
  if (status === "complete") return "定式化・実行・比較あり";
  if (status === "partial") return "定式化あり・一部準備中";
  return "準備中";
}

export function journeyStatusSummary(status?: LearningJourney["status"]): string {
  if (status === "complete") return "このケースは、定式化から実行・比較まで続けて読めます。";
  if (status === "partial") return "定式化は読めます。実行・比較は順次整備中です。";
  return "ケース本文と関連する学習素材を整備しています。";
}

export function countCasesByDomain(
  cases: Pick<GalleryCase, "domain">[],
): Array<{ domain: string; count: number }> {
  const counts = new Map<string, number>();
  cases.forEach((item) => counts.set(item.domain, (counts.get(item.domain) ?? 0) + 1));
  return [...counts.entries()]
    .map(([domain, count]) => ({ domain, count }))
    .sort((left, right) => right.count - left.count || domainLabel(left.domain).localeCompare(domainLabel(right.domain), "ja"));
}

function difficultyLabel(difficulty: GalleryCase["difficulty"]): string {
  if (difficulty === "intro") return "入門";
  if (difficulty === "intermediate") return "実践";
  return "発展";
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
  journeyPatch,
  missing,
  state,
  title,
}: {
  available: boolean;
  children: ReactNode;
  eyebrow: string;
  fallbackTo: string;
  href?: string;
  journeyPatch?: AtlasJourneyPatch;
  missing: string;
  state?: AtlasStateV1;
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
  return <JourneyLink atlasState={state} className={`gallery-journey-action${available ? "" : " is-missing"}`} journeyPatch={journeyPatch} to={href ?? fallbackTo}>{content}</JourneyLink>;
}

function MethodGroup({
  className,
  empty,
  ids,
  label,
  method,
  openByDefault = false,
  reasons,
  state,
}: {
  className: string;
  empty: string;
  ids: string[];
  label: string;
  method: (type: EntityType, id: string) => LinkedEntity | undefined;
  openByDefault?: boolean;
  reasons: Map<string, string>;
  state?: AtlasStateV1;
}) {
  return (
    <details className={`gallery-method-group ${className}`} open={openByDefault}>
      <summary>
        <strong>{label}</strong>
        <span>{ids.length}件</span>
      </summary>
      <div>
        {ids.length === 0 ? <p>{empty}</p> : (
          <ul>
            {ids.map((id) => {
              const target = method("method", id);
              const reason = reasons.get(id) || target?.summary || "このケースの定式化と前提に合う主要候補です。";
              return (
                <li key={id}>
                  <EntityReference atlasState={state} entity={target} fallback={id} journeyPatch={{ methodId: id }} />
                  <p>{reason}</p>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </details>
  );
}

export function GalleryNote({ children }: { children: string }) {
  const tokens = children.split(/(\[[^\]]+\]\(#[^)]+\)|\$[^$]+\$)/gu).filter(Boolean);
  return (
    <>
      {tokens.map((token, index) => {
        const link = token.match(/^\[([^\]]+)\]\(#([^)]+)\)$/u);
        if (link) return <Link key={`${token}-${index}`} className="text-link" to={link[2]}>{link[1]}</Link>;
        if (token.startsWith("$") && token.endsWith("$")) {
          return <code key={`${token}-${index}`} className="gallery-inline-math">{token.slice(1, -1)}</code>;
        }
        return token;
      })}
    </>
  );
}

export function GalleryTakeaway({ children }: { children: string }) {
  const { lead, detail } = splitGalleryNote(children);
  return (
    <>
      <p><GalleryNote>{lead}</GalleryNote></p>
      {detail && (
        <details className="gallery-note-disclosure">
          <summary>判断の根拠と実務上の注意を読む</summary>
          <p><GalleryNote>{detail}</GalleryNote></p>
        </details>
      )}
    </>
  );
}

export function splitGalleryNote(text: string): { lead: string; detail: string } {
  const sentenceEnd = text.indexOf("。");
  if (sentenceEnd < 0 || sentenceEnd === text.length - 1) return { lead: text, detail: "" };
  return {
    lead: text.slice(0, sentenceEnd + 1),
    detail: text.slice(sentenceEnd + 1).trim(),
  };
}

export function sameStringSet(left: string[], right: string[]): boolean {
  if (left.length !== right.length) return false;
  const sortedLeft = [...left].sort();
  const sortedRight = [...right].sort();
  return sortedLeft.every((value, index) => value === sortedRight[index]);
}

function ResourceList({
  atlasState,
  ids,
  type,
  entity,
}: {
  atlasState?: AtlasStateV1;
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
            <EntityReference atlasState={atlasState} entity={target} fallback={id} />
            {target?.summary && <p>{target.summary}</p>}
          </li>
        );
      })}
    </ul>
  );
}

function EntityRouteLink({ atlasState, entity, fallback, journeyPatch, to }: { atlasState?: AtlasStateV1; entity?: LinkedEntity; fallback: string; journeyPatch?: AtlasJourneyPatch; to: string }) {
  return <JourneyLink atlasState={atlasState} className="text-link" journeyPatch={journeyPatch} to={to}>{entity?.label ?? fallback}</JourneyLink>;
}

function EntityReference({ atlasState, entity, fallback, journeyPatch }: { atlasState?: AtlasStateV1; entity?: LinkedEntity; fallback: string; journeyPatch?: AtlasJourneyPatch }) {
  if (entity?.canonical_url) return <JourneyLink atlasState={atlasState} className="text-link" journeyPatch={journeyPatch} to={entity.canonical_url}>{entity.label}</JourneyLink>;
  if (entity?.external_url) {
    return <a className="text-link" href={entity.external_url} rel="noreferrer" target="_blank">{entity.label}</a>;
  }
  return <strong>{entity?.label ?? fallback}</strong>;
}

export function journeyCompletionLabel(reason: string): string {
  const labels: Record<string, string> = {
    case_is_draft: "ケース本文を編集中",
    invalid_source_currentness: "出典の現行性を要確認",
    missing_comparison: "比較ページ未接続",
    missing_comparison_source: "比較の出典未接続",
    missing_cross_surface_link: "関連ページ間の導線未接続",
    missing_failure_or_sensitivity_scenario: "失敗例・感度確認未接続",
    missing_implementation: "実装情報未接続",
    missing_primary_scenario: "主な実行例未接続",
    missing_problem_instance: "実行用問題インスタンス未接続",
    missing_scenario_source: "実行例の出典未接続",
    missing_static_text_alternative: "可視化のテキスト説明未整備",
    stale_case_review: "ケース内容の再確認が必要",
  };
  return labels[reason] ?? "接続状況を確認中";
}

function scenarioRoleLabel(role: LearningJourney["scenarios"][number]["role"]): string {
  if (role === "failure_contrast") return "失敗の比較";
  if (role === "sensitivity") return "感度確認";
  return "別条件";
}

export function caseState(
  item: Pick<GalleryCase, "map_node_id" | "question_answers">,
  datasetVersion: string,
  journey?: Pick<LearningJourney, "journey_id" | "case_id">,
): AtlasStateV1 {
  return {
    stateVersion: 1,
    datasetVersion,
    viewId: "problem-structure",
    viewVersion: "1.0.0",
    selectedNodeId: item.map_node_id,
    journey: journey ? { journeyId: journey.journey_id, caseId: journey.case_id } : undefined,
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
  if (!journey) throw new Error(`ケース ${caseId} の学習の流れが見つかりません。`);
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
