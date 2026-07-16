---
content_id: basin-hopping
kind: method
method_id: M_BASIN_HOPPING
title_ja: Basin Hopping
title_en: Basin Hopping
summary: ランダムな大きな移動と局所最適化を交互に行い、一つの初期点では届きにくい複数の谷を渡り歩く確率的大域探索です。
source_ids: [S001, S002, S056]
related_ids: [family.global-search, dual-annealing, differential-evolution]
status: published
last_reviewed: 2026-07-16
---

ランダムな大きな移動と局所最適化を交互に行い、一つの初期点では届きにくい複数の谷を渡り歩く確率的大域探索です。

## 30秒でつかむ

この手法の気持ちは、**いまいる谷の底まで一度きちんと下り、その谷に満足せず、ときどき別の場所へ飛んでもう一度下り直したい**というものです。

- 見ているもの: 各local solve後の局所最小値、受理判定、best-so-far
- 動かしているもの: basin間のrandom stepと局所solverの初期点
- 前進の判断: より良いbasinを発見できたか
- 恐れていること: 同じbasinへの再訪、local solveの過剰cost、step sizeの不適合

有限budgetで大域最適性を証明する手法ではありません。複数basinを探す実用的strategyとして扱います。

## まず確認すること

| 項目 | 確認内容 |
|---|---|
| bounds / domain | random stepをどこまで許すか |
| local solver | 各basin内を安定して解けるか |
| evaluation cost | 多数のlocal solveを許容できるか |
| multimodality | 初期点ごとに異なる局所解が現れるか |
| seed | 複数runで安定性を確認できるか |
| constraints | random stepとlocal solveで実行可能性をどう保つか |

一評価が高価なら、basinを飛ぶたびにlocal solveするcostが重すぎる可能性があります。

## 仕組み

基本サイクルは次です。

1. 現在点からrandom perturbationで候補初期点を作る
2. 候補からlocal solverを実行する
3. 得られた局所最小を、改善量とtemperatureに基づき受理または棄却する
4. best-so-farを更新し、budgetまで繰り返す

悪化するbasinも一定確率で受け入れることで、局所的な閉じ込めを避けます。step size、temperature、local solver、accept testはまとめて記録します。

## 向く条件・避ける条件

向きやすい条件:

- 低〜中次元の多峰性連続問題
- local solverが比較的安価で有効
- boundsやparameterizationを妥当に設定できる
- 証明より良い候補を複数runで探したい

避ける条件:

- 高次元かつ一評価が高価
- 離散・カテゴリ変数を無理に連続摂動する
- 一般制約を無視したrandom step
- 大域certificateや再現可能な単一run結果が必要

## うまくいったサインと切替サイン

見る値:

- best-so-farとlocal minimumの分布
- accepted / rejected basin数
- 同じbasinへの再訪率
- local solveごとの評価数
- step sizeとtemperature
- seed間のsuccess率

切替サイン:

- 同じbasinばかり再訪 → step sizeやproposalを調整
- local solveがbudgetの大半を消費 → cheaper local methodか別global searchへ
- 受理率がほぼ0または1 → temperatureとscaleを見直す
- 高価評価で試行数が不足 → Bayesian Optimizationへ
- 低次元boundedで決定論的探索が欲しい → DIRECTやSHGOへ

## Python例

```python
import numpy as np
from scipy.optimize import basinhopping


def objective(x: np.ndarray) -> float:
    return float(np.sum(x**2 - 10.0 * np.cos(2.0 * np.pi * x) + 10.0))


result = basinhopping(
    objective,
    x0=np.array([2.5, -1.5]),
    niter=50,
    stepsize=0.5,
    seed=7,
    minimizer_kwargs={"method": "BFGS"},
)
print(result.x, result.fun, result.message)
```

比較では`niter`だけでなく、local solverが使ったobjective / gradient evaluationも合計します。

## コラム: landscape transformation

Basin Hoppingは、各点をそこから到達するlocal minimumへ写した「basinの地形」を探索していると考えられます。元の関数を直接random walkするのとは異なります。

[大域探索・多峰性問題の選び分け](#/learn/family.global-search)でDIRECT、SHGO、Dual Annealing、population法とのbudgetと再現性の違いを確認してください。