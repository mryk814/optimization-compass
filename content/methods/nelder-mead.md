---
content_id: method.nelder-mead
kind: method
method_id: M_NELDER_MEAD
title_ja: Nelder–Mead単体法
title_en: Nelder–Mead
summary: 勾配を使わず、n次元でn+1頂点からなる単体を反射・膨張・収縮・縮小しながら局所的に良い点を探します。
related_ids: [concept.derivative-free, mads, differential-evolution]
visualization_ids: [nelder-mead-quadratic]
comparison_ids: [COMPARE_GRADIENT_FAMILY]
aliases: [/learn/method.nelder-mead]
visualization_aliases: [nelder-mead-quadratic|/theater/nelder-mead]
comparison_aliases: [COMPARE_GRADIENT_FAMILY|/compare/gradient-quadratic]
source_ids: [S001, S002]
status: published
last_reviewed: 2026-07-15
---

勾配を使わず、n次元でn+1頂点からなる単体を反射・膨張・収縮・縮小しながら局所的に良い点を探します。

## 単体は何を表すか

2次元では三角形、3次元では四面体がsimplexです。各頂点で目的関数を評価し、best、second-worst、worstを並べます。worst以外の頂点の重心 $c$ を基準に、worst点を反対側へ動かして候補を作ります。

代表操作:

1. **reflection**: worst点を重心の反対へ移す
2. **expansion**: reflectionが非常に良ければさらに進む
3. **outside / inside contraction**: 改善が弱ければ重心側へ縮める
4. **shrink**: 候補が悪ければbest点の周囲へ全体を縮小する

操作名が同じでも係数や停止条件は実装optionです。

## 画面の読み方

[Nelder–Mead Theater](#/theater/nelder-mead)では、次を区別します。

| 表示 | 意味 |
|---|---|
| best / worst | 現在の頂点中で最良・最悪 |
| centroid | worst以外の頂点の重心 |
| candidate | reflection等で評価する試行点 |
| simplex diameter | 探索geometryの大きさ |
| objective history | best-so-farが改善しているか |
| operation caption | 候補を採用・棄却した理由 |

単体が小さくなったことと、正しいbasinへ入ったことは別です。

## 向いている条件

- 非常に低〜低次元の連続変数
- gradientを得られない、またはgradient checkが不安定
- 一評価が比較的安価
- 無制約または単純bounds
- 高精度certificateより簡単な局所探索を優先

## Python

```python
import numpy as np
from scipy.optimize import minimize


def rosenbrock(x: np.ndarray) -> float:
    return float((1.0 - x[0]) ** 2 + 100.0 * (x[1] - x[0] ** 2) ** 2)


result = minimize(
    rosenbrock,
    x0=np.array([-1.2, 1.0]),
    method="Nelder-Mead",
    options={
        "xatol": 1e-8,
        "fatol": 1e-10,
        "maxiter": 2_000,
        "adaptive": False,
    },
)

print(result.success, result.x, result.fun, result.nfev, result.message)
```

`xatol`はgeometry、`fatol`は目的値差の停止条件です。両方が小さくても大域最適性は証明されません。

## 初期単体とscaling

初期点だけでなく、初期simplexの大きさ・方向が探索を変えます。変数scaleが大きく違うと、標準生成されたsimplexが一部座標では大きすぎ、別の座標では小さすぎる場合があります。

確認する値:

- function evaluation数
- simplex diameter / volume
- best and worst objective
- shrink回数
- repeated evaluation / duplicate vertex
- constraint violation（外部penaltyを使う場合）
- 異なる初期simplexでの解

## 失敗の兆候

- simplexが細長く退化する
- shrinkを繰り返してもbestが改善しない
- noise floor以下の差を追い続ける
- boundsへ多数の頂点がclipされ同一点になる
- 高次元で一操作あたりの評価数が重い
- 多峰性で初期点ごとに別解へ入る
- 一般制約をpenaltyだけで扱い、infeasible解を誤採用する

::: warning
Nelder–Meadは「微分不要」ですが、「評価回数が少ない」ことを意味しません。高価なblack-boxでは、評価budgetをBayesian Optimizationやsurrogate法と比較します。
:::

black-box制約やstationarityの扱いを強めたい場合は[MADS](#/learn/mads)、複数basinを集団で探したい場合は[Differential Evolution](#/learn/differential-evolution)も候補です。
