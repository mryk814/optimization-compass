import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { parseComparisonIndex, type ComparisonSet } from "../../contracts/comparisons";
import { siteBaseUrl } from "../../data/base-url";
import { comparisonRoute } from "./compare-routes";
import { PageOrientation } from "../../components/PageOrientation";

export function CompareLabIndexPage() {
  const [comparisons, setComparisons] = useState<ComparisonSet[]>([]);
  const [error, setError] = useState<Error>();

  useEffect(() => {
    const controller = new AbortController();
    void loadComparisons(controller.signal).then(
      (index) => setComparisons(index.comparisons),
      (caught: unknown) => {
        if (!controller.signal.aborted) {
          setError(caught instanceof Error ? caught : new Error(String(caught)));
        }
      },
    );
    return () => controller.abort();
  }, []);

  return (
    <section className="atlas-page compare-lab-index-page">
      <header className="atlas-page-header">
        <p className="eyebrow">Compare Lab · Same budget, different behavior</p>
        <h1>Compare Lab</h1>
        <p>何を固定し、何を変えたかが明示されたcase-bound comparisonを選びます。</p>
      </header>
      <PageOrientation
        limits="比較は登録済みの固定scenario・seed・評価予算の範囲での履歴です。単一runから一般的な優劣は結論づけません。"
        next={[{ label: "実問題から探す", to: "/gallery" }, { label: "手法の説明を読む", to: "/learn" }, { label: "動きを再生する", to: "/theater" }]}
        purpose="手法ランキングではなく、fixed / changed / metricsをそろえた公平な比較を読みます。"
        readingSteps={["比較したいquestionとmodeを選びます。", "fixed / changed / budget / fairnessを先に確認します。", "軌跡・feasibility・Paretoなど、caseに合うrendererで差を読みます。"]}
      />
      {error && <p className="atlas-error" role="alert">{error.message}</p>}
      {!error && comparisons.length === 0 && <p role="status">比較presetを読み込み中…</p>}
      <div className="theater-card-grid" aria-label="Compare Labの比較メニュー">
        {comparisons.map((comparison) => (
          <Link className="theater-card" key={comparison.comparison_id} to={comparisonRoute(comparison.comparison_id)}>
            <span>{comparison.mode} · {comparison.budget.metric} {comparison.budget.value}</span>
            <h2>{comparison.title_ja}</h2>
            <p>{comparison.fairness_note}</p>
            <small>{comparison.members.length} members · {comparison.comparability} →</small>
          </Link>
        ))}
      </div>
    </section>
  );
}

async function loadComparisons(signal: AbortSignal) {
  const response = await fetch(`${siteBaseUrl()}data/comparisons.json`, { signal });
  if (!response.ok) throw new Error(`Comparison request failed (${response.status}).`);
  return parseComparisonIndex(await response.json());
}
