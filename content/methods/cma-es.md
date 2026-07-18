---
content_id: cma-es
kind: method
method_id: M_CMA_ES
title_ja: CMA-ES
title_en: Covariance Matrix Adaptation Evolution Strategy
summary: 関数値の順位から探索分布の平均・global step size・共分散を更新し、連続black-boxの有望な方向とscaleを学ぶpopulation法です。
source_ids: [S032, S058]
prerequisites: [concept.derivative-free]
related_ids: [concept.derivative-free, multi-objective, differential-evolution, particle-swarm]
visualization_ids: []
comparison_ids: []
aliases: [/learn/cma-es]
visualization_aliases: []
comparison_aliases: []
status: published
last_reviewed: 2026-07-18
---

関数値の順位から探索分布の平均・global step size・共分散を更新し、連続black-boxの有望な方向とscaleを学ぶpopulation法です。

## 点ではなく分布を更新する

CMA-ESは概念的に

$$
x_i \sim \mathcal{N}(m,\sigma^2 C)
$$

からpopulationをsampleし、目的値の良い個体を使って、

- mean $m$
- step size $\sigma$
- covariance $C$

を更新します。$C$が変数間の相関と探索ellipseの向きを、$\sigma$が全体の探索scaleを表します。

function valueの絶対差よりrankingを主に使うため、単調変換に比較的頑健です。ただし、constraint、noise、failure、boundsの扱いは別途必要です。

## 可視化で見るもの

2Dでは、

- population points
- selected elite
- mean
- covariance ellipse
- step-size history
- best-so-far
- population diversity

を同期すると、地形の谷に合わせてellipseが回転・伸縮する様子を読めます。ellipseが小さくなったことは大域最適性の証明ではありません。

## 初期sigmaの意味

- 小さすぎる: 初期mean近傍だけを局所探索しやすい
- 大きすぎる: boundsやinvalid領域へ多数sampleしやすい
- variable scaleが違う: 単一sigmaでは一部座標に不適切

変数を無次元化する、初期covarianceを設計する、bounds handlingを確認することが重要です。

## Constraint handling

代表的な方法:

- penalty
- repair / projection
- rejection / resampling
- feasibility ranking
- augmented Lagrangian variant
- constrained transformation

penaltyで低目的値のinfeasible点を誤ってbestにしないよう、objectiveとconstraint violationを別に記録します。

## Noiseとrestart

noiseによりrankingが入れ替わる場合、

- resampling
- repeated evaluation
- larger population
- noise handling option
- uncertainty-aware stopping

を検討します。multimodal problemではIPOP / BIPOPなどrestart strategyがありますが、総evaluation budgetを分割して報告します。

## 向いている条件

- 連続・非凸・black-box
- 勾配がない、信用できない、または不連続がある
- moderate dimension
- population evaluationを並列化できる
- 局所的な勾配法の初期値依存を緩和したい
- 最適性certificateより良いcandidateが必要

## Alternative-first

- 勾配が信頼できる → BFGS / L-BFGS-B
- 残差Jacobianがある → nonlinear least squares
- 1評価が極端に高価 → Bayesian Optimization
- 離散・論理変数 → CP-SAT / MIP / GA encoding
- low-dimensional local DFO → Nelder–Mead / MADS

## Python

```python
import cma


def rosenbrock(x: list[float]) -> float:
    return (1.0 - x[0]) ** 2 + 100.0 * (x[1] - x[0] ** 2) ** 2


options = {
    "seed": 7,
    "bounds": [[-3.0, -3.0], [3.0, 3.0]],
    "maxfevals": 2_000,
    "verb_disp": 0,
}
result = cma.fmin(
    rosenbrock,
    x0=[-1.2, 1.0],
    sigma0=0.6,
    options=options,
)

print(result[0], result[1], result[2])
```

`x0`、`sigma0`、bounds、seed、population size、restartを再現条件として保存します。`fmin`の返却構造やoptionは実装versionの公式documentationで確認します。

## 診断値

- best / median objective
- mean trajectory
- sigma
- covariance eigenvalues / condition number
- population diversity
- feasible fraction
- invalid evaluation数
- restart count
- evaluation budget
- seed間の結果分散

## 失敗・切替の兆候

- sigmaが早期に極小化
- covariance condition numberが巨大化
- populationが同一basinへcollapse
- bounds / failure regionでsampleを浪費
- 高次元でcovariance更新・population評価が重い
- penaltyによりfeasible解が生成されない
- 一回の成功runだけで性能を判断

::: warning
CMA-ESはglobal candidate探索として有力ですが、有限budgetで大域最適性を証明する手法ではありません。複数seed、同じevaluation budget、同じboundsで比較します。
:::
