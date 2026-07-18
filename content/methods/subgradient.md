---
content_id: subgradient
kind: method
method_id: M_SUBGRADIENT
title_ja: 劣勾配法
title_en: Subgradient Method
summary: 凸だが非微分可能な点でも利用できる劣勾配を使い、step scheduleとbest-so-farを管理して目的値を改善する一次法です。
source_ids: [S055, S056]
prerequisites: [concept.convexity, method.gradient-descent]
related_ids: [proximal-gradient, mirror-descent, fista]
aliases: [/learn/subgradient]
status: published
last_reviewed: 2026-07-18
---

凸だが非微分可能な点でも利用できる劣勾配を使い、step scheduleとbest-so-farを管理して目的値を改善する一次法です。

## 30秒でつかむ

Subgradient法は、微分できない点を避けるのではなく、凸関数を下から支えるsubgradientを一つ選んで進みます。
毎回のobjectiveが下がるとは限らないため、best-so-farとstep scheduleを主な手がかりにします。

- 見ているもの: current / best-so-far objective、subgradient、lower boundとgap
- 動かしているもの: 現在点、step schedule、必要ならprojection
- 前進の判断: best-so-farまたはgapが改善し、stepが理論上の条件に沿うこと
- 恐れていること: saw-tooth、fixed stepの振動、遅いrate、scaleの不一致

## 劣勾配とは何か

凸関数 $f$ の点 $x$ でvector $g$ が

$$
f(y)\ge f(x)+g^T(y-x)
$$

をすべての $y$ で満たすとき、$g$ はsubgradientです。滑らかな点では通常の勾配が唯一のsubgradientですが、$f(x)=|x|$ の $x=0$ では区間 $[-1,1]$ のすべてがsubgradientです。

更新は

$$
x_{k+1}=\Pi_C(x_k-\alpha_k g_k)
$$

で、必要ならconvex set $C$ へprojectionします。

## Gradient Descentとの違い

subgradient方向へ有限step進んでも、目的値が毎回下がるとは限りません。したがってcurrent objectiveだけでなくbest-so-farやergodic averageを追います。

代表的なstep schedule:

- diminishing: $\alpha_k\to0$ かつ $\sum_k\alpha_k=\infty$
- square summable: $\sum_k\alpha_k^2<\infty$
- Polyak step: optimal valueの下界が分かる場合
- fixed step: 誤差neighborhoodへ入るが厳密収束しない場合

## Python

```python
import numpy as np


def objective(x: np.ndarray) -> float:
    return float(abs(x[0] - 2.0) + 0.2 * (x[0] + 1.0) ** 2)


def subgradient(x: np.ndarray) -> np.ndarray:
    shifted = x[0] - 2.0
    absolute_part = 0.0 if shifted == 0.0 else np.sign(shifted)
    return np.array([absolute_part + 0.4 * (x[0] + 1.0)])


x = np.array([-4.0])
best_x = x.copy()
best_value = objective(x)

for iteration in range(1, 5_001):
    step = 1.0 / np.sqrt(iteration)
    x = x - step * subgradient(x)
    value = objective(x)
    if value < best_value:
        best_x = x.copy()
        best_value = value

print(best_x, best_value)
```

非滑らかな点で0を選ぶruleは一例です。oracleが返すsubgradientの選び方も再現条件に含めます。

## 最初に見る診断値

- current / best-so-far objective
- step size
- subgradient norm
- projected step norm
- running average objective
- lower boundとgap（利用可能な場合）
- constraint violation
- iteration / oracle evaluation budget

目的値がsaw-tooth状に動くこと自体は異常ではありません。best-so-farが長時間改善しない、stepが大きすぎる、またはnoise floorへ達したかを確認します。

## 向いている条件

- convexだが非滑らかな目的
- proxを計算しにくいがsubgradientは得られる
- 巨大problemで安価な一反復を優先
- exact高精度より粗い解やlower-bound progressが重要
- Lagrangian dualの更新

## 失敗・切替の兆候

- proximableな構造がある → [近接勾配法](#/learn/proximal-gradient)を比較する
- smoothで条件数が支配 → gradient / quasi-Newtonを比較する
- 非凸でsubgradient理論をそのまま適用 → 理論の適用範囲を見直す
- fixed stepの振動を収束と誤認 → best-so-far、gap、stepを確認する
- stoppingをcurrent objectiveだけで判定 → best-so-farまたはlower boundを併用する
- scaleが違う座標へ同じEuclidean step → scalingまたはparameterizationを見直す

::: warning
劣勾配法の理論rateは一般に遅く、高精度解には多数の反復が必要です。「微分不要法」ではなく、凸解析のsubgradient oracleを使う方法として位置付けます。
:::
