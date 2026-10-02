---
content_id: admm-qp
kind: method
method_id: M_ADMM_QP
title_ja: Operator-splitting QP（ADMM型）
title_en: ADMM / Operator-Splitting QP
summary: 凸二次計画（凸 QP）を固定した分割構造で反復し、同じ線形系の因数分解を使い回しながら作用素分割で解く専用ソルバーの方式です。
source_ids: [S012, S062, S055, S010]
prerequisites: [concept.convexity]
related_ids: [admm, lp-qp-conic, proximal-gradient]
aliases: [/learn/admm-qp]
visualization_ids: [repeated-mpc-qp-warm-start, repeated-mpc-qp-cold-start]
comparison_ids: [COMPARE_REPEATED_MPC_QP_WARM_START]
status: published
last_reviewed: 2026-09-30
---

凸二次計画（凸 QP）を固定した分割構造で反復し、同じ線形系の因数分解を使い回しながら作用素分割で解く専用ソルバーの方式です。

## 30秒でつかむ

同じ型の部品を繰り返し加工するとき、治具を一度作って使い回すように、線形系の因数分解を再利用します。

- 見るもの: 制約との不一致と双対残差
- 動かすもの: 主変数、補助変数、双対変数
- 前進の判断: 両残差が必要精度へ近づくこと

## 一手の意味

箱型制約の教育用例では、固定した行列で $x$ を求め、$z$ を区間へ射影します。

$$
(P+\rho I)x_{k+1}=-q+\rho(z_k-u_k),\qquad
z_{k+1}=\Pi_{[l,u]}(x_{k+1}+u_k),\qquad
u_{k+1}=u_k+x_{k+1}-z_{k+1}
$$

一般の $Ax$ を含むOSQPの反復とは、補助変数の定義と線形系が異なります。

### 何を固定して反復するか

[ADMM](#/learn/admm)は$f$と$g$の分け方を問題ごとに設計する汎用枠組みですが、QP専用ソルバーは分割構造をあらかじめ固定します。
代表形は

$$
\min_x \frac{1}{2}x^TPx+q^Tx\quad\text{subject to}\quad l\le Ax\le u
$$

$P\succeq0$なら凸QPです。
OSQPはこの形をそのまま受け取り、$x$と補助変数$z=Ax$を分けて交互に更新します。
設計上の自由度を減らす代わりに、同じKKT行列を反復全体で固定して使えるようにしています。

### 因数分解を1回で使い回す仕組み

各反復は次を繰り返します。

1. $x$を更新する線形系を解く（KKT行列は$\rho$を固定する限り不変）
2. $z$を$[l,u]$へ射影する
3. 双対変数を更新する

$P$・$A$・罰則係数 $\rho$が固定なら、KKT行列は反復間で変わりません。
最初の反復で因数分解（Choleskyや$LDL^T$）を1度だけ計算します。
以降の反復では前進後退代入だけで済ませられます。
これが内点法のように、反復ごとに行列を作り直す方式との大きな違いです。

## 小さな例

$x^2-2x$ を $0\le x\le0.5$ の範囲で最小化します。
係数は $P=2$、$q=-2$、$\rho=1$ です。
$x=z=u=0$ から始めます。

| 反復 | 線形系の解 $x$ | 射影後の $z$ | 双対変数 $u$ |
|---|---:|---:|---:|
| 1 | 0.667 | 0.500 | 0.167 |
| 2 | 0.778 | 0.500 | 0.444 |
| 3 | 0.685 | 0.500 | 0.630 |

$z$ は上限を守りますが、途中の $x$ は上限を超えます。
採用する解の可行性は残差で確認します。

## 向く条件・避ける条件

### まず確認すること

作用素分割は1反復が軽く、初期解の再利用や同じ問題構造の逐次再解に向きます。
例として、モデル予測制御やポートフォリオの配分調整の定期再最適化があります。
一方、高精度な最適解へ収束させるには反復数がかさむことがあります。
厳密な基底・証明・高い双対ギャップ精度が要る場合は、[主-双対障壁法](#/learn/barrier-lp-qp)など別方式を検討します。

同じ疎構造のQPを繰り返し中精度で解くなら、因数分解再利用の利点が大きくなります。

### 向いている条件

| 条件 | 理由 |
|---|---|
| 凸QP（$P\succeq0$）として明示できる | 分割構造がQPの標準形に依存するため |
| 疎な係数行列 | 因数分解と行列とベクトルの積を軽くできるため |
| 同じ構造のQPを繰り返し解く | KKT行列と因数分解を使い回せるため |
| 中精度で運用上十分 | 主/双対残差の収束が漸近的なため |

### 避ける／切り替える条件

- 非凸QPを凸として誤って扱っている
- $\rho$や尺度調整が悪く残差が一方だけ停滞する
- 高精度な証明や厳密な基底が必要
- 制約や目的が線形・二次形式に収まらない非線形構造

## Python

次は箱型制約QPをADMM型反復で解く教育用の例です。
対象は$\min_x \frac{1}{2}x^TPx+q^Tx$ 制約 $l\le x\le u$です。
$P+\rho I$のCholesky因数分解を1回だけ計算し、反復全体で使い回します。

```python
import numpy as np


def solve_box_qp_admm(
    p: np.ndarray,
    q: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    rho: float = 1.0,
    n_iter: int = 200,
) -> tuple[np.ndarray, np.ndarray, float, float]:
    n = q.shape[0]
    factor = np.linalg.cholesky(p + rho * np.eye(n))  # 反復間で使い回す
    x = np.zeros(n)
    z = np.zeros(n)
    y = np.zeros(n)
    for _ in range(n_iter):
        rhs = -q + rho * (z - y)
        w = np.linalg.solve(factor, rhs)
        x = np.linalg.solve(factor.T, w)
        z_prev = z
        z = np.clip(x + y, lower, upper)
        y = y + x - z
    primal_residual = float(np.linalg.norm(x - z))
    dual_residual = float(rho * np.linalg.norm(z - z_prev))
    return x, z, primal_residual, dual_residual


p = np.array([[4.0, 1.0], [1.0, 2.0]])
q = np.array([1.0, 1.0])
lower = np.array([-1.0, -1.0])
upper = np.array([1.0, 1.0])

x, z, primal_residual, dual_residual = solve_box_qp_admm(p, q, lower, upper)
print(x, z, primal_residual, dual_residual, 0.5 * x @ p @ x + q @ x)
```

より一般の$Ax$を含む形や錐制約を扱う場合は、[OSQP公式ドキュメント](https://osqp.org/docs/)を確認します。
成熟した初期解の再利用や前処理を使う場合も同様です。
利用バージョンのAPIと`default parameter`は、公式資料で確認します。

## 診断値

- 主残差（$\|Ax-z\|$相当）
- 双対残差
- 目的値
- $\rho$（罰則係数）と尺度調整
- 反復数
- 因数分解再利用回数

## 失敗・切替の兆候

- `primal residual`／`dual residual`の一方だけが停滞する
- 実行不可能または非有界の証明が返る
- 係数の尺度が桁違いで数値警告が出る
- 同じ精度要求に対し反復数が増え続ける
- 非凸な$P$を凸QPとして与えてしまっている

### 反復MPCで初期解の再利用を読む

[初期解の再利用の実行記録](#/traces/repeated-mpc-qp-warm-start)と[初期解なしの求解の実行記録](#/traces/repeated-mpc-qp-cold-start)は、同じMPC QPを周期ごとに解く固定教材です。
[初期解の再利用の比較](#/compare/COMPARE_REPEATED_MPC_QP_WARM_START)では、問題・上下限・残差・期限の判定規則を固定します。
変えるのは、前周期の解を再利用するかどうかだけです。

ここで読むのは、各周期の残差と期限余裕です。
CPU・OS・線形代数バックエンド・実装固有のキャッシュや時間のばらつきを測ったベンチマークではありません。
初期解の再利用が初回解や実機遅延を必ず改善するとも主張しません。

## 次に読む

分割構造を自分で設計したい場合は[ADMM](#/learn/admm)を確認します。
単一の近接演算で済む問題は[近接勾配法](#/learn/proximal-gradient)へ進みます。
LP・QP・錐全体の位置付けは[LP・QP・錐最適化](#/learn/lp-qp-conic)で確認できます。

- 問題の形を確認する: [凸二次計画](#/formulations/PA018)
