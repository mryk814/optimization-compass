---
content_id: primal-dual-conic
kind: method
method_id: M_PRIMAL_DUAL_CONIC
title_ja: Primal-dual錐内点法
title_en: Primal-Dual Conic Interior-Point
summary: LPのbarrier法を二次錐や半正定値錐へ一般化し、主・双対・slackを同時に更新してconic標準形の凸問題を解く内点法です。
source_ids: [S013, S014, S028, S010, S055]
prerequisites: [concept.convexity]
related_ids: [barrier-lp-qp, lp-qp-conic, interior-point-nlp]
status: published
last_reviewed: 2026-09-30
---

LPのbarrier法を二次錐や半正定値錐へ一般化し、主・双対・slackを同時に更新してconic標準形の凸問題を解く内点法です。

## 30秒でつかむ

壁へ突き当たる前に距離を保ち、目的と制約の両側から釣合いを整えます。

- 見るもの: 主残差、双対残差、相補性
- 動かすもの: 主変数、双対変数、余裕変数
- 前進の判断: 残差と双対ギャップが同時に小さくなること

## 一手の意味

非負錐の場合、余裕と双対変数の積を正の障壁係数へ合わせます。

$$
s_i z_i=\mu,\qquad s_i>0,\quad z_i>0
$$

主残差と双対残差も同時に小さくするNewton方向を求めます。
一般の錐では、単純な成分積をそのまま使いません。

### Coneで表現できる凸問題の広さ

[LP/QP専用のbarrier法](#/learn/barrier-lp-qp)は非負orthant $x\ge0$ を対象にしますが、主-双対錐内点法はより一般のconic標準形

$$
\min_x\; c^Tx \quad\text{subject to}\quad Ax+s=b,\ \ s\in K
$$

を扱います。
$K$には、非負orthant／second-order cone／positive semidefinite coneなどを組み合わせます。
これにより、一見異なる次の問題を同じ枠組みで表現できます。

- normやrobust制約（second-order cone）
- 行列の固有値やtraceに関する制約（semidefinite cone）
- LP・凸QP（非負orthantとその上の二次項）

「凸性を持つ問題をどこまでconeとして書けるか」というmodeling上の表現力が、この手法群の中心的な価値です。

### Primal-双対 KKT系を同時に更新する仕組み

各反復では、主変数$x$／双対変数$y$／slack変数$s$を同時に更新します。
そのためのNewton方程式を、barrier パラメータを下げながら解きます。

[LP/QP barrier法](#/learn/barrier-lp-qp)と同じく、中心pathに沿って進みます。
違いは、complementarity条件がcone $K$上のbarrier関数に応じた形になる点です。
この関数は対数障壁の一般化です。

反復ごとに、主 feasibility 残差／双対 feasibility 残差／duality gapが得られます。
これらを停止判定と精度確認に使えます。

### Self-双対 embeddingとinfeasibility証明

conic ソルバーの多くは、self-双対 embeddingという技法で元の問題を拡張した自己双対問題に埋め込みます。
この embeddingを解くと、元の問題が実行不可能か非有界かを目的値だけに頼らず、証明として得られる場合があります。
これは「解が見つからなかった」ことと「問題自体に解が存在しない」ことを区別したい場面で重要です。

### Modeling層とソルバー層を分ける

実務では、CVXPY（[S010](https://www.cvxpy.org/)）のようなmodeling層を使います。
modeling層は、norm／固有値／robust制約などを人が読みやすい形式で受け取ります。
これをconic標準形へ変換（canonicalization）してからソルバー層へ渡します。

ソルバー層にはClarabel／SCS／MOSEKなど複数の実装があり、

- 得意とするcone（LP・QPのみか、semidefiniteまで扱うか）
- 収束の速さと精度のtrade-off
- 初期解の再利用やsparsity対応の有無

が異なります。
modeling層とソルバー層は役割が別であり、どちらのversionを使ったかを区別して記録する必要があります。

## 小さな例

錐の最も簡単な例として、$\min x$、$x-1=s\ge0$ を使います。
双対変数は $y=1$ です。
中心経路では $sy=\mu$ を満たすので、$x=1+\mu$ となります。

| 障壁係数 $\mu$ | 主変数 $x$ | 余裕 $s$ | 双対値 $y$ | 主双対の目的差 |
|---|---:|---:|---:|---:|
| 1.00 | 2.00 | 1.00 | 1.00 | 1.00 |
| 0.50 | 1.50 | 0.50 | 1.00 | 0.50 |
| 0.25 | 1.25 | 0.25 | 1.00 | 0.25 |

$\mu$ を下げると、可行性を保って境界 $x=1$ へ近づきます。
これは中心経路上の3点を計算した例で、Newton反復そのものではありません。
二次錐や半正定値錐では、余裕と相補性の幾何が変わります。

## 向く条件・避ける条件

### 向いている条件

| 条件 | 理由 |
|---|---|
| norm・固有値・robust制約などconic標準形で表現できる | この手法の適用範囲がconeの表現力に依存するため |
| 主/双対・duality gap・infeasibility 証明が重要 | 主-双対 KKT系を同時に解くことでこれらが得られるため |
| modeling層で問題を組み、backend ソルバーへ任せたい | CVXPY等がcanonicalizationとソルバー呼び出しを分離しているため |
| 高精度な解や証明が必要 | barrier型内点法は反復ごとにfeasibilityとgapを追えるため |

modeling層に収まらない非凸な制約や、ブラックボックスな評価しかできない目的関数には向きません。
そうした場合は非線形内点法や大域探索を検討します。

## Python

次はsecond-order cone制約 $\lVert Ax-b\rVert_2 \leq t$ をCVXPYで記述する最小例です。
modeling層がconic標準形へ変換し、対応ソルバーへ渡します。

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

実装は[CVXPYの公式ドキュメント](https://www.cvxpy.org/)でconic標準形への変換方法を、ソルバーの反復挙動やoptionは[Clarabelの公式ドキュメント](https://clarabel.org/stable/)で確認します。
利用versionによってdefault パラメータやbackendの対応coneが異なるため、必ず該当versionのreferenceを参照します。

## 診断値

- 主 feasibility 残差
- 双対 feasibility 残差
- duality gap（absolute / relative）
- barrier パラメータ
- complementarity
- infeasibility 証明の有無
- 反復数とNewton system 求解のcondition

## 失敗・切替の兆候

- barrier パラメータを下げてもduality gapが縮まらない
- 実行不可能/非有界の証明が返るのに目的値だけで成功と誤判定する
- coneの選び方が問題の凸構造を正しく表現できていない
- 係数の尺度が極端でNewton system 求解にnumerical warningが出る
- modeling層のcanonicalizationがソルバーの対応coneと合わない

## 次に読む

LP/QP専用のbarrier法との対比は、[Primal-双対 barrier法（LP/QP）](#/learn/barrier-lp-qp)で確認できます。
conic問題を含む全体の位置付けは、[LP・QP・錐最適化](#/learn/lp-qp-conic)へ進みます。
非線形制約への一般化は[非線形内点法](#/learn/interior-point-nlp)で確認できます。

- 問題の形を確認する: [二次錐計画](#/formulations/PA020)
