import { useEffect, useMemo, useState } from "react";
import { parseCoverageReport, type CoverageReport, type CoverageStatus, type SubjectType } from "../../contracts/coverage";
import { parseSiteManifest } from "../../contracts/manifest";
import { siteBaseUrl } from "../../data/base-url";

type LoadState = { status: "loading" } | { status: "error"; message: string } | { status: "ready"; report: CoverageReport };
const statusLabels: Record<CoverageStatus, string> = { available: "利用可能", partial: "一部接続", missing: "未構築", not_applicable: "適用外" };

export function CoveragePage() {
  const [state, setState] = useState<LoadState>({ status: "loading" });
  const [subjectType, setSubjectType] = useState<SubjectType | "all">("all");
  const [status, setStatus] = useState<CoverageStatus | "all">("all");
  const [family, setFamily] = useState("all");
  useEffect(() => {
    const controller = new AbortController();
    void loadCoverage(controller.signal).then((report) => setState({ status: "ready", report }), (error: unknown) => {
      if (!(error instanceof DOMException && error.name === "AbortError")) setState({ status: "error", message: error instanceof Error ? error.message : String(error) });
    });
    return () => controller.abort();
  }, []);
  if (state.status === "loading") return <p role="status">Coverageを集計しています…</p>;
  if (state.status === "error") return <p role="alert">Coverageを読み込めませんでした: {state.message}</p>;
  return <CoverageView report={state.report} subjectType={subjectType} status={status} family={family} setSubjectType={setSubjectType} setStatus={setStatus} setFamily={setFamily} />;
}

function CoverageView({ report, subjectType, status, family, setSubjectType, setStatus, setFamily }: { report: CoverageReport; subjectType: SubjectType | "all"; status: CoverageStatus | "all"; family: string; setSubjectType: (value: SubjectType | "all") => void; setStatus: (value: CoverageStatus | "all") => void; setFamily: (value: string) => void }) {
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
    <div className="coverage-status-grid" aria-label="期待成果物のステータス">{Object.entries(report.summary.status_counts).map(([key, count]) => <article key={key} className={`coverage-stat coverage-${key}`}><strong>{count}</strong><span>{statusLabels[key as CoverageStatus]}</span></article>)}</div>
    <p className="coverage-baseline">Release delta: baseline未指定。初回スナップショットでは差分を推測しません。</p>
    <section aria-labelledby="priority-title"><h2 id="priority-title">Priority slices</h2><div className="coverage-priority-grid">{report.priorities.map((item) => <article key={item.slice_id}><p className="eyebrow">#{item.rank} · {item.total}/12</p><h3>{item.title_ja}</h3><p>{item.proposed_scope}</p><details><summary>優先理由</summary><ul>{Object.entries(item.factors).map(([name, factor]) => <li key={name}><strong>{name} {factor.score}/3:</strong> {factor.reason}</li>)}</ul></details></article>)}</div></section>
    <section aria-labelledby="inventory-title"><h2 id="inventory-title">Artifact inventory</h2><div className="coverage-filters" aria-label="Coverage filters">
      <label>Subject<select value={subjectType} onChange={(event) => setSubjectType(event.target.value as SubjectType | "all")}><option value="all">すべて</option><option value="method">手法</option><option value="problem">問題型</option><option value="feature_family">特徴ファミリー</option></select></label>
      <label>Family<select value={family} onChange={(event) => setFamily(event.target.value)}><option value="all">すべて</option>{families.map((item) => <option key={item}>{item}</option>)}</select></label>
      <label>Status<select value={status} onChange={(event) => setStatus(event.target.value as CoverageStatus | "all")}><option value="all">すべて</option>{Object.entries(statusLabels).map(([key, label]) => <option value={key} key={key}>{label}</option>)}</select></label>
    </div><div className="coverage-table-wrap"><table><thead><tr><th>Subject</th><th>Type</th><th>接続</th><th>期待状態</th></tr></thead><tbody>{visible.map((subject) => { const expectations = expectationBySubject.get(subject.subject_id) ?? []; const connected = Object.values(subject.dimensions).filter((item) => item.state === "connected").length; return <tr key={`${subject.subject_type}:${subject.subject_id}`}><th scope="row"><span>{subject.label}</span><code>{subject.subject_id}</code></th><td>{subject.subject_type}</td><td>{connected}/8</td><td>{expectations.length ? expectations.map((item) => <details key={item.expectation_id}><summary><span className={`coverage-pill coverage-${item.status}`}>{statusLabels[item.status]}</span> {item.purpose}</summary><p>{item.rationale}</p>{item.reason_codes.map((reason) => <code key={reason}>{reason}</code>)}</details>) : <span className="muted">期待値なし</span>}</td></tr>; })}</tbody></table></div></section>
    {report.integrity_issues.length > 0 && <section aria-labelledby="integrity-title"><h2 id="integrity-title">Broken references</h2><ul className="coverage-issues">{report.integrity_issues.map((item) => <li key={`${item.code}:${item.entity_id}`}><code>{item.code}</code> <strong>{item.entity_id}</strong> — {item.detail}</li>)}</ul></section>}
  </section>;
}

async function loadCoverage(signal: AbortSignal): Promise<CoverageReport> {
  const base = siteBaseUrl();
  const manifestResponse = await fetch(`${base}data/manifest.json`, { signal });
  if (!manifestResponse.ok) throw new Error(`Manifest request failed (${manifestResponse.status}).`);
  const manifest = parseSiteManifest(await manifestResponse.json());
  const response = await fetch(`${base}data/${manifest.coverage.path}`, { signal });
  if (!response.ok) throw new Error(`Coverage request failed (${response.status}).`);
  const report = parseCoverageReport(await response.json());
  if (report.dataset_version !== manifest.dataset_version) throw new Error("Coverage dataset version does not match the manifest.");
  return report;
}
