import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { PageOrientation } from "../../components/PageOrientation";
import {
  parseCoverageReport,
  type CoverageReport,
  type CoverageStatus,
  type SubjectType,
} from "../../contracts/coverage";
import {
  parseLearningJourneyIndex,
  type JourneyDimensionName,
  type JourneyStatus,
  type LearningJourney,
  type LearningJourneyIndex,
} from "../../contracts/learning-journeys";
import { parseSiteManifest } from "../../contracts/manifest";
import { siteBaseUrl } from "../../data/base-url";

type LoadState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; report: CoverageReport; journeys: LearningJourneyIndex };

const INVENTORY_PREVIEW_LIMIT = 24;

const statusLabels: Record<CoverageStatus, string> = {
  available: "利用可能",
  partial: "一部接続",
  missing: "未構築",
  not_applicable: "適用外",
};
const subjectTypeLabels: Record<SubjectType, string> = {
  method: "手法",
  problem: "問題型",
  feature_family: "特徴ファミリー",
};
const journeyStatusLabels: Record<JourneyStatus, string> = {
  complete: "完了",
  partial: "一部接続",
  draft: "下書き",
};
const dimensionLabels: Record<JourneyDimensionName, string> = {
  formulation: "定式化",
  canonical_problem_instance: "問題インスタンス",
  primary_scenario: "主な実行例",
  alternate_scenario: "別条件の実行例",
  canonical_comparison: "比較",
  method_roles: "手法の役割",
  implementation: "実装",
  source_review: "根拠とレビュー",
  terminology_prerequisite: "用語と前提",
  static_text_alternative: "可視化のテキスト説明",
  cross_surface_links: "画面間リンク",
  route_reachability: "到達可能な経路",
  validation_status: "参照整合性",
};
const purposeLabels: Record<string, string> = {
  application_result: "応用結果",
  comparison: "条件比較",
  failure_contrast: "失敗との比較",
  mechanism: "仕組み",
  sensitivity: "感度確認",
};
const factorLabels: Record<string, string> = {
  classification: "分類の基盤",
  demand: "利用ニーズ",
  misconception: "誤解の防止",
  visualization: "可視化の効果",
};

export function CoveragePage() {
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    void loadCoverage(controller.signal).then(
      ({ report, journeys }) => setState({ status: "ready", report, journeys }),
      (error: unknown) => {
        if (!(error instanceof DOMException && error.name === "AbortError")) {
          setState({
            status: "error",
            message: error instanceof Error ? error.message : String(error),
          });
        }
      },
    );
    return () => controller.abort();
  }, []);

  if (state.status === "loading") return <p role="status">接続状況を集計しています…</p>;
  if (state.status === "error") {
    return <p role="alert">接続状況を読み込めませんでした: {state.message}</p>;
  }
  return <CoverageView report={state.report} journeys={state.journeys} />;
}

function CoverageView({
  report,
  journeys,
}: {
  report: CoverageReport;
  journeys: LearningJourneyIndex;
}) {
  const [showTechnical, setShowTechnical] = useState(false);

  return (
    <section className="coverage-page">
      <header className="page-heading coverage-heading">
        <div>
          <p className="eyebrow">接続状況</p>
          <h1>Atlasの接続状況</h1>
          <p>教材の深さを一律にせず、期待する学習成果と実在する成果物を分けて監査します。</p>
        </div>
        <button
          aria-pressed={showTechnical}
          className="coverage-technical-toggle"
          onClick={() => setShowTechnical((current) => !current)}
          type="button"
        >
          {showTechnical ? "技術情報を隠す" : "技術情報を表示"}
        </button>
      </header>

      <PageOrientation
        limits="接続状況は学習経路の整備状態を監査します。件数や接続率だけで教材の質や手法の優劣を判断しません。日本語の説明を基準にし、英語の正式用語や別名は検索用情報として扱います。"
        next={[
          { label: "教材の進捗を見る", to: "/learn" },
          { label: "Galleryのケースを見る", to: "/gallery" },
          { label: "根拠資料を確認する", to: "/sources" },
        ]}
        purpose="各手法・問題型・特徴ファミリーに、Map・診断・教材・可視化・根拠がどこまで接続しているかを確認します。"
        readingSteps={[
          "学習経路の完了数と不足を見ます。",
          "次に整備する領域を確認します。",
          "一覧を検索・絞り込みして、個別の不足を追います。",
        ]}
      />

      <JourneyCompleteness journeys={journeys} showTechnical={showTechnical} />
      <CoverageSummary report={report} />
      <PriorityAreas priorities={report.priorities} showTechnical={showTechnical} />
      <Inventory report={report} showTechnical={showTechnical} />
      <Integrity issues={report.integrity_issues} showTechnical={showTechnical} />
    </section>
  );
}

function CoverageSummary({ report }: { report: CoverageReport }) {
  return (
    <section aria-labelledby="coverage-summary-title" className="coverage-summary">
      <div className="coverage-section-heading">
        <div>
          <p className="eyebrow">全体</p>
          <h2 id="coverage-summary-title">期待する成果物</h2>
        </div>
        <p>現在のリリース内で、期待値を定義した成果物の状態です。</p>
      </div>
      <div className="coverage-status-grid" aria-label="期待成果物のステータス">
        {Object.entries(report.summary.status_counts).map(([key, count]) => (
          <article className={`coverage-stat coverage-${key}`} key={key}>
            <strong>{count}</strong>
            <span>{statusLabels[key as CoverageStatus]}</span>
          </article>
        ))}
      </div>
      <p className="coverage-baseline">
        前リリースとの比較基準はまだありません。初回スナップショットから増減を推測しません。
      </p>
    </section>
  );
}

function PriorityAreas({
  priorities,
  showTechnical,
}: {
  priorities: CoverageReport["priorities"];
  showTechnical: boolean;
}) {
  return (
    <section aria-labelledby="priority-title">
      <div className="coverage-section-heading">
        <div>
          <p className="eyebrow">次の焦点</p>
          <h2 id="priority-title">次に整備する領域</h2>
        </div>
        <p>分類・誤解の防止・可視化・利用ニーズの4観点から並べています。</p>
      </div>
      <div className="coverage-priority-grid">
        {priorities.map((item) => (
          <article key={item.slice_id}>
            <p className="eyebrow">優先 {item.rank} · {item.total}/12</p>
            <h3>{item.title_ja}</h3>
            <details>
              <summary>選定理由を見る</summary>
              <ul>
                {Object.entries(item.factors).map(([name, factor]) => (
                  <li key={name}>
                    <strong>{factorLabels[name] ?? name} {factor.score}/3:</strong> {factor.reason}
                  </li>
                ))}
              </ul>
            </details>
            {showTechnical && (
              <details className="coverage-technical-details">
                <summary>対象IDと表示方式</summary>
                <p>{item.proposed_scope}</p>
              </details>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}

function Inventory({
  report,
  showTechnical,
}: {
  report: CoverageReport;
  showTechnical: boolean;
}) {
  const [subjectType, setSubjectType] = useState<SubjectType | "all">("all");
  const [status, setStatus] = useState<CoverageStatus | "all">("all");
  const [family, setFamily] = useState("all");
  const [query, setQuery] = useState("");
  const [showAll, setShowAll] = useState(false);

  const expectationBySubject = useMemo(
    () => new Map(report.subjects.map((subject) => [
      subject.subject_id,
      report.expectations.filter((item) => item.subject_id === subject.subject_id),
    ])),
    [report],
  );
  const families = report.subjects
    .filter((item) => item.subject_type === "method" && item.subject_id.startsWith("MF_"))
    .map((item) => item.subject_id);
  const normalizedQuery = query.trim().toLocaleLowerCase();
  const visible = report.subjects.filter((subject) => {
    const expectations = expectationBySubject.get(subject.subject_id) ?? [];
    return (subjectType === "all" || subject.subject_type === subjectType)
      && (family === "all" || subject.subject_id === family)
      && (status === "all" || expectations.some((item) => item.status === status))
      && (
        normalizedQuery.length === 0
        || `${subject.label} ${subject.subject_id}`.toLocaleLowerCase().includes(normalizedQuery)
      );
  });
  const displayed = showAll ? visible : visible.slice(0, INVENTORY_PREVIEW_LIMIT);

  const resetPreview = () => setShowAll(false);

  return (
    <section aria-labelledby="inventory-title">
      <div className="coverage-section-heading">
        <div>
          <p className="eyebrow">個別確認</p>
          <h2 id="inventory-title">成果物一覧</h2>
        </div>
        <output>{visible.length}件中{displayed.length}件を表示</output>
      </div>
      <div className="coverage-filters" aria-label="成果物一覧の絞り込み">
        <label>
          検索
          <input
            onChange={(event) => {
              setQuery(event.target.value);
              resetPreview();
            }}
            placeholder="名前またはID"
            type="search"
            value={query}
          />
        </label>
        <label>
          対象種別
          <select
            onChange={(event) => {
              setSubjectType(event.target.value as SubjectType | "all");
              resetPreview();
            }}
            value={subjectType}
          >
            <option value="all">すべて</option>
            {Object.entries(subjectTypeLabels).map(([key, label]) => (
              <option key={key} value={key}>{label}</option>
            ))}
          </select>
        </label>
        <label>
          手法ファミリー
          <select
            onChange={(event) => {
              setFamily(event.target.value);
              resetPreview();
            }}
            value={family}
          >
            <option value="all">すべて</option>
            {families.map((item) => <option key={item}>{item}</option>)}
          </select>
        </label>
        <label>
          状態
          <select
            onChange={(event) => {
              setStatus(event.target.value as CoverageStatus | "all");
              resetPreview();
            }}
            value={status}
          >
            <option value="all">すべて</option>
            {Object.entries(statusLabels).map(([key, label]) => (
              <option key={key} value={key}>{label}</option>
            ))}
          </select>
        </label>
      </div>

      <div className="coverage-table-wrap" role="region" aria-label="成果物一覧の表" tabIndex={0}>
        <table>
          <thead>
            <tr><th>対象</th><th>種別</th><th>接続</th><th>期待状態</th></tr>
          </thead>
          <tbody>
            {displayed.map((subject) => {
              const expectations = expectationBySubject.get(subject.subject_id) ?? [];
              const connected = Object.values(subject.dimensions)
                .filter((item) => item.state === "connected").length;
              const dimensionCount = Object.keys(subject.dimensions).length;
              return (
                <tr key={`${subject.subject_type}:${subject.subject_id}`}>
                  <th scope="row">
                    <span>{subject.label}</span>
                    {showTechnical && <code>{subject.subject_id}</code>}
                  </th>
                  <td>{subjectTypeLabels[subject.subject_type]}</td>
                  <td>{connected}/{dimensionCount}</td>
                  <td>
                    {expectations.length > 0
                      ? expectations.map((item) => (
                        <details key={item.expectation_id}>
                          <summary>
                            <span className={`coverage-pill coverage-${item.status}`}>
                              {statusLabels[item.status]}
                            </span>{" "}
                            {purposeLabels[item.purpose] ?? "学習成果"}
                          </summary>
                          <p>{item.rationale}</p>
                          {showTechnical && item.reason_codes.length > 0 && (
                            <p className="coverage-reason-codes">
                              理由コード: {item.reason_codes.map((reason) => <code key={reason}>{reason}</code>)}
                            </p>
                          )}
                        </details>
                      ))
                      : <span className="muted">期待値なし</span>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {visible.length > displayed.length && (
        <button className="coverage-show-all" onClick={() => setShowAll(true)} type="button">
          残り{visible.length - displayed.length}件を表示
        </button>
      )}
      {visible.length === 0 && <p className="coverage-empty">条件に合う成果物はありません。</p>}
    </section>
  );
}

function JourneyCompleteness({
  journeys,
  showTechnical,
}: {
  journeys: LearningJourneyIndex;
  showTechnical: boolean;
}) {
  const assessmentById = new Map(journeys.assessments.map((item) => [item.journey_id, item]));
  const orphanCounts = journeys.orphan_assets.reduce<Record<string, number>>((counts, item) => {
    counts[item.policy] = (counts[item.policy] ?? 0) + 1;
    return counts;
  }, {});
  const completed = journeys.summary.status_counts.complete;
  const target = journeys.summary.target_complete_journeys;
  const remaining = Math.max(0, target - completed);
  const surplus = Math.max(0, completed - target);
  const incompleteJourneys = journeys.journeys.filter((journey) => journey.status !== "complete");
  const completeJourneys = journeys.journeys.filter((journey) => journey.status === "complete");

  return (
    <section className="journey-coverage" aria-labelledby="journey-coverage-title">
      <div className="journey-coverage-heading">
        <div>
          <p className="eyebrow">Case → Theater → Compare</p>
          <h2 id="journey-coverage-title">学習経路の接続状況</h2>
        </div>
        <div className={`journey-milestone journey-${journeys.summary.milestone_status}`}>
          <strong>{completed}件完了</strong>
          <span>
            {remaining > 0
              ? `目標${target}件まであと${remaining}件`
              : `目標${target}件を達成${surplus > 0 ? `（+${surplus}件）` : ""}`}
          </span>
          <progress aria-label={`完了${completed}件、目標${target}件`} max={target} value={Math.min(completed, target)} />
        </div>
      </div>
      <div className="journey-status-grid" aria-label="学習ジャーニーのステータス">
        {(["complete", "partial", "draft"] as const).map((status) => (
          <article key={status}>
            <strong>{journeys.summary.status_counts[status]}</strong>
            <span>{journeyStatusLabels[status]}</span>
          </article>
        ))}
      </div>
      <section className="journey-mobile-list" aria-label="学習経路の接続状況一覧">
        <div className="journey-mobile-incomplete">
          {incompleteJourneys.map((journey) => (
            <JourneyMobileCard
              assessment={assessmentById.get(journey.journey_id)}
              journey={journey}
              key={journey.journey_id}
              showTechnical={showTechnical}
            />
          ))}
        </div>
        {completeJourneys.length > 0 && (
          <details className="journey-mobile-complete">
            <summary>
              <span>完了した学習経路</span>
              <strong>{completeJourneys.length}件</strong>
            </summary>
            <div>
              {completeJourneys.map((journey) => (
                <JourneyMobileCard
                  assessment={assessmentById.get(journey.journey_id)}
                  journey={journey}
                  key={journey.journey_id}
                  showTechnical={showTechnical}
                />
              ))}
            </div>
          </details>
        )}
      </section>
      <div className="coverage-table-wrap journey-desktop-table" role="region" aria-label="学習経路の接続状況一覧（表）" tabIndex={0}>
        <table>
          <thead>
            <tr><th>学習経路</th><th>状態</th><th>不足している接続</th></tr>
          </thead>
          <tbody>
            {journeys.journeys.map((journey) => {
              const assessment = assessmentById.get(journey.journey_id);
              return (
                <tr key={journey.journey_id}>
                  <th scope="row">
                    <Link to={journey.canonical_url}>{journey.title_ja}</Link>
                    {showTechnical && <code>{journey.journey_id}</code>}
                  </th>
                  <td>
                    <span className={`coverage-pill journey-${journey.status}`}>
                      {journeyStatusLabels[journey.status]}
                    </span>
                  </td>
                  <td>
                    {assessment && assessment.missing_dimensions.length > 0
                      ? (
                        <details>
                           <summary>{assessment.missing_dimensions.length}領域</summary>
                          <ul>
                            {assessment.missing_dimensions.map((name) => (
                              <li key={name}>
                                {dimensionLabels[name]}
                                {showTechnical && (
                                  <code>{assessment.dimensions[name].reason_codes.join(", ")}</code>
                                )}
                              </li>
                            ))}
                          </ul>
                        </details>
                      )
                      : <span>すべて接続済み</span>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="journey-orphan-summary">
        未接続の成果物: 単独 {orphanCounts.standalone ?? 0}件 / 注意 {orphanCounts.warning ?? 0}件
      </p>
      {showTechnical && (
        <details className="journey-orphans">
          <summary>未接続成果物の技術情報</summary>
          {journeys.orphan_assets.length > 0
            ? (
              <ul>
                {journeys.orphan_assets.map((item) => (
                  <li key={`${item.asset_type}:${item.asset_id}`}>
                    <span className={`coverage-pill journey-${item.policy}`}>{item.policy}</span>{" "}
                    <code>{item.asset_type}:{item.asset_id}</code> — {item.reason_code}
                  </li>
                ))}
              </ul>
            )
            : <p>未接続の成果物はありません。</p>}
        </details>
      )}
    </section>
  );
}

function JourneyMobileCard({
  journey,
  assessment,
  showTechnical,
}: {
  journey: LearningJourney;
  assessment: LearningJourneyIndex["assessments"][number] | undefined;
  showTechnical: boolean;
}) {
  const missingDimensions = assessment?.missing_dimensions ?? [];
  return (
    <article className={`journey-mobile-card journey-${journey.status}`}>
      <div className="journey-mobile-card-heading">
        <Link to={journey.canonical_url}>{journey.title_ja}</Link>
        <span className={`coverage-pill journey-${journey.status}`}>
          {journeyStatusLabels[journey.status]}
        </span>
      </div>
      {showTechnical && <code>{journey.journey_id}</code>}
      {missingDimensions.length > 0
        ? (
          <details className="journey-mobile-gaps">
            <summary>
              <span>次に必要な接続</span>
              <strong>{missingDimensions.length}領域</strong>
            </summary>
            <ul>
              {missingDimensions.map((name) => (
                <li key={name}>
                  {dimensionLabels[name]}
                  {showTechnical && (
                    <code>{assessment?.dimensions[name].reason_codes.join(", ")}</code>
                  )}
                </li>
              ))}
            </ul>
          </details>
        )
        : <p className="journey-mobile-complete-copy">定式化・実行例・比較まで接続済み</p>}
    </article>
  );
}

function Integrity({
  issues,
  showTechnical,
}: {
  issues: CoverageReport["integrity_issues"];
  showTechnical: boolean;
}) {
  return (
    <section aria-labelledby="integrity-title">
      <div className="coverage-section-heading">
        <div>
          <p className="eyebrow">安全網</p>
          <h2 id="integrity-title">参照整合性</h2>
        </div>
      </div>
      {issues.length > 0
        ? (
          <ul className="coverage-issues">
            {issues.map((item) => (
              <li key={`${item.code}:${item.entity_id}`}>
                {showTechnical && <><code>{item.code}</code> <strong>{item.entity_id}</strong> — </>}
                {item.detail}
              </li>
            ))}
          </ul>
        )
        : (
          <p>
            壊れた参照はありません。これは学習経路が完了しているという意味ではありません。
            不足は上の「学習経路の接続状況」で確認します。
          </p>
        )}
    </section>
  );
}

async function loadCoverage(
  signal: AbortSignal,
): Promise<{ report: CoverageReport; journeys: LearningJourneyIndex }> {
  const base = siteBaseUrl();
  const manifestResponse = await fetch(`${base}data/manifest.json`, { signal });
  if (!manifestResponse.ok) throw new Error(`Manifest request failed (${manifestResponse.status}).`);
  const manifest = parseSiteManifest(await manifestResponse.json());
  const [coverageResponse, journeyResponse] = await Promise.all([
    fetch(`${base}data/${manifest.coverage.path}`, { signal }),
    fetch(`${base}data/${manifest.learning_journeys.path}`, { signal }),
  ]);
  if (!coverageResponse.ok) throw new Error(`Coverage request failed (${coverageResponse.status}).`);
  if (!journeyResponse.ok) {
    throw new Error(`Learning journey request failed (${journeyResponse.status}).`);
  }
  const report = parseCoverageReport(await coverageResponse.json());
  const journeys = parseLearningJourneyIndex(await journeyResponse.json());
  if (report.dataset_version !== manifest.dataset_version) {
    throw new Error("Coverage dataset version does not match the manifest.");
  }
  if (journeys.dataset_version !== manifest.dataset_version) {
    throw new Error("Learning journey dataset version does not match the manifest.");
  }
  return { report, journeys };
}
