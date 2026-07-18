---
content_id: nonlinear-cg
kind: method
method_id: M_NLCG
title_ja: 非線形共役勾配法
title_en: Nonlinear Conjugate Gradient
summary: 現在の勾配だけでなく直前までの探索方向も再利用し、少ないmemoryで大規模な滑らかな無制約問題を解く局所法です。
source_ids: [S002, S056]
related_ids: [family.smooth-local, method.gradient-descent, bfgs]
status: published
last_reviewed: 2026-07-18
---

現在の勾配だけでなく直前までの探索方向も再利用し、少ないmemoryで大規模な滑らかな無制約問題を解く局所法です。

## 30秒でつかむ

この手法の気持ちは、**毎回その場の最急降下方向へ曲がり直すのではなく、前の一歩が持っていた良い向きを少し残したい**というものです。

- 見ているもの: 目的関数値、gradient、line searchの結果
- 動かしているもの: 現在点と探索方向
- 前進の判断: 十分な目的値低下とgradient normの減少
- 恐れていること: 古い方向が役に立たなくなり、直交性や降下性を失うこと

二次関数では共役な方向を順に進む発想が基礎ですが、一般の非線形関数では方向を更新しながらline searchとrestartで安定化します。

## 仕組み

基本形は、gradient $g_k$ と直前の方向 $p_{k-1}$から新しい方向を作ります。

$$
p_k = -g_k + \beta_k p_{k-1}
$$

$\beta_k$には複数の定義があります。
実装上は、方向が降下方向でなくなった場合や一定間隔で、$p_k=-g_k$へ戻すrestartが重要です。
更新式の名前だけでなく、line search条件とrestart policyを記録します。

## まず確認すること

| 項目 | 確認内容 |
|---|---|
| 変数 | 連続で、原則として無制約か |
| oracle | 信頼できるgradientを計算できるか |
| 規模 | BFGSのdense memoryを避けたいほど大きいか |
| 滑らかさ | line searchが意味を持つ程度に滑らかか |
| 目標 | 局所停留点でよいか、大域証明が必要か |

boundsや一般制約が本質なら、変換で無理に押し込まずL-BFGS-B、projected method、制約付きNLPを検討します。

## 向く条件・避ける条件

向きやすい条件:

- 高次元の滑らかな無制約問題
- gradientは得られるがHessianやdense近似は保持したくない
- 一反復のmemoryを小さくしたい
- line searchの追加評価を許容できる

避ける条件:

- gradientがnoiseや実装ミスで不安定
- 強い不連続、離散変数、一般制約
- 一評価が極端に高価でline searchを何度も試せない
- 局所解ではなく大域最適性のcertificateが必要

## Python

```python
import numpy as np
from scipy.optimize import minimize


def objective(x: np.ndarray) -> float:
    return float((1.0 - x[0]) ** 2 + 100.0 * (x[1] - x[0] ** 2) ** 2)


def gradient(x: np.ndarray) -> np.ndarray:
    return np.array([
        -2.0 * (1.0 - x[0]) - 400.0 * x[0] * (x[1] - x[0] ** 2),
        200.0 * (x[1] - x[0] ** 2),
    ])


result = minimize(objective, x0=np.array([-1.2, 1.0]), jac=gradient, method="CG")
print(result.success, result.fun, np.linalg.norm(result.jac), result.nit)
```

## 診断値

見る値は、gradient norm、step length、line-search試行回数、方向とgradientの内積、restart回数です。

- gradient normが下がり、stepが極端に小さくならない → 継続候補
- restartがほぼ毎回起きる → 共役方向の利点が出ていない

## うまくいったサインと切替サイン

- line search failureが続く → scaling、gradient、別globalizationを確認する
- 進行は安定するが遅い → L-BFGSやtrust-regionと比較する
- 初期値ごとに別解へ入る → multi-startやglobal-search familyを検討する

## コラム: restartは失敗ではない

非線形共役勾配法では、restartによって古い方向の影響を捨てることがあります。restartの頻度は、手法が壊れたかどうかではなく、共役性を保ちにくい地形かどうかを読む診断材料です。

## 次に読む

線形共役勾配法と非線形共役勾配法は名前が近いものの、解いている対象と保証を同一視できません。
非線形版ではline searchやrestartを含むalgorithm全体が挙動を決めます。

まず[滑らかな局所最適化の選び分け](#/learn/family.smooth-local)でBFGS、L-BFGS、trust-regionとの交換条件を確認してください。
