---
content_id: trust-krylov
kind: method
method_id: M_TRUST_KRYLOV
title_ja: Trust-region Krylov法
title_en: Trust-Region Krylov
summary: Hessian-vector積から作るKrylov部分空間でtrust-region部分問題を近似し、大規模な滑らか問題へ曲率を安全に利用する局所法です。
source_ids: [S002, S056]
related_ids: [family.smooth-local, newton-cg, trust-region-newton-cg]
status: published
last_reviewed: 2026-07-16
---

Hessian-vector積から作るKrylov部分空間でtrust-region部分問題を近似し、大規模な滑らか問題へ曲率を安全に利用する局所法です。

## 30秒でつかむ

この手法の気持ちは、**高次元空間を全部詳しく見る代わりに、勾配とHessianが作る重要な方向だけを集めた小さな空間で、信用できる一歩を探したい**というものです。

- 見ているもの: gradient、Hessian-vector積、局所modelの予測改善
- 動かしているもの: Krylov部分空間、trust radius、候補step
- 前進の判断: 実際の改善とmodel予測の比
- 恐れていること: 悪い局所model、HVP誤差、半径の過小化

Newton-CGと似ていますが、line searchで方向の長さを決めるより、trust-region部分問題として方向と長さを同時に扱います。

## まず確認すること

| 項目 | 確認内容 |
|---|---|
| objective | 二階近似が意味を持つ程度に滑らかか |
| gradient / HVP | 高精度かつ効率的に計算できるか |
| dimension | dense Hessianを作らずに済む価値があるか |
| nonconvexity | 負の曲率を見つける意味があるか |
| constraints | 無制約問題か、対応する制約付きvariantが必要か |

一反復の目的評価が高価な場合、候補stepの拒否回数もbudgetとして記録します。

## 仕組み

局所二次modelを、半径 $\Delta_k$ の内側で最小化します。

$$
\min_p\; g_k^T p + \frac{1}{2}p^T H_k p
\quad \text{subject to}\quad \lVert p\rVert \leq \Delta_k
$$

高次元ではこの部分問題を全空間で解かず、HVPから構成したKrylov部分空間で近似します。候補stepを評価した後、actual / predicted reduction比に応じて採用と半径更新を行います。

## 向く条件・避ける条件

向きやすい条件:

- 大規模で滑らかな無制約問題
- HVPを自動微分や構造から得られる
- 不定Hessianや負の曲率を無視したくない
- line searchより局所modelの信頼度を明示したい

避ける条件:

- gradient / HVPがnoiseに支配される
- 不連続・離散・black-box評価のみ
- 部分問題solveが目的評価より支配的
- 一般制約や大域certificateが必要

## うまくいったサインと切替サイン

見る値:

- trust radius
- actual / predicted reduction比
- accepted / rejected step数
- Krylov iteration数
- gradient norm
- negative curvature detection

切替サイン:

- 半径が縮み続ける → model、scaling、HVPを確認
- step拒否が多い → 二次近似の範囲が悪いかnoiseを疑う
- Krylov反復が上限に張り付く → preconditioningや低精度solveを検討
- 曲率を使っても改善しない → L-BFGSや一階法とのcost比較
- 初期値で解が変わる → local methodであることを受け入れるかglobal探索へ

## Python

```python
import numpy as np
from scipy.optimize import minimize

A = np.diag([1.0, 10.0, 100.0])


def objective(x: np.ndarray) -> float:
    return float(0.5 * x @ A @ x)


def gradient(x: np.ndarray) -> np.ndarray:
    return A @ x


def hessian_product(x: np.ndarray, vector: np.ndarray) -> np.ndarray:
    del x
    return A @ vector


result = minimize(
    objective,
    x0=np.array([2.0, -1.0, 0.5]),
    jac=gradient,
    hessp=hessian_product,
    method="trust-krylov",
)
print(result.success, result.fun, result.nit, result.message)
```

## コラム: Krylov部分空間が拾うもの

Krylov法は、勾配とHessian作用から反復的に重要な方向を作ります。全固有vectorを求めるわけではなく、現在の右辺と曲率に関係する方向を優先的に扱います。

より単純な内部CGを使う[Trust-region Newton-CG](#/learn/trust-region-newton-cg)や、line-search型の[Newton-CG](#/learn/newton-cg)と、HVP回数・拒否step・wall timeを揃えて比較してください。