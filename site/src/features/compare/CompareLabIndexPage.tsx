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
        <p>比較する現象を選び、同じ条件・oracle evaluation軸で手法の動きを見比べます。</p>
      </header>
      <PageOrientation
        limits="比較は登録済みの固定scenario・seed・評価予算の範囲での履歴です。単一runから一般的な優劣は結論づけません。"
        next={[{ label: "実問題から探す", to: "/gallery" }, { label: "手法の説明を読む", to: "/learn" }, { label: "動きを再生する", to: "/theater" }]}
        purpose="同じ目的関数・条件・評価軸で、複数手法の更新の違いを比べます。"
        readingSteps={["比較したい現象presetを選びます。", "初期条件・budget・fairness noteを先に確認します。", "軌跡と目的値を同じ評価回数で見比べ、差の理由を追います。"]}
      />
      {error && <p className="atlas-error" role="alert">{error.message}</p>}
      {!error && comparisons.length === 0 && <p role="status">比較presetを読み込み中…</p>}
      <div className="theater-card-grid" aria-label="Compare Labの比較メニュー">
        {comparisons.map((comparison) => (
          <Link className="theater-card" key={comparison.comparison_id} to={comparisonRoute(comparison.comparison_id)}>
            <span>{comparison.preset_id} · budget {comparison.budget}</span>
            <h2>{comparison.title_ja}</h2>
            <p>{comparison.fairness_note}</p>
            <small>{comparison.members.length}手法 · {comparison.comparability} →</small>
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
