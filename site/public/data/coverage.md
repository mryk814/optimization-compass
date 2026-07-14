# Atlas learning coverage

- Dataset: `0.3.1`
- Generated: `2026-07-15T00:00:00+00:00`
- Baseline: not provided (this initial snapshot does not claim a release delta)

## Expected learning artifacts

| Status | Count |
|---|---:|
| available | 2 |
| partial | 2 |
| missing | 3 |
| not_applicable | 1 |

## Priority slices

| Rank | Slice | Score | Why now |
|---:|---|---:|---|
| 1 | Discrete optimization and search trees | 12/12 | 連続最適化と異なる探索空間・下界・分枝の読み方を代表する。 |
| 2 | Expensive black-box optimization | 11/12 | 評価費と不確実性が手法選択を支配する代表的な問題型である。 |
| 3 | Constrained continuous optimization | 10/12 | 目的改善と実行可能性を同時に扱う主要分類を代表する。 |
| 4 | Multi-objective optimization | 9/12 | 単一の最良解ではなく非劣解集合を扱う分類差が大きい。 |
| 5 | Optimal control and manifolds | 8/12 | 変数が軌道であり、力学・幾何制約を持つ分類を代表する。 |

## Integrity issues

- `broken_scenario_id` `SCENARIO_GD_QUADRATIC`: The canonical database scenario has no generated trace with the same ID.
- `orphan_generated_scenario` `SCENARIO_ADAM_QUADRATIC_DIVERGENCE`: The generated trace scenario is not registered in the canonical database.
- `orphan_generated_scenario` `SCENARIO_BINARY_KNAPSACK_BNB_BUDGET`: The generated trace scenario is not registered in the canonical database.
- `orphan_generated_scenario` `SCENARIO_BINARY_KNAPSACK_BNB_COMPLETE`: The generated trace scenario is not registered in the canonical database.
- `orphan_generated_scenario` `SCENARIO_BO_1D_EXPLOIT_NOISELESS`: The generated trace scenario is not registered in the canonical database.
- `orphan_generated_scenario` `SCENARIO_BO_1D_EXPLOIT_SMALL_NOISE`: The generated trace scenario is not registered in the canonical database.
- `orphan_generated_scenario` `SCENARIO_BO_1D_EXPLORE_NOISELESS`: The generated trace scenario is not registered in the canonical database.
- `orphan_generated_scenario` `SCENARIO_BO_1D_EXPLORE_SMALL_NOISE`: The generated trace scenario is not registered in the canonical database.
- `orphan_generated_scenario` `SCENARIO_GRADIENT_DESCENT_QUADRATIC`: The generated trace scenario is not registered in the canonical database.
- `orphan_generated_scenario` `SCENARIO_GRADIENT_DESCENT_QUADRATIC_DIVERGENCE`: The generated trace scenario is not registered in the canonical database.
- `orphan_generated_scenario` `SCENARIO_MOMENTUM_QUADRATIC_DIVERGENCE`: The generated trace scenario is not registered in the canonical database.
- `orphan_generated_scenario` `SCENARIO_NM_QUADRATIC_SHIFTED`: The generated trace scenario is not registered in the canonical database.
- `orphan_generated_scenario` `SCENARIO_NM_ROSENBROCK_SHIFTED`: The generated trace scenario is not registered in the canonical database.
- `orphan_comparison` `COMPARE_FIRST_ORDER_ROSENBROCK`: The canonical database comparison has no generated comparison with the same ID.
- `orphan_generated_comparison` `COMPARE_GRADIENT_DIVERGENCE`: The generated comparison is not registered in the canonical database.
- `orphan_generated_comparison` `COMPARE_GRADIENT_FAMILY`: The generated comparison is not registered in the canonical database.
