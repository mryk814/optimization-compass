---
content_id: newton-method
kind: method
method_id: M_NEWTON
title_ja: Newton法
title_en: Newton's method
summary: 勾配とHessianから局所二次modelを作り、その停留点へ進む二階最適化法です。
source_ids: [S002, S056]
prerequisites: [method.gradient-descent, concept.convexity]
related_ids: [bfgs, lbfgsb, trust-region-newton-cg]
aliases: [/learn/newton-method]
status: published
last_reviewed: 2026-07-17
---

勾配とHessianから局所二次modelを作り、その停留点へ進む二階最適化法です。

## 30秒でつかむ

この手法の気持ちは、現在地の傾きと曲がり方から近くの地形を二次modelで描き、その停留点を狙うことです。

- **見るもの**: 目的関数値、勾配、Hessian
- **動かすもの**: 現在点とNewton step
- **前進の判断**: 目的関数値とgradient normが下がり、stepが過大にならないこと

## 仕組み

### 一手の意味

現在点 $x_k$ の近くで目的関数を二次近似すると、

$$
f(x_k+p) \approx f(x_k) + \nabla f(x_k)^T p + \frac{1}{2}p^T\nabla^2f(x_k)p
$$

です。
このmodelの停留条件からNewton step

$$
\nabla^2 f(x_k)p_k = -\nabla f(x_k)
$$

を解き、$x_{k+1}=x_k+p_k$ と更新します。

最適点の十分近くでHessianが正定値なら非常に速く収束できます。
しかし、遠い初期点、非凸領域、不定Hessianでは、そのままのstepが下り方向にならないことがあります。

## まず確認すること

| 項目 | 確認点 |
|---|---|
| gradient | analytic、automatic differentiation、検証済み数値微分か |
| Hessian | 明示行列、sparse構造、Hessian-vector積のどれか |
| linear solve | factorizationの時間とmemory |
| globalization | line searchまたはtrust regionを使うか |
| stopping | gradient norm、step norm、目的値変化 |

Hessianを作る費用だけでなく、線形方程式を解く費用も支配的になります。
大規模問題ではNewton-CGやtrust-region Krylov法のようにHessian-vector積を使う変種が有力です。

## 向いている条件・避ける条件

向いている条件:

- gradientとHessian、またはHessian-vector積を安定して計算できる
- 最適点の十分近くでHessianが正定値になる
- factorizationやlinear solveの費用を許容できる

避ける／条件付き:

- 遠い初期点、非凸領域、不定Hessianではglobalizationを加える
- factorizationが重い場合はNewton-CG、L-BFGS、sparse solverと比較する
- noiseや不連続が強い場合は二階modelの前提を再検討する

## Python

```python
import numpy as np


def gradient(x: np.ndarray) -> np.ndarray:
    return np.array([2.0 * (x[0] - 1.0), 8.0 * (x[1] + 2.0)])


def hessian(_: np.ndarray) -> np.ndarray:
    return np.array([[2.0, 0.0], [0.0, 8.0]])


x = np.array([5.0, 3.0])
for _ in range(10):
    g = gradient(x)
    if np.linalg.norm(g) < 1e-10:
        break
    step = np.linalg.solve(hessian(x), -g)
    x = x + step

print(x)
```

この例は正定値二次関数なのでfull Newton stepが安全です。
一般の非線形・非凸問題では、この短い実装だけをそのまま使わず、line searchやtrust regionを追加します。

## 診断値

- 目的関数値
- gradient norm
- Hessianの固有値
- step norm
- 目的値変化
- factorizationの時間とmemory
- 制約条件

Newton法の速い局所収束は、大域最適性の証明ではありません。
非凸問題では初期点を変え、得られた解とHessianの固有値、制約条件を確認します。

## 失敗・切替の兆候

- Hessianが不定で目的値が上がる → modified Newtonまたはtrust region
- factorizationが重い → Newton-CG、L-BFGS、sparse solver
- gradient/Hessian checkが合わない → 微分実装を修正
- stepが巨大 → scaling、damping、trust radiusを確認
- saddle point付近で停止 → second-order情報やnegative curvatureを確認
- noiseや不連続が強い → 二階modelの前提を再検討

## 次に読む

Hessianを近似する方法は[BFGS](#/learn/bfgs)、局所modelを信頼できる範囲だけで使う方法は[trust-region Newton-CG](#/learn/trust-region-newton-cg)で確認できます。
