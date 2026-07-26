---
content_id: branch-and-cut
kind: method
method_id: M_BRANCH_CUT
title_ja: Branch-and-Cut
title_en: Branch-and-Cut
summary: MILPをbranch-and-boundで探索しながらcutで連続緩和を強化し、incumbentとboundのgapを詰めて最適性を証明する厳密探索法です。
source_ids: [S005, S016, S021, S024, S025, S028]
prerequisites: [branch-and-bound]
related_ids: [branch-and-bound, cp-sat, lp-qp-conic]
aliases: [/learn/branch-and-cut]
visualization_ids: [binary-knapsack-bnb-complete, binary-knapsack-bnb-budget]
comparison_ids: [COMPARE_KNAPSACK_BNB_BUDGET]
status: published
last_reviewed: 2026-07-26
---

MILPをbranch-and-boundで探索しながらcutで連続緩和を強化し、incumbentとboundのgapを詰めて最適性を証明する厳密探索法です。

## 30秒でつかむ

この手法の気持ちは、整数解を残したまま不要な枝を切り、見るべき探索だけに集中することです。

整数解を残すcutで連続緩和を締めると、改善不能な枝を早く除外できます。
それでも残る枝だけを探索し、incumbentとbest boundのgapを詰めます。

- **見るもの**: LP relaxation、fractional解、incumbent、best bound、gap
- **動かすもの**: 探索木、各nodeのrelaxation、追加するcut
- **前進の判断**: incumbentとbest boundのgapが設定したtoleranceへ近づくこと

## Cutは何をするか

MILPのLP relaxationは整数条件を外すため、整数実行可能解より良すぎるfractional解を返すことがあります。cutting planeは、

- すべての整数実行可能解を残す
- 現在のfractional解を除外する

不等式を追加し、relaxationを強くします。

Branch-and-Cutは、

1. presolve
2. LP relaxation
3. cut separation
4. primal heuristic
5. branching
6. node pruning

を統合した現代的なMILPソルバーの中心的枠組みです。

## boundとgapをどう読むか

- **incumbent / primal bound**: 現在見つかっている最良整数実行可能解
- **best bound / dual bound**: 未探索領域から得られる可能性の限界
- **gap**: incumbentとboundの差

minimizationではbest boundがincumbentを下から追い、gapが許容値以下になれば、設定したtoleranceにおける最適性を主張できます。

::: warning
ソルバーが`optimal`と返す場合でも、整数許容誤差と実行可能性許容誤差を確認します。
相対gapと絶対gapも含め、数学的な完全一致ではなく数値許容値付きの判定です。
:::

## 探索木で基礎部分を確認する

[最後まで探索した木](#/theater/learning/SCENARIO_BINARY_KNAPSACK_BNB_COMPLETE)では、incumbentの更新とboundによる枝刈りを追えます。
最後にgapが閉じるところまで確認できます。
[予算で止めた木](#/theater/learning/SCENARIO_BINARY_KNAPSACK_BNB_BUDGET)では、同じ問題を途中で止めたときに何が未証明として残るかを確認できます。

[2つの停止条件を並べる](#/compare/COMPARE_KNAPSACK_BNB_BUDGET)では、問題とseedを固定しています。
branch順、bound計算、評価予算も同じです。
nodeの停止上限だけを変えた差を読めます。

これらはBranch-and-Cutの土台であるBranch-and-Boundの教材です。
cut生成、separation round、root relaxationの強化そのものは表示しません。
Branch-and-Cut実装のsolver rankingでもありません。

## まず確認すること

Branch-and-Cutの性能はアルゴリズムの設定値だけでなく、定式化に強く依存します。

確認項目:

- Big-Mが必要以上に大きくないか
- symmetryがないか
- variable boundsが十分tightか
- strong formulationやvalid inequalityがあるか
- presolveで固定できる変数があるか
- 初期incumbentをwarm startできるか
- 係数の桁が極端でないか

## Python: MILPをsolverへ渡す

次の例ではcutやbranchingを手実装せず、HiGHS backendへmodelを渡します。

```python
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

values = np.array([8.0, 5.0, 6.0, 4.0])
weights = np.array([4.0, 3.0, 5.0, 2.0])

result = milp(
    c=-values,
    integrality=np.ones(len(values)),
    bounds=Bounds(np.zeros(len(values)), np.ones(len(values))),
    constraints=LinearConstraint(weights, -np.inf, 8.0),
    options={"time_limit": 30.0, "mip_rel_gap": 1e-6},
)

print(result.success, result.x, -result.fun, result.message)
```

実装がどのcut familyを有効にするか、どのheuristicを使うかはsolverとversionに依存します。

## 診断値

- root relaxation gap
- incumbent / best bound / relative gap
- node count
- LP iteration数
- cut countとcut efficacy
- feasible solutionが最初に見つかるまでの時間
- memory
- presolve reduction
- termination reason

## CP-SATとの違い

Branch-and-Cutは線形緩和が強いMILPで力を発揮します。CP-SATは論理関係、reification、scheduling global constraintなどを自然に表現できる場合があります。どちらが良いかは、同じ現実問題でも定式化によって変わります。

## 失敗・切替の兆候

- root gapが大きいまま
- node数が指数的に増える
- incumbentが長時間見つからない
- memoryがtreeで増大
- Big-Mによる数値warning
- symmetryで同等解を繰り返し探索
- 専用flow、matching、DP、CP構造を無視している

## 次に読む

探索木の基本は[Branch-and-Bound](#/learn/branch-and-bound)、論理制約中心のmodelは[CP-SAT](#/learn/cp-sat)で確認できます。
