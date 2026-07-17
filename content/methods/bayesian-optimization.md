---
content_id: bayesian-optimization
kind: method
method_id: M_BAYESIAN_OPT_GP
title_ja: ベイズ最適化
title_en: Bayesian Optimization
summary: 高価なblack-box評価を節約するため、観測履歴からsurrogate modelと不確実性を更新し、獲得関数で次の評価点を選ぶ逐次最適化です。
source_ids: [S034, S035]
prerequisites: []
related_ids: [differential-evolution, cma-es]
visualization_ids: [ARTIFACT_BO_EXPLORE_NOISELESS, ARTIFACT_BO_EXPLORE_SMALL_NOISE]
comparison_ids: [COMPARE_BO_ACQUISITION_NOISE_BASELINE]
aliases: [/learn/bayesian-optimization]
visualization_aliases: []
comparison_aliases: []
status: published
last_reviewed: 2026-07-17
---

高価なblack-box評価を節約するため、観測履歴からsurrogate modelと不確実性を更新し、獲得関数で次の評価点を選ぶ逐次最適化です。

## 30秒でつかむ

この手法の気持ちは、限られた評価budgetを、既知の良い場所とまだ分からない場所へ配分することです。

- **見るもの**: 観測済みの目的関数値、surrogateの予測と不確実性、acquisition
- **動かすもの**: 次に実評価する点と、観測後のsurrogate
- **前進の判断**: 同じobjective evaluation budgetでbest-so-farが改善すること

## 一巡で何をしているか

1. 初期点で目的関数を評価する
2. 観測 $(x_i,y_i)$ からsurrogate posteriorを更新する
3. acquisitionをsearch space上で最適化する
4. 選んだ点を実際に評価する
5. budgetまたは停止条件まで繰り返す

Gaussian-process BOでは、各入力に予測平均 $\mu(x)$ と標準偏差 $\sigma(x)$ を持ちます。平均は現在の予測、不確実性は未観測領域に関するmodel上の情報不足です。

## Acquisitionの意味

代表例:

- expected improvement
- probability of improvement
- lower / upper confidence bound
- Thompson sampling
- knowledge gradient系

minimizationのlower confidence boundなら、概念的には

$$
a(x)=\mu(x)-\beta\sigma(x)
$$

が小さい点を選びます。平均が良い場所を調べる**活用**と、不確実性が大きい場所を調べる**探索**を一つのcriterionへまとめます。

::: warning
acquisitionの最良点は、目的関数の最適点だと証明された場所ではありません。「次に評価する価値が高い」とmodelが判断した候補です。
:::

## 画面の読み方

[Bayesian Optimization Theater](#/theater/bayesian-optimization/SCENARIO_BO_1D_EXPLORE_NOISELESS)では、次を混同しないようにします。

| 表示 | 意味 |
|---|---|
| observed points | 実際に高価な関数を評価した結果 |
| true objective | 教育用scenarioでだけ既知の関数 |
| surrogate mean | 現在のsurrogate modelの予測 |
| uncertainty | surrogate model上の不確実性 |
| acquisition | 次点を選ぶ基準 |
| incumbent | 観測済みのbest-so-far |
| next point | 次に実評価する候補 |

実務ではtrue objective curveは見えません。見えるのは観測とmodelだけです。

## Python: 小さな1次元surrogate loop

```python
import numpy as np


def objective(x: np.ndarray) -> np.ndarray:
    return (x - 0.25) ** 2 + 0.1 * np.sin(12.0 * x)


def rbf_kernel(left: np.ndarray, right: np.ndarray, length_scale: float) -> np.ndarray:
    squared_distance = (left[:, None] - right[None, :]) ** 2
    return np.exp(-0.5 * squared_distance / length_scale**2)


observed_x = np.array([-1.0, 0.8])
observed_y = objective(observed_x)
grid = np.linspace(-1.0, 1.0, 401)

for _ in range(12):
    kernel = rbf_kernel(observed_x, observed_x, 0.25) + 1e-6 * np.eye(len(observed_x))
    cross = rbf_kernel(grid, observed_x, 0.25)
    weights = np.linalg.solve(kernel, observed_y)
    mean = cross @ weights
    solved = np.linalg.solve(kernel, cross.T)
    variance = np.maximum(1.0 - np.sum(cross * solved.T, axis=1), 1e-12)
    acquisition = mean - 1.5 * np.sqrt(variance)

    next_x = grid[np.argmin(acquisition)]
    observed_x = np.append(observed_x, next_x)
    observed_y = np.append(observed_y, objective(np.array([next_x]))[0])

best_index = np.argmin(observed_y)
print(observed_x[best_index], observed_y[best_index])
```

これはzero-mean、fixed kernel、noiselessに近い教育例です。実務ではmean function、kernel hyperparameter、noise、numerical stability、acquisition optimizerを明示します。

## 向いている条件

- 1評価が数分〜数日かかるsimulationや実験
- evaluation数が数十〜数百程度に制限される
- 低〜中次元のsearch space
- 過去観測を次点選択へ活用したい
- gradientを直接得られない
- observation noiseや失敗をmodel化できる

## 避ける／切り替える条件

- 評価が安価で大量並列可能 → random / population searchが単純な場合
- 極端な高次元 → kernelやacquisition最適化が難しい
- conditional / categorical space → encodingやspecialized surrogateが必要
- nonstationary objective → fixed kernelが過去を誤解する
- evaluation failureを欠損として無視 → feasibility modelが必要
- model uncertaintyを実世界の安全保証と誤認

## 診断値

- best-so-far vs objective evaluation数
- surrogate predictive error
- uncertainty calibration
- acquisition value
- repeated / near-duplicate proposal
- failed trial数
- model fitting timeとacquisition optimization time
- seed / initial design間の分散

## 公平な比較

Random Search、Differential Evolution、CMA-ESなどと比較する場合は、

- 同じproblem instanceとbounds
- 同じinitial designまたはそのcost
- 同じobjective evaluation budget
- 同じnoise / failure handling
- 複数seed
- wall-clock overheadも別に記録

を揃えます。単一trajectoryの勝敗を一般的なrankingにはしません。
