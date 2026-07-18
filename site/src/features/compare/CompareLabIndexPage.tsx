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
        <p className="eyebrow">比較 · 条件をそろえて違いを見る</p>
        <h1>条件を比較</h1>
        <p>「何を同じにして、何を変えたか」を先に確認し、見るべき差が決まっている比較を選びます。</p>
      </header>
      <PageOrientation
        limits="比較は登録済みの条件・seed・評価予算の範囲での履歴です。1回の実行から一般的な優劣は結論づけません。"
        next={[{ label: "実問題から探す", to: "/gallery" }, { label: "手法の説明を読む", to: "/learn" }, { label: "動きを再生する", to: "/theater" }]}
        purpose="手法ランキングではなく、固定条件・変更条件・指標をそろえた公平な比較を読みます。"
        readingSteps={["比較したい問いと方式を選びます。", "固定条件・変更条件・予算・公平性を先に確認します。", "軌跡・実行可能性・Paretoなど、ケースに合う表示で差を読みます。"]}
      />
      {error && <p className="atlas-error" role="alert">{error.message}</p>}
      {!error && comparisons.length === 0 && <p role="status">比較条件を読み込み中…</p>}
      <div className="theater-card-grid compare-card-grid" aria-label="比較のメニュー">
        {comparisons.map((comparison) => (
          <Link className="theater-card compare-card" key={comparison.comparison_id} to={comparisonRoute(comparison.comparison_id)}>
            <span>{comparisonModeLabel(comparison.mode)} · {comparison.budget.value}回でそろえる</span>
            <h2>{comparison.title_ja}</h2>
            <p>{readableComparisonText(comparison.comparison_question)}</p>
            <div className="compare-card-contract" aria-label="比較の要点">
              <span><strong>同じ</strong>{comparison.fixed_factors.length}項目</span>
              <span><strong>違う</strong>{comparison.changed_factors.length}項目</span>
              <span><strong>見る</strong>{comparison.metrics.map((metric) => metric.label_ja).join(" / ")}</span>
            </div>
            <small>比較対象 {comparison.members.length}件 · この比較を読む →</small>
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

function comparisonModeLabel(mode: string): string {
  return {
    method_contrast: "手法の違い",
    parameter_sensitivity: "条件の違い",
    initial_condition_sensitivity: "初期条件の違い",
    failure_contrast: "失敗の違い",
    result_tradeoff: "結果のトレードオフ",
    strategy_contrast: "戦略の違い",
  }[mode] ?? mode;
}

function readableComparisonText(value: string): string {
  return value
    .replaceAll("failure signal", "失敗の兆候")
    .replaceAll("learning rate", "学習率")
    .replaceAll("parameter sensitivity", "条件感度")
    .replaceAll("initial simplex", "初期単体")
    .replaceAll("proposal policy", "候補選択方針")
    .replaceAll("observation noise", "観測ノイズ")
    .replaceAll("random baseline", "ランダム基準")
    .replaceAll("Expected Improvement", "期待改善量")
    .replaceAll("acquisition", "獲得関数")
    .replaceAll("budget", "評価予算")
    .replaceAll("solver", "ソルバー");
}
