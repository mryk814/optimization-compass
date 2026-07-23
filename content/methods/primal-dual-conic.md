---
content_id: primal-dual-conic
kind: method
method_id: M_PRIMAL_DUAL_CONIC
title_ja: Primal-dual錐内点法
title_en: Primal-Dual Conic Interior-Point
summary: LPのbarrier法を二次錐や半正定値錐へ一般化し、primal・dual・slackを同時に更新してconic標準形の凸問題を解く内点法です。
source_ids: [S013, S014, S028, S010, S055]
prerequisites: [concept.convexity]
related_ids: [barrier-lp-qp, lp-qp-conic, interior-point-nlp]
status: published
last_reviewed: 2026-07-24
---

LPのbarrier法を二次錐や半正定値錐へ一般化し、primal・dual・slackを同時に更新してconic標準形の凸問題を解く内点法です。

## Coneで表現できる凸問題の広さ

[LP/QP専用のbarrier法](#/learn/barrier-lp-qp)は非負orthant $x\ge0$ を対象にしますが、primal-dual錐内点法はより一般のconic標準形

$$
\min_x\; c^Tx \quad\text{subject to}\quad Ax+s=b,\ \ s\in K
$$

を扱います。$K$には、非負orthant／second-order cone／positive semidefinite coneなどを組み合わせます。これにより、一見異なる次の問題を同じ枠組みで表現できます。

- normやrobust制約（second-order cone）
- 行列の固有値やtraceに関する制約（semidefinite cone）
- LP・凸QP（非負orthantとその上の二次項）

「凸性を持つ問題をどこまでconeとして書けるか」というmodeling上の表現力が、この手法群の中心的な価値です。

## Primal-dual KKT系を同時に更新する仕組み

各反復では、primal変数$x$／dual変数$y$／slack変数$s$を同時に更新します。そのためのNewton方程式を、barrier parameterを下げながら解きます。

[LP/QP barrier法](#/learn/barrier-lp-qp)と同じく、中心pathに沿って進みます。違いは、complementarity条件がcone $K$上のbarrier関数に応じた形になる点です。この関数は対数障壁の一般化です。

反復ごとに、primal feasibility residual／dual feasibility residual／duality gapが得られます。これらを停止判定と精度確認に使えます。

## Self-dual embeddingとinfeasibility証明

conic solverの多くは、self-dual embeddingという技法で元の問題を拡張した自己双対問題に埋め込みます。この embeddingを解くと、元の問題がinfeasibleかunboundedかを目的値だけに頼らず、certificateとして得られる場合があります。これは「解が見つからなかった」ことと「問題自体に解が存在しない」ことを区別したい場面で重要です。

## Modeling層とsolver層を分ける

実務では、CVXPY（[S010](https://www.cvxpy.org/)）のようなmodeling層を使います。modeling層は、norm／固有値／robust制約などを人が読みやすい形式で受け取ります。これをconic標準形へ変換（canonicalization）してからsolver層へ渡します。

solver層にはClarabel／SCS／MOSEKなど複数の実装があり、

- 得意とするcone（LP・QPのみか、semidefiniteまで扱うか）
- 収束の速さと精度のtrade-off
- warm startやsparsity対応の有無

が異なります。modeling層とsolver層は役割が別であり、どちらのversionを使ったかを区別して記録する必要があります。

## 向いている条件

| 条件 | 理由 |
|---|---|
| norm・固有値・robust制約などconic標準形で表現できる | この手法の適用範囲がconeの表現力に依存するため |
| primal/dual・duality gap・infeasibility certificateが重要 | primal-dual KKT系を同時に解くことでこれらが得られるため |
| modeling層で問題を組み、backend solverへ任せたい | CVXPY等がcanonicalizationとsolver呼び出しを分離しているため |
| 高精度な解や証明が必要 | barrier型内点法は反復ごとにfeasibilityとgapを追えるため |

modeling層に収まらない非凸な制約や、black-boxな評価しかできない目的関数には向きません。そうした場合は非線形内点法や大域探索を検討します。

## Python

次はsecond-order cone制約 $\lVert Ax-b\rVert_2 \leq t$ をCVXPYで記述する最小例です。modeling層がconic標準形へ変換し、対応solverへ渡します。

```python
import cvxpy as cp
import numpy as np

A = np.array([[1.0, 2.0], [-1.0, 1.0]])
b = np.array([1.0, 0.0])
c = np.array([1.0, -0.5])

x = cp.Variable(2)
t = cp.Variable(nonneg=True)
problem = cp.Problem(
    cp.Minimize(c @ x + t),
    [cp.norm(A @ x - b, 2) <= t, x >= 0],
)
value = problem.solve(solver="CLARABEL")

print(problem.status, value)
print("x:", x.value, "cone radius:", t.value)
```

実装は[CVXPYの公式ドキュメント](https://www.cvxpy.org/)でconic標準形への変換方法を、solverの反復挙動やoptionは[Clarabelの公式ドキュメント](https://clarabel.org/stable/)で確認します。利用versionによってdefault parameterやbackendの対応coneが異なるため、必ず該当versionのreferenceを参照します。

## 診断値

- primal feasibility residual
- dual feasibility residual
- duality gap（absolute / relative）
- barrier parameter
- complementarity
- infeasibility certificateの有無
- iteration数とNewton system solveのcondition

## 失敗・切替の兆候

- barrier parameterを下げてもduality gapが縮まらない
- infeasible/unboundedの証明が返るのに目的値だけで成功と誤判定する
- coneの選び方が問題の凸構造を正しく表現できていない
- 係数のscaleが極端でNewton system solveにnumerical warningが出る
- modeling層のcanonicalizationがsolverの対応coneと合わない

## 次に読む

LP/QP専用のbarrier法との対比は、[Primal-dual barrier法（LP/QP）](#/learn/barrier-lp-qp)で確認できます。conic問題を含む全体の位置付けは、[LP・QP・錐最適化](#/learn/lp-qp-conic)へ進みます。非線形制約への一般化は[非線形内点法](#/learn/interior-point-nlp)で確認できます。
