---
content_id: branch-and-cut
kind: method
method_id: M_BRANCH_CUT
title_ja: Branch-and-Cut
title_en: Branch-and-Cut
summary: branch-and-boundへcut生成を組み込み、連続緩和を強化しながらMILPのincumbentとboundを詰める厳密探索法です。
source_ids: [S005, S016, S021, S024, S025, S028]
prerequisites: [branch-and-bound]
related_ids: [branch-and-bound, cp-sat, lp-qp-conic]
aliases: [/learn/branch-and-cut]
status: published
last_reviewed: 2026-07-17
---

branch-and-boundへcut生成を組み込み、連続緩和を強化しながらMILPのincumbentとboundを詰める厳密探索法です。

## 30秒でつかむ

この手法の気持ちは、整数解を残すcutで連続緩和を締め、必要な枝だけを探索して最適性gapを詰めることです。

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

を統合した現代的MILP solverの中心的枠組みです。

## 読むべき三つの値

- **incumbent / primal bound**: 現在見つかっている最良整数実行可能解
- **best bound / dual bound**: 未探索領域から得られる可能性の限界
- **gap**: incumbentとboundの差

minimizationではbest boundがincumbentを下から追い、gapが許容値以下になれば、設定したtoleranceにおける最適性を主張できます。

::: warning
solverが`optimal`と返す場合でも、integrality tolerance、feasibility tolerance、relative / absolute gapを確認します。数学的な完全一致ではなく数値許容値付きの判定です。
:::

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

## Model品質が探索を支配する

Branch-and-Cutの性能はalgorithm parameterだけでなく定式化に強く依存します。

確認項目:

- Big-Mが必要以上に大きくないか
- symmetryがないか
- variable boundsが十分tightか
- strong formulationやvalid inequalityがあるか
- presolveで固定できる変数があるか
- 初期incumbentをwarm startできるか
- coefficient scaleが極端でないか

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

探索木の基本は[Branch-and-Bound](#/learn/branch-and-bound)、論理制約中心のmodelは[CP-SAT](#/learn/cp-sat)で確認できます。
