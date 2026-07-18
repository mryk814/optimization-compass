---
content_id: barrier-lp-qp
kind: method
method_id: M_BARRIER_LP_QP
title_ja: Primal-dual barrier法（LP/QP）
title_en: Primal-Dual Barrier Method for LP/QP
summary: 不等式制約を対数障壁（log barrier）へ置き換え、中心path（central path）に沿ってNewton stepで進むLP/QP専用の内点法です。
source_ids: [S016, S004, S055, S056]
prerequisites: [concept.convexity]
related_ids: [primal-simplex, dual-simplex, interior-point-nlp, lp-qp-conic]
aliases: [/learn/barrier-lp-qp]
status: published
last_reviewed: 2026-07-18
---

不等式制約を対数障壁（log barrier）へ置き換え、中心path（central path）に沿ってNewton stepで進むLP/QP専用の内点法です。

## 何を追って中心pathを進むか

LP標準形 $\min_x c^Tx$ subject to $Ax=b,\ x\ge0$ を考えると、barrier法は非負制約をlog barrierで置き換えます。

$$
\min_x\; c^Tx-\mu\sum_i\log x_i \quad\text{subject to}\quad Ax=b
$$

$\mu>0$を固定した解の集合を$\mu\to0$へ動かした軌跡が中心pathです。各$\mu$での最適性条件（KKT条件にcomplementarity $x_is_i=\mu$を加えたもの）を満たす点を追いながら、$\mu$を段階的に小さくしていきます。

## Newton stepで何を解いているか

各反復では、primal変数$x$、dual変数$y$、slack/dual変数$s$を同時に更新するNewton方程式を解きます。線形化されたKKT systemは対称かつ疎になることが多く、$\mu$を下げながらcomplementarity $x^Ts$を0へ近づけます。QPでも同様に、目的関数の二次項を含めたKKT systemを同じ枠組みで扱います。反復ごとにこの線形系を作り直して解く点が、[operator-splitting QP](#/learn/admm-qp)のようにfactorizationを固定して使い回す方式との違いです。

## Simplexとの違い

primal/dual simplexは頂点（basis）を辿って移動しますが、barrier法は多面体の内部を進み、頂点上のbasisを直接維持しません。

- 反復回数は問題規模にほぼ依存しにくい一方、1反復あたりのNewton system solveは重くなり得ます
- barrier法は明示的なbasisを返さないため、basisが必要な後続処理（sensitivity解析やwarm restartなど）にはcrossoverでbasic solutionへ変換する工程が使われる場合があります
- 停止判定はprimal/dual feasibility residualとduality gapで行い、simplexのようなreduced costの符号条件とは異なります

一般の非線形制約を持つ問題でのbarrier法の考え方は[非線形内点法](#/learn/interior-point-nlp)で扱っており、この記事はLP/QPという凸で構造化された場合に限定します。

## 向いている条件

| 条件 | 理由 |
|---|---|
| LP/QP/conic構造が明示できる | 中心pathの議論がこれらの標準形に依存するため |
| 大規模・疎な問題 | 疎なKKT systemのfactorizationを利用できるため |
| 明確なduality gapで停止判定したい | primal/dual feasibilityとgapが直接得られるため |
| basisを必ずしも必要としない | barrier法自体はbasisを維持しないため |

## 避ける／切り替える条件

- basisやwarm startによる再最適化を頻繁に行いたい（[primal simplex](#/learn/primal-simplex)や[dual simplex](#/learn/dual-simplex)が候補）
- 制約や目的が非線形で、LP/QP標準形に収まらない
- coefficient scaleが極端で数値warningが出る
- crossoverのcostが許容できないほど大きい

## Python

```python
import numpy as np
from scipy.optimize import linprog

cost = np.array([-3.0, -2.0])
a_ub = np.array([
    [1.0, 1.0],
    [2.0, 1.0],
])
b_ub = np.array([4.0, 5.0])

result = linprog(
    cost,
    A_ub=a_ub,
    b_ub=b_ub,
    bounds=[(0.0, None), (0.0, None)],
    method="highs-ipm",
)

print(result.success, result.x, -result.fun, result.status, result.message)
```

`method="highs-ipm"`はHiGHSのinterior-point solverを明示的に指定します。同じ問題を`method="highs-ds"`（dual simplex）と比べる場合、iteration数だけでなく1反復あたりのfactorization費用を含めて比較します。solverが持つcrossoverの有無やdefault parameterは利用versionの[公式SciPyリファレンス](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linprog.html)や[HiGHSドキュメント](https://highs.dev/)で確認します。

## 診断値

- primal feasibility residual
- dual feasibility residual
- duality gap（absolute / relative）
- barrier parameter $\mu$
- complementarity（$x^Ts$）
- KKT system condition
- crossoverの有無とcost

## 失敗・切替の兆候

- $\mu$を下げてもduality gapが縮まらない
- KKT systemのfactorizationがmemoryを圧迫する
- coefficient scaleが桁違いでnumerical warningが出る
- infeasibleまたはunboundedの状態を目的値だけで見落とす
- crossover後のbasisが数値的に不安定

## 次に読む

LP basisを保った再最適化は[Primal Simplex](#/learn/primal-simplex)と[Dual Simplex](#/learn/dual-simplex)、非線形制約への一般化は[非線形内点法](#/learn/interior-point-nlp)、LP・QP・conic全体の位置付けは[LP・QP・錐最適化](#/learn/lp-qp-conic)で確認できます。
