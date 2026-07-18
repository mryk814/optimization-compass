---
content_id: primal-simplex
kind: method
method_id: M_SIMPLEX
title_ja: Primal simplex法
title_en: Primal Simplex
summary: LPの実行可能なbasisを保ちながら、被約費用が示す隣接basisへpivotし、目的値を改善するsimplex法です。
source_ids: [S004, S016, S055]
prerequisites: [concept.convexity]
related_ids: [dual-simplex, lp-qp-conic, family.discrete-structure]
aliases: [/learn/primal-simplex]
status: published
last_reviewed: 2026-07-18
---

LPの実行可能なbasisを保ちながら、被約費用が示す隣接basisへpivotし、目的値を改善するsimplex法です。

## LPの頂点とbasis

線形計画問題の実行可能領域は多面体です。
目的関数が線形で最適値が有限なら、最適解は多面体のどこかの頂点、つまりbasic feasible solutionに存在します。
内部の点をわずかに動かしても目的値は線形にしか変化しないため、頂点の集合だけを調べれば最適解を取りこぼしません。

$n$個の変数と$m$本の等式制約からなる標準形では、頂点は$m$個の変数を基底（basis）として選び、残りを$0$に固定した解に対応します。
primal simplexは、常にprimal feasibleなbasisを保ったまま、より目的値の良い隣接basisへ移動を繰り返します。

## 被約費用とpivotの直感

現在のbasisで、非基底変数$x_j$を$1$単位だけ増やしたときの目的値の変化量を被約費用（reduced cost）と呼びます。

$$
\bar{c}_j = c_j - c_B^T B^{-1} A_j
$$

最小化問題では、$\bar{c}_j < 0$となる非基底変数が存在すれば、その変数を増やすことで目的値を改善できます。
この変数を**entering variable**として選び、基底変数のどれかが実行可能性の境界（多くは非負制約）に達するまで増やします。
境界に達した基底変数が**leaving variable**としてbasisから外れ、新しいbasisに置き換わる操作がpivotです。
すべての非基底変数で$\bar{c}_j \ge 0$になれば、それ以上改善する方向がなく最適basisに到達したと判断できます。

## 退化・cycling・infeasible/unboundedの見分け方

leaving variableの候補が複数（境界までの余裕が同時に$0$）になる状況をdegeneracyと呼びます。degenerateなpivotでは目的値が変化しないまま基底だけが入れ替わり、選び方によっては同じbasisの列を巡回するcyclingが起こり得ます。entering/leaving変数の選び方（pivot rule）はcyclingを避けるための実装上の工夫です。

探索の結果は次のいずれかに分類されます。

- 最適basisに到達した（すべての被約費用が最適性条件を満たす）
- 実行可能な初期basisが存在しない（infeasible）
- ある方向へ目的値を改善し続けても実行可能領域から出ない（unbounded）

`infeasible`と`unbounded`は別の状態であり、どちらも「解なし」とひとまとめにはできません。

## 向いている条件

| 条件 | 理由 |
|---|---|
| 問題が線形（LP）として明示できる | basisと被約費用の議論がLPの構造に依存するため |
| basisをwarm startとして再利用したい | 直前のbasisから近い解を得やすいため |
| basis・被約費用として解釈したい | 頂点・活性制約・sensitivityが読みやすいため |
| sparse構造がある | factorizationの計算量を抑えやすいため |

大規模で密なLPや、barrier法のように反復ごとの計算量を均したい場合はinterior-point法も候補になります。両者は「一反復あたりの仕事量」も異なるため、iteration数だけで比較しません。

## Python

```python
import numpy as np
from scipy.optimize import linprog


def build_problem() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    cost = np.array([-3.0, -2.0])
    a_ub = np.array([
        [1.0, 1.0],
        [2.0, 1.0],
    ])
    b_ub = np.array([4.0, 5.0])
    return cost, a_ub, b_ub


cost, a_ub, b_ub = build_problem()
result = linprog(
    cost,
    A_ub=a_ub,
    b_ub=b_ub,
    bounds=[(0.0, None), (0.0, None)],
    method="highs",
)

print(result.success, result.x, -result.fun, result.status, result.message)
```

`scipy.optimize.linprog`はHiGHSをbackendとしており、simplexとinterior-pointの選び分けは`method`optionに従います。`method="highs"`はpresolveの判断に応じてsolverが内部でroutineを選び、`method="highs-ds"`はHiGHSのdual simplexを明示的に指定します。primal simplexをどのoptionで明示的に選べるかはHiGHSのversionに依存するため、利用versionで用意されているoptionは[公式SciPyリファレンス](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linprog.html)で確認します。

## 診断値

- primal feasibility residual
- objective value（$-$`result.fun`は元の最大化目的への符号戻し）
- basis status / active constraints
- simplex iteration数
- degeneracy（同一目的値でのpivot継続）
- presolve reduction
- condition（factorizationの数値的な安定性）

::: warning
「primal simplexを使った」だけでは再現条件として不十分です。presolveの有無、scaling、pivot rule、boundsの与え方を一緒に記録します。
:::

## 失敗・切替の兆候

- presolveの段階でinfeasibleと判定される
- 目的値が改善しないままiteration数だけが増える（degeneracy/stalling）
- 係数のscaleが桁違いで数値warningが出る
- factorizationがmemoryを圧迫する大規模denseなLP
- 反復のたびに同じ頂点集合を巡回している疑いがある

## 次に読む

被可行性の向きを変えたsimplex変種は[Dual Simplex](#/learn/dual-simplex)、LP・QP・conic全体の位置付けは[LP・QP・錐最適化](#/learn/lp-qp-conic)、離散変数を含む問題での役割は[離散・組合せ最適化の選び分け](#/learn/family.discrete-structure)で確認できます。
