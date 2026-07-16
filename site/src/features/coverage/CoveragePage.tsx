import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { parseCoverageReport, type CoverageReport, type CoverageStatus, type SubjectType } from "../../contracts/coverage";
import { parseLearningJourneyIndex, type JourneyDimensionName, type JourneyStatus, type LearningJourneyIndex } from "../../contracts/learning-journeys";
import { parseSiteManifest } from "../../contracts/manifest";
import { siteBaseUrl } from "../../data/base-url";
import { PageOrientation } from "../../components/PageOrientation";

type LoadState = { status: "loading" } | { status: "error"; message: string } | { status: "ready"; report: CoverageReport; journeys: LearningJourneyIndex };
const statusLabels: Record<CoverageStatus, string> = { available: "利用可能", partial: "一部接続", missing: "未構築", not_applicable: "適用外" };
const journeyStatusLabels: Record<JourneyStatus, string> = { complete: "完了", partial: "一部接続", draft: "下書き" };
const dimensionLabels: Record<JourneyDimensionName, string> = {
  formulation: "定式化", canonical_problem_instance: "問題インスタンス", primary_scenario: "主シナリオ",
  alternate_scenario: "別条件シナリオ", canonical_comparison: "比較", method_roles: "手法の役割",
  implementation: "実装", source_review: "根拠とレビュー", terminology_prerequisite: "用語と前提",
  static_text_alternative: "静的・テキスト代替", cross_surface_links: "画面間リンク",
  route_reachability: "到達可能な経路", validation_status: "参照整合性",
};

export function CoveragePage() {
  const [state, setState] = useState<LoadState>({ status: "loading" });
  const [subjectType, setSubjectType] = useState<SubjectType | "all">("all");
  const [status, setStatus] = useState<CoverageStatus | "all">("all");
  const [family, setFamily] = useState("all");
  useEffect(() => {
    const controller = new AbortController();
    void loadCoverage(controller.signal).then(({ report, journeys }) => setState({ status: "ready", report, journeys }), (error: unknown) => {
      if (!(error instanceof DOMException && error.name === "AbortError")) setState({ status: "error", message: error instanceof Error ? error.message : String(error) });
    });
    return () => controller.abort();
  }, []);
  if (state.status === "loading") return <p role="status">Coverageを集計しています…</p>;
  if (state.status === "error") return <p role="alert">Coverageを読み込めませんでした: {state.message}</p>;
  return <CoverageView report={state.report} journeys={state.journeys} subjectType={subjectType} status={status} family={family} setSubjectType={setSubjectType} setStatus={setStatus} setFamily={setFamily} />;
}

function CoverageView({ report, journeys, subjectType, status, family, setSubjectType, setStatus, setFamily }: { report: CoverageReport; journeys: LearningJourneyIndex; subjectType: SubjectType | "all"; status: CoverageStatus | "all"; family: string; setSubjectType: (value: SubjectType | "all") => void; setStatus: (value: CoverageStatus | "all") => void; setFamily: (value: string) => void }) {
  const expectationBySubject = useMemo(() => new Map(report.subjects.map((subject) => [subject.subject_id, report.expectations.filter((item) => item.subject_id === subject.subject_id)])), [report]);
  const families = report.subjects.filter((item) => item.subject_type === "method" && item.subject_id.startsWith("MF_")).map((item) => item.subject_id);
  const visible = report.subjects.filter((subject) => {
    const expectations = expectationBySubject.get(subject.subject_id) ?? [];
    return (subjectType === "all" || subject.subject_type === subjectType)
      && (family === "all" || subject.subject_id === family)
      && (status === "all" || expectations.some((item) => item.status === status));
  });
  return <section className="coverage-page">
    <header className="page-heading"><p className="eyebrow">Maintainer view</p><h1>Atlas Coverage</h1><p>教材の深さを一律にせず、期待する学習成果と実在する成果物を分けて監査します。</p></header>
    <PageOrientation limits="Coverageは学習contractの接続状態を監査します。page数やcoverage scoreだけで、教材の質や手法の優劣を判断しません。" next={[{ label: "教材の進捗を見る", to: "/learn" }, { label: "Galleryのケースを見る", to: "/gallery" }, { label: "根拠資料を確認する", to: "/sources" }]} purpose="各method・problem・feature familyに、Map・診断・教材・可視化・根拠などがどこまで接続しているかを確認します。" readingSteps={["status countsで全体の接続状態を見ます。", "Priority slicesで次に補う学習成果を確認します。", "Artifact inventoryをfilterし、欠けた接続と理由を追います。"]} />
    <JourneyCompleteness journeys={journeys} />
    <div className="coverage-status-grid" aria-label="期待成果物のステータス">{Object.entries(report.summary.status_counts).map(([key, count]) => <article key={key} className={`coverage-stat coverage-${key}`}><strong>{count}</strong><span>{statusLabels[key as CoverageStatus]}</span></article>)}</div>
    <p className="coverage-baseline">Release delta: baseline未指定。初回スナップショットでは差分を推測しません。</p>
    <section aria-labelledby="priority-title"><h2 id="priority-title">Priority slices</h2><div className="coverage-priority-grid">{report.priorities.map((item) => <article key={item.slice_id}><p className="eyebrow">#{item.rank} · {item.total}/12</p><h3>{item.title_ja}</h3><p>{item.proposed_scope}</p><details><summary>優先理由</summary><ul>{Object.entries(item.factors).map(([name, factor]) => <li key={name}><strong>{name} {factor.score}/3:</strong> {factor.reason}</li>)}</ul></details></article>)}</div></section>
    <section aria-labelledby="inventory-title"><h2 id="inventory-title">Artifact inventory</h2><div className="coverage-filters" aria-label="Coverage filters">
      <label>Subject<select value={subjectType} onChange={(event) => setSubjectType(event.target.value as SubjectType | "all")}><option value="all">すべて</option><option value="method">手法</option><option value="problem">問題型</option><option value="feature_family">特徴ファミリー</option></select></label>
      <label>Family<select value={family} onChange={(event) => setFamily(event.target.value)}><option value="all">すべて</option>{families.map((item) => <option key={item}>{item}</option>)}</select></label>
      <label>Status<select value={status} onChange={(event) => setStatus(event.target.value as CoverageStatus | "all")}><option value="all">すべて</option>{Object.entries(statusLabels).map(([key, label]) => <option value={key} key={key}>{label}</option>)}</select></label>
    </div><div className="coverage-table-wrap" role="region" aria-label="Artifact inventory table" tabIndex={0}><table><thead><tr><th>Subject</th><th>Type</th><th>接続</th><th>期待状態</th></tr></thead><tbody>{visible.map((subject) => { const expectations = expectationBySubject.get(subject.subject_id) ?? []; const connected = Object.values(subject.dimensions).filter((item) => item.state === "connected").length; return <tr key={`${subject.subject_type}:${subject.subject_id}`}><th scope="row"><span>{subject.label}</span><code>{subject.subject_id}</code></th><td>{subject.subject_type}</td><td>{connected}/8</td><td>{expectations.length ? expectations.map((item) => <details key={item.expectation_id}><summary><span className={`coverage-pill coverage-${item.status}`}>{statusLabels[item.status]}</span> {item.purpose}</summary><p>{item.rationale}</p>{item.reason_codes.map((reason) => <code key={reason}>{reason}</code>)}</details>) : <span className="muted">期待値なし</span>}</td></tr>; })}</tbody></table></div></section>
    {report.integrity_issues.length > 0 && <section aria-labelledby="integrity-title"><h2 id="integrity-title">Broken references</h2><ul className="coverage-issues">{report.integrity_issues.map((item) => <li key={`${item.code}:${item.entity_id}`}><code>{item.code}</code> <strong>{item.entity_id}</strong> — {item.detail}</li>)}</ul></section>}
  </section>;
}

function JourneyCompleteness({ journeys }: { journeys: LearningJourneyIndex }) {
  const assessmentById = new Map(journeys.assessments.map((item) => [item.journey_id, item]));
  const orphanCounts = journeys.orphan_assets.reduce<Record<string, number>>((counts, item) => {
    counts[item.policy] = (counts[item.policy] ?? 0) + 1;
    return counts;
  }, {});
  return <section className="journey-coverage" aria-labelledby="journey-coverage-title">
    <div className="journey-coverage-heading">
      <div><p className="eyebrow">Case → Theater → Compare</p><h2 id="journey-coverage-title">Learning journey completeness</h2></div>
      <strong className={`journey-milestone journey-${journeys.summary.milestone_status}`}>{journeys.summary.status_counts.complete}/{journeys.summary.target_complete_journeys} complete</strong>
    </div>
    <div className="journey-status-grid" aria-label="学習ジャーニーのステータス">
      {(["complete", "partial", "draft"] as const).map((status) => <article key={status}><strong>{journeys.summary.status_counts[status]}</strong><span>{journeyStatusLabels[status]}</span></article>)}
    </div>
    <div className="coverage-table-wrap" role="region" aria-label="Learning journey completeness table" tabIndex={0}><table><thead><tr><th>Journey</th><th>Status</th><th>不足している接続</th></tr></thead><tbody>
      {journeys.journeys.map((journey) => { const assessment = assessmentById.get(journey.journey_id); return <tr key={journey.journey_id}><th scope="row"><Link to={journey.canonical_url}>{journey.title_ja}</Link><code>{journey.journey_id}</code></th><td><span className={`coverage-pill journey-${journey.status}`}>{journeyStatusLabels[journey.status]}</span></td><td>{assessment && assessment.missing_dimensions.length > 0 ? <details><summary>{assessment.missing_dimensions.length}項目</summary><ul>{assessment.missing_dimensions.map((name) => <li key={name}>{dimensionLabels[name]} <code>{assessment.dimensions[name].reason_codes.join(", ")}</code></li>)}</ul></details> : <span>すべて接続済み</span>}</td></tr>; })}
    </tbody></table></div>
    <details className="journey-orphans">
      <summary><strong>未接続asset:</strong> standalone {orphanCounts.standalone ?? 0}件 / warning {orphanCounts.warning ?? 0}件</summary>
      {journeys.orphan_assets.length > 0
        ? <ul>{journeys.orphan_assets.map((item) => <li key={`${item.asset_type}:${item.asset_id}`}><span className={`coverage-pill journey-${item.policy}`}>{item.policy}</span> <code>{item.asset_type}:{item.asset_id}</code> — {item.reason_code}</li>)}</ul>
        : <p>未接続assetはありません。</p>}
    </details>
  </section>;
}

async function loadCoverage(signal: AbortSignal): Promise<{ report: CoverageReport; journeys: LearningJourneyIndex }> {
  const base = siteBaseUrl();
  const manifestResponse = await fetch(`${base}data/manifest.json`, { signal });
  if (!manifestResponse.ok) throw new Error(`Manifest request failed (${manifestResponse.status}).`);
  const manifest = parseSiteManifest(await manifestResponse.json());
  const [coverageResponse, journeyResponse] = await Promise.all([
    fetch(`${base}data/${manifest.coverage.path}`, { signal }),
    fetch(`${base}data/${manifest.learning_journeys.path}`, { signal }),
  ]);
  if (!coverageResponse.ok) throw new Error(`Coverage request failed (${coverageResponse.status}).`);
  if (!journeyResponse.ok) throw new Error(`Learning journey request failed (${journeyResponse.status}).`);
  const report = parseCoverageReport(await coverageResponse.json());
  const journeys = parseLearningJourneyIndex(await journeyResponse.json());
  if (report.dataset_version !== manifest.dataset_version) throw new Error("Coverage dataset version does not match the manifest.");
  if (journeys.dataset_version !== manifest.dataset_version) throw new Error("Learning journey dataset version does not match the manifest.");
  return { report, journeys };
}
