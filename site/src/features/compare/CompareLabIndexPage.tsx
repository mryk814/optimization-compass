import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { parseComparisonIndex, type ComparisonSet } from "../../contracts/comparisons";
import { siteBaseUrl } from "../../data/base-url";
import { comparisonRoute } from "./compare-routes";
import {
  buildComparisonCatalog,
  rendererFamilyLabel,
} from "./compare-catalog";
import { PageOrientation } from "../../components/PageOrientation";

const visibleComparisonsPerSection = 1;

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
  const catalog = buildComparisonCatalog(comparisons);

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
      <div className="compare-catalog" aria-label="比較の問い別メニュー">
        {catalog.map((section) => (
          <section className="compare-catalog-section" key={section.mode} aria-labelledby={`compare-catalog-${section.mode}`}>
            <header>
              <div className="compare-catalog-section-heading">
                <h2 id={`compare-catalog-${section.mode}`}>{section.label}から読む</h2>
                <span>{section.comparisons.length}件</span>
              </div>
              <p>{section.description}</p>
            </header>
            <div className="theater-card-grid compare-card-grid">
              {section.comparisons.slice(0, visibleComparisonsPerSection).map((comparison) => (
                <ComparisonCard comparison={comparison} key={comparison.comparison_id} />
              ))}
            </div>
            {section.comparisons.length > visibleComparisonsPerSection && (
              <details className="compare-catalog-more">
                <summary>{section.label}の残り{section.comparisons.length - visibleComparisonsPerSection}件を見る</summary>
                <div className="theater-card-grid compare-card-grid">
                  {section.comparisons.slice(visibleComparisonsPerSection).map((comparison) => (
                    <ComparisonCard comparison={comparison} key={comparison.comparison_id} />
                  ))}
                </div>
              </details>
            )}
          </section>
        ))}
      </div>
    </section>
  );
}

function ComparisonCard({ comparison }: { comparison: ComparisonSet }) {
  const rendererLabels = [...new Set(comparison.members.map((member) => rendererFamilyLabel(member.artifact.renderer_family)))];
  return (
    <Link className="theater-card compare-card" to={comparisonRoute(comparison.comparison_id)}>
      <div className="compare-card-meta">
        <span>{comparison.budget.value}回でそろえる</span>
        <span className="compare-card-reading">
          {comparison.ranking_eligible ? "条件内で順位を読む" : "順位ではなく差を見る"}
        </span>
      </div>
      <h3>{comparison.title_ja}</h3>
      <p className="compare-card-question">{readableComparisonText(comparison.comparison_question)}</p>
      <dl className="compare-card-contract" aria-label="固定条件、変更条件、観察指標">
        <div>
          <dt>固定</dt>
          <dd>{summarizeComparisonItems(comparison.fixed_factors, "項目")}</dd>
        </div>
        <div>
          <dt>変更</dt>
          <dd>{summarizeComparisonItems(comparison.changed_factors, "項目")}</dd>
        </div>
        <div>
          <dt>観察</dt>
          <dd>{summarizeComparisonItems(comparison.metrics.map((metric) => metric.label_ja), "指標")}</dd>
        </div>
      </dl>
      <div className="compare-card-footer">
        <small>比較対象 {comparison.members.length}件 · {rendererLabels.join(" + ")}で見る</small>
        <strong>比較を開く →</strong>
      </div>
    </Link>
  );
}

async function loadComparisons(signal: AbortSignal) {
  const response = await fetch(`${siteBaseUrl()}data/comparisons.json`, { signal });
  if (!response.ok) throw new Error(`Comparison request failed (${response.status}).`);
  return parseComparisonIndex(await response.json());
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

function summarizeComparisonItems(values: string[], unit: "項目" | "指標"): string {
  const first = readableComparisonText(values[0]);
  return values.length === 1 ? first : `${first} · ほか${values.length - 1}${unit}`;
}
