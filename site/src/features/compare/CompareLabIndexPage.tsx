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
        <p className="eyebrow">比較 · 同じ予算で挙動を比べる</p>
        <h1>比較ラボ</h1>
        <p>固定した条件と変えた条件が明示された比較を選びます。</p>
      </header>
      <PageOrientation
        limits="比較は登録済みの条件・seed・評価予算の範囲での履歴です。1回の実行から一般的な優劣は結論づけません。"
        next={[{ label: "実問題から探す", to: "/gallery" }, { label: "手法の説明を読む", to: "/learn" }, { label: "動きを再生する", to: "/theater" }]}
        purpose="手法ランキングではなく、固定条件・変更条件・指標をそろえた公平な比較を読みます。"
        readingSteps={["比較したい問いと方式を選びます。", "固定条件・変更条件・予算・公平性を先に確認します。", "軌跡・実行可能性・Paretoなど、ケースに合う表示で差を読みます。"]}
      />
      {error && <p className="atlas-error" role="alert">{error.message}</p>}
      {!error && comparisons.length === 0 && <p role="status">比較条件を読み込み中…</p>}
      <div className="theater-card-grid" aria-label="比較ラボのメニュー">
        {comparisons.map((comparison) => (
          <Link className="theater-card" key={comparison.comparison_id} to={comparisonRoute(comparison.comparison_id)}>
            <span>{comparison.mode} · {comparison.budget.metric} {comparison.budget.value}</span>
            <h2>{comparison.title_ja}</h2>
            <p>{comparison.fairness_note}</p>
            <small>比較対象 {comparison.members.length}件 · {comparison.comparability} →</small>
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
