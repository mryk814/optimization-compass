/**
 * Problem Signature: the twelve diagnosis axes (Q01–Q12) as one shared coordinate system.
 *
 * Gallery cases store `question_answers` on the same axes the Diagnose form asks, and method
 * rules/predicates attach to the same features, so every surface can draw a problem — and a
 * method's view of it — with the same marks. See docs/visual-system.md.
 */

export type AxisState = "known" | "unknown" | "missing" | "not_applicable";

export interface AxisDefinition {
  questionId: string;
  /** Two-to-four character axis name used in the compact signature. */
  name: string;
  group: SignatureGroupId;
}

export type SignatureGroupId = "shape" | "computation" | "goal";

export const SIGNATURE_GROUPS: ReadonlyArray<{ id: SignatureGroupId; label: string }> = [
  { id: "shape", label: "問題の形" },
  { id: "computation", label: "計算の性質" },
  { id: "goal", label: "ほしい結果" },
];

export const SIGNATURE_AXES: readonly AxisDefinition[] = [
  { questionId: "Q01", name: "変数", group: "shape" },
  { questionId: "Q02", name: "記述", group: "shape" },
  { questionId: "Q03", name: "目的の形", group: "shape" },
  { questionId: "Q04", name: "制約", group: "shape" },
  { questionId: "Q05", name: "勾配", group: "computation" },
  { questionId: "Q06", name: "評価費", group: "computation" },
  { questionId: "Q07", name: "再現性", group: "computation" },
  { questionId: "Q08", name: "次元", group: "computation" },
  { questionId: "Q09", name: "探す範囲", group: "goal" },
  { questionId: "Q10", name: "証明", group: "goal" },
  { questionId: "Q11", name: "特殊構造", group: "goal" },
  { questionId: "Q12", name: "反復", group: "goal" },
];

/** Short value labels: the signature's vocabulary. Full labels stay in optimization-language.ts. */
const SHORT_VALUE_LABELS: Record<string, Record<string, string>> = {
  Q01: { continuous: "連続", integer: "整数", binary: "0-1", categorical: "カテゴリ", mixed: "混合", structured_or_unknown: "複雑な型" },
  Q02: { explicit_algebraic: "数式", residual_vector: "残差", automatic_differentiation_graph: "AD graph", simulation_only: "simulation", experiment_only: "実験", unknown: "不明" },
  Q03: { linear: "線形", quadratic: "二次", sum_of_squares: "二乗和", general_nonlinear: "非線形", multiobjective: "多目的", equation_or_feasibility: "方程式", unknown: "不明" },
  Q04: { none: "なし", bounds: "上下限", linear: "線形", nonlinear: "非線形", logical_or_combinatorial: "論理", conic_or_psd: "錐", dynamics_or_manifold: "力学系", implicit_or_failure: "暗黙・失敗" },
  Q05: { analytic_gradient: "解析勾配", autodiff: "自動微分", jacobian_or_hvp: "Jacobian", numerical_difference_only: "数値差分", stochastic_gradient: "確率勾配", unreliable_or_none: "使えない", not_differentiable: "微分不能" },
  Q06: { milliseconds_or_less: "ms以下", seconds: "秒", minutes: "分", hours_or_more: "時間以上", unknown: "不明" },
  Q07: { deterministic_reliable: "決定的", small_noise: "小noise", large_noise: "大noise", random_seeded: "seed固定", occasional_failure: "時々失敗", frequent_failure: "頻繁に失敗", timeout_possible: "timeout", unknown: "不明" },
  Q08: { under_10: "<10", "10_to_100": "10–100", "100_to_10000": "100–1万", over_10000: ">1万", huge_sparse_or_distributed: "巨大・疎", unknown: "不明" },
  Q09: { local_is_fine: "局所", global_candidate_desired: "大域候補", multiple_distinct_solutions: "複数解", unknown: "不明" },
  Q10: { no_certificate_needed: "不要", gap_desired: "gap", global_proof_required: "大域証明", feasible_solution_first: "実行可能解", approximation_guarantee: "近似保証", unknown: "不明" },
  Q11: { none_known: "なし", least_squares: "最小二乗", lp_qp_conic: "LP/QP/錐", graph_flow_path_matching: "graph", scheduling_routing: "scheduling", prox_separable: "prox", optimal_control: "最適制御", manifold: "多様体", stochastic_or_robust: "確率・robust", other: "その他" },
  Q12: { one_off: "単発", repeated_similar: "反復", online_or_realtime: "online", parallel_evaluations: "並列評価", distributed: "分散", gpu_available: "GPU", warm_start_available: "warm start" },
};

/**
 * Ordered scales for axes whose values have a natural order. The gauge shows position on the
 * scale only; it never encodes "easy" or "hard", which would be an editorial judgement.
 */
export const ORDINAL_SCALES: Record<string, readonly string[]> = {
  Q06: ["milliseconds_or_less", "seconds", "minutes", "hours_or_more"],
  Q08: ["under_10", "10_to_100", "100_to_10000", "over_10000"],
};

export function shortValueLabel(questionId: string, value: string): string {
  return SHORT_VALUE_LABELS[questionId]?.[value] ?? value;
}

export interface SignatureAnswer {
  status: "answered" | "unknown" | "not_applicable";
  values: readonly string[];
}

export interface SignatureAxis extends AxisDefinition {
  state: AxisState;
  values: readonly string[];
  /** Position on the ordinal scale (0-based) and its length, when the axis is ordinal. */
  ordinal?: { index: number; length: number };
}

/**
 * Build the signature from answers keyed by question ID. A missing key is `missing` (not asked
 * yet); "unknown" is a recorded answer that the fact is not known. They stay distinct.
 */
export function buildSignature(
  answers: Readonly<Record<string, SignatureAnswer | undefined>>,
): SignatureAxis[] {
  return SIGNATURE_AXES.map((axis) => {
    const answer = answers[axis.questionId];
    if (!answer) return { ...axis, state: "missing", values: [] };
    if (answer.status === "not_applicable") return { ...axis, state: "not_applicable", values: [] };
    const values = answer.values.filter((value) => value !== "unknown");
    if (answer.status === "unknown" || values.length === 0) return { ...axis, state: "unknown", values: [] };
    const scale = ORDINAL_SCALES[axis.questionId];
    const index = scale ? scale.indexOf(values[0]) : -1;
    return {
      ...axis,
      state: "known",
      values,
      ...(scale && index >= 0 ? { ordinal: { index, length: scale.length } } : {}),
    };
  });
}

/** Gallery cases store one value per question; "unknown" is a recorded answer. */
export function caseAnswers(questionAnswers: Readonly<Record<string, string>>): Record<string, SignatureAnswer> {
  return Object.fromEntries(
    Object.entries(questionAnswers).map(([questionId, value]) => [
      questionId,
      value === "unknown"
        ? { status: "unknown", values: ["unknown"] }
        : { status: "answered", values: [value] },
    ]),
  );
}

export const AXIS_STATE_LABELS: Record<AxisState, string> = {
  known: "分かっている",
  unknown: "不明と回答",
  missing: "まだ答えていない",
  not_applicable: "該当なし",
};

export function axisValueText(axis: SignatureAxis): string {
  if (axis.state !== "known") return AXIS_STATE_LABELS[axis.state];
  return axis.values.map((value) => shortValueLabel(axis.questionId, value)).join("・");
}

export function signatureSummary(axes: readonly SignatureAxis[]): string {
  const counts = { known: 0, unknown: 0, missing: 0, not_applicable: 0 } satisfies Record<AxisState, number>;
  axes.forEach((axis) => { counts[axis.state] += 1; });
  const known = axes
    .filter((axis) => axis.state === "known")
    .map((axis) => `${axis.name}: ${axisValueText(axis)}`)
    .join("、");
  const open = axes.filter((axis) => axis.state === "unknown" || axis.state === "missing").map((axis) => axis.name);
  return `問題の署名。${known || "分かっている軸はまだありません"}。`
    + (open.length ? `まだ開いている軸: ${open.join("、")}。` : "")
    + (counts.not_applicable ? `該当なし ${counts.not_applicable}軸。` : "");
}

/** Slot order per axis: the question's choices, without "unknown" (that is an axis state). */
export const SIGNATURE_SLOTS: Record<string, readonly string[]> = Object.fromEntries(
  SIGNATURE_AXES.map((axis) => [
    axis.questionId,
    Object.keys(SHORT_VALUE_LABELS[axis.questionId] ?? {}).filter((value) => value !== "unknown"),
  ]),
);

export const MAX_SIGNATURE_SLOTS = Math.max(...Object.values(SIGNATURE_SLOTS).map((slots) => slots.length));

/** A signature with no problem placed on it: used where only a method's view is drawn. */
export function blankSignature(): SignatureAxis[] {
  return SIGNATURE_AXES.map((axis) => ({ ...axis, state: "known", values: [] }));
}
