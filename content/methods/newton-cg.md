---
content_id: newton-cg
kind: method
method_id: M_NEWTON_CG
title_ja: Newton-CG法
title_en: Newton Conjugate Gradient
summary: Hessian全体を保持せずHessian-vector積と共役勾配法でNewton方向を近似し、滑らかな大規模問題へ二階情報を使う局所法です。
source_ids: [S002, S056]
related_ids: [family.smooth-local, newton-method, trust-region-newton-cg]
status: published
last_reviewed: 2026-07-18
---

Hessian全体を保持せずHessian-vector積と共役勾配法でNewton方向を近似し、滑らかな大規模問題へ二階情報を使う局所法です。

## 30秒でつかむ

この手法の気持ちは、**谷の傾きだけでなく曲がり方も利用したいが、巨大なHessian行列を作って保存するのは避けたい**というものです。

- 見ているもの: gradientとHessian-vector積
- 動かしているもの: Newton方向を近似する内部CG反復と現在点
- 前進の判断: line search後の目的値低下とgradient normの減少
- 恐れていること: 不定曲率、誤ったHVP、内部CGの過剰計算

Newton方程式を完全に解く代わりに、必要な精度まで方向を近似します。
外側の最適化と内側の線形solveの二重構造を持つ手法です。

## 仕組み

Newton方向は理想的には次を満たします。

$$
H(x_k)p_k = -\nabla f(x_k)
$$

Newton-CGはこの線形系をCGで近似します。
内部反復を早めに止めれば一stepは安価になりますが、方向の質が落ちます。
外側のline search、内部CG tolerance、負の曲率への対応をまとめて一つのalgorithmとして扱います。

## HVPの扱い

正確なHVPは、Hessian行列を明示的に組み立てずにその作用だけを計算する方法です。
一方、有限差分でgradient差からHVPを近似する場合はstep幅と数値誤差が追加されます。

## まず確認すること

| 項目 | 確認内容 |
|---|---|
| gradient | 正確または十分信頼できるか |
| HVP | $H(x)v$を行列を作らず計算できるか |
| 規模 | dense Hessianを保持できない大きさか |
| 曲率 | 非凸領域で負の曲率が現れるか |
| 制約 | 原則無制約か、別の制約処理が必要か |

自動微分でHVPを得られる場合も、方向微分checkを行い、gradientと同じobjectiveを微分しているか確認します。

## 向く条件・避ける条件

向きやすい条件:

- 滑らかな大規模無制約問題
- gradientとHVPを効率よく計算できる
- BFGSのdense memoryを避けつつ曲率を使いたい
- 解の近くで高精度化したい

避ける条件:

- 不連続、強いnoise、離散変数
- HVPが目的関数と不整合
- line searchの追加評価が許されない
- 一般制約や大域最適性certificateが必要

## Python

```python
import numpy as np
from scipy.optimize import minimize

A = np.array([[4.0, 1.0], [1.0, 3.0]])
b = np.array([-1.0, 2.0])


def objective(x: np.ndarray) -> float:
    return float(0.5 * x @ A @ x + b @ x)


def gradient(x: np.ndarray) -> np.ndarray:
    return A @ x + b


def hessian_product(x: np.ndarray, vector: np.ndarray) -> np.ndarray:
    del x
    return A @ vector


result = minimize(
    objective,
    x0=np.zeros(2),
    jac=gradient,
    hessp=hessian_product,
    method="Newton-CG",
)
print(result.success, result.x, result.fun, result.nit)
```

## 診断値

- gradient norm
- outer iterationとinner CG iteration
- line-search試行回数
- curvature $p^T H p$
- step normとobjective change

## 失敗・切替の兆候

- 内部CGが毎回上限まで走る → preconditioning、tolerance、L-BFGSを検討する
- 負の曲率やline-search failureが多い → trust-region Newton-CGへ切り替える
- HVP計算がobjective評価より重い → 一階法・準Newton法と比較する
- gradient checkが不一致 → algorithm変更より先に微分実装を修正する
- 解近傍で速いが初期点から不安定 → globalizing strategyを見直す

## 次に読む

非凸問題での安全性を重視するなら[Trust-region Newton-CG](#/learn/trust-region-newton-cg)、memoryをさらに単純化するなら[非線形共役勾配法](#/learn/nonlinear-cg)も比較してください。
