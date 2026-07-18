import type { ComparisonMode, ComparisonRendererFamily, ComparisonSet } from "../../contracts/comparisons";

type ComparisonModeDescription = {
  label: string;
  description: string;
};

export type ComparisonCatalogSection = ComparisonModeDescription & {
  mode: ComparisonMode;
  comparisons: ComparisonSet[];
};

const comparisonModeOrder: ComparisonMode[] = [
  "method_contrast",
  "parameter_sensitivity",
  "initial_condition_sensitivity",
  "failure_contrast",
  "result_tradeoff",
  "strategy_contrast",
];

const comparisonModeDescriptions: Record<ComparisonMode, ComparisonModeDescription> = {
  method_contrast: {
    label: "手法の違い",
    description: "同じ問題・予算で更新則やsolverの違いを読む。",
  },
  parameter_sensitivity: {
    label: "条件の違い",
    description: "手法を固定し、parameterやノイズ条件を変えた影響を読む。",
  },
  initial_condition_sensitivity: {
    label: "初期条件の違い",
    description: "同じ手法で開始位置や初期状態を変え、経路の依存性を読む。",
  },
  failure_contrast: {
    label: "失敗の違い",
    description: "目的値だけでは見えない、停止・実行可能性・予算切れの差を読む。",
  },
  result_tradeoff: {
    label: "結果のトレードオフ",
    description: "単一の最良値に潰さず、複数指標やPareto上の選択を読む。",
  },
  strategy_contrast: {
    label: "戦略の違い",
    description: "候補選択や探索方針の違いを、同じ評価軸で読む。",
  },
};

const rendererFamilyLabels: Record<ComparisonRendererFamily, string> = {
  simplex_geometry: "単体形状",
  continuous_trajectory: "連続軌跡",
  generic_metric_history: "指標の履歴",
  search_tree: "探索木",
  surrogate_uncertainty: "代理モデルの不確実性",
  feasible_region: "実行可能領域",
  pareto_front: "パレート前線",
  field_evolution: "設計fieldの進化",
};

export function buildComparisonCatalog(comparisons: ComparisonSet[]): ComparisonCatalogSection[] {
  return comparisonModeOrder.flatMap((mode) => {
    const entries = comparisons.filter((comparison) => comparison.mode === mode);
    return entries.length === 0
      ? []
      : [{ mode, ...comparisonModeDescriptions[mode], comparisons: entries }];
  });
}

export function comparisonModeLabel(mode: ComparisonMode): string {
  return comparisonModeDescriptions[mode].label;
}

export function comparisonModeDescription(mode: ComparisonMode): string {
  return comparisonModeDescriptions[mode].description;
}

export function rendererFamilyLabel(family: ComparisonRendererFamily): string {
  return rendererFamilyLabels[family];
}
