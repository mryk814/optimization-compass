export const OPTIMIZATION_TERMS = [
  {
    symbol: "x",
    title: "決めるもの",
    description: "温度・寸法・人数・材料の種類など。手法が探す答えです。",
  },
  {
    symbol: "f(x)",
    title: "比べるもの",
    description: "費用・誤差・時間など。小さく、または大きくしたい値です。",
  },
  {
    symbol: "g(x), h(x)",
    title: "守る条件",
    description: "上限・品質・収支など。満たさないxは答えにできません。",
  },
  {
    symbol: "X",
    title: "選べる範囲",
    description: "xが取り得る値の種類と範囲。連続・整数・カテゴリなどです。",
  },
] as const;

export const VARIABLE_TYPE_DEFINITIONS = [
  {
    title: "連続 (continuous)",
    description: "20.0と20.1の間も選べる。例: 温度・濃度・寸法。",
  },
  {
    title: "整数・0-1",
    description: "離散 (discrete) の一種。個数やYes / Noを表します。",
  },
  {
    title: "カテゴリ (categorical)",
    description: "これも離散。材料A / B / Cなど、数の大小に意味がない。",
  },
  {
    title: "混合 (mixed)",
    description: "連続と離散など、複数の種類を一緒に決める。",
  },
] as const;

export const DIAGNOSIS_QUESTION_TITLES: Record<string, string> = {
  Q01: "x（決めるもの）はどの種類ですか？",
  Q02: "f(x)や制約は、式や計算手順として書けますか？",
  Q03: "f(x)（比べるもの）はどんな形ですか？",
  Q04: "守る条件（制約）はありますか？",
  Q05: "f(x)の傾き（勾配）を使えますか？",
  Q06: "f(x)や制約を1回計算する時間は？",
  Q07: "同じxなら、結果は毎回同じですか？",
  Q08: "xの要素はいくつありますか？",
  Q09: "どの範囲で良い解を探したいですか？",
  Q10: "最適だと証明する必要がありますか？",
  Q11: "問題に特別な構造がありますか？",
  Q12: "同じ問題を何度も解きますか？",
};

const DIAGNOSIS_CHOICE_LABELS: Record<string, Record<string, string>> = {
  Q01: {
    continuous: "連続 — 途中の値も選べる",
    integer: "整数 — 個数など",
    binary: "0-1 — Yes / No",
    categorical: "カテゴリ — A / B / C",
    mixed: "混合 — 複数種類",
    structured_or_unknown: "複雑な構造・まだ分からない",
  },
  Q02: {
    explicit_algebraic: "数式で書ける",
    residual_vector: "誤差の一覧を計算できる",
    automatic_differentiation_graph: "プログラムから自動微分できる",
    simulation_only: "シミュレーションして分かる",
    experiment_only: "実験して初めて分かる",
    unknown: "まだ分からない",
  },
  Q03: {
    linear: "直線的に変わる",
    quadratic: "二次式・放物線に近い",
    sum_of_squares: "誤差の二乗和",
    general_nonlinear: "一般の非線形",
    multiobjective: "複数のものさしがある",
    equation_or_feasibility: "条件を満たす解を探す",
    unknown: "まだ分からない",
  },
  Q04: {
    none: "条件なし",
    bounds: "各xの上下限",
    linear: "直線的な条件",
    nonlinear: "曲線的な条件",
    logical_or_combinatorial: "論理・組合せの条件",
    conic_or_psd: "錐・半正定値の条件",
    dynamics_or_manifold: "時間発展・曲面上の条件",
    implicit_or_failure: "計算して初めて分かる・失敗もある",
  },
  Q05: {
    analytic_gradient: "式から勾配を出せる",
    autodiff: "自動微分できる",
    jacobian_or_hvp: "Jacobian・HVPを出せる",
    numerical_difference_only: "数値差分なら使える",
    stochastic_gradient: "確率勾配を使える",
    unreliable_or_none: "信頼できない・使えない",
    not_differentiable: "滑らかでない・微分できない",
  },
  Q06: {
    milliseconds_or_less: "1ミリ秒以下",
    seconds: "数秒",
    minutes: "数分",
    hours_or_more: "1時間以上",
    unknown: "まだ分からない",
  },
  Q07: {
    deterministic_reliable: "同じxなら同じ結果",
    small_noise: "少しばらつく",
    large_noise: "大きくばらつく",
    random_seeded: "乱数だがseedを固定できる",
    occasional_failure: "時々失敗する",
    frequent_failure: "頻繁に失敗する",
    timeout_possible: "時間切れがある",
    unknown: "まだ分からない",
  },
  Q08: {
    under_10: "10未満",
    "10_to_100": "10〜100",
    "100_to_10000": "100〜10,000",
    over_10000: "10,000超",
    huge_sparse_or_distributed: "巨大・疎・分散型",
    unknown: "まだ分からない",
  },
  Q09: {
    local_is_fine: "近くの良い解で十分",
    global_candidate_desired: "広く探した良い候補がほしい",
    multiple_distinct_solutions: "異なる解を複数ほしい",
    unknown: "まだ分からない",
  },
  Q10: {
    no_certificate_needed: "証明は不要",
    gap_desired: "最良値との差がほしい",
    global_proof_required: "大域最適性の証明が必要",
    feasible_solution_first: "まず条件を満たす解がほしい",
    approximation_guarantee: "近似保証がほしい",
    unknown: "まだ分からない",
  },
  Q11: {
    none_known: "特になし・まだ分からない",
    least_squares: "最小二乗",
    lp_qp_conic: "LP・QP・錐最適化",
    graph_flow_path_matching: "グラフ・フロー・経路・マッチング",
    scheduling_routing: "スケジューリング・経路計画",
    prox_separable: "分けて計算できる・近接作用素を使える",
    optimal_control: "最適制御",
    manifold: "多様体上",
    stochastic_or_robust: "確率的・ロバスト",
    other: "その他",
  },
  Q12: {
    one_off: "一度だけ解く",
    repeated_similar: "似た問題を繰り返す",
    online_or_realtime: "その場で素早く解く",
    parallel_evaluations: "複数のxを同時に試せる",
    distributed: "複数の計算機を使える",
    gpu_available: "GPUを使える",
    warm_start_available: "前回の解から始められる",
  },
};

export function diagnosisChoiceLabel(questionId: string, value: string, fallback: string): string {
  return DIAGNOSIS_CHOICE_LABELS[questionId]?.[value] ?? fallback;
}
