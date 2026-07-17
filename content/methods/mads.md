---
content_id: mads
kind: method
method_id: M_MADS
title_ja: Mesh Adaptive Direct Search（MADS）
title_en: Mesh Adaptive Direct Search
summary: mesh上のpoll方向を適応させ、微分を使わずにblack-box目的と制約の局所停留点を探すdirect-search法です。
source_ids: [S031, S060, S094]
prerequisites: [concept.derivative-free]
related_ids: [method.nelder-mead, differential-evolution]
aliases: [/learn/mads]
status: published
last_reviewed: 2026-07-17
---

mesh上のpoll方向を適応させ、微分を使わずにblack-box目的と制約の局所停留点を探すdirect-search法です。

## 30秒でつかむ

この手法の気持ちは、現在のincumbentの周囲をmesh上で確かめ、改善できなければ探索の目を細かくすることです。

- **見るもの**: poll候補の目的関数値、constraint violation、評価成否
- **動かすもの**: incumbent、mesh size、poll directions
- **前進の判断**: constraint handlingの規則に従い、constraint violationを減らすか、同等のfeasibilityでincumbent objectiveを改善すること

## SearchとPoll

MADSは候補点を評価する処理を大きく二つに分けます。

- **Search step**: surrogate、heuristic、履歴などを使って任意の有限個の候補を試す
- **Poll step**: incumbent近傍で、理論条件を満たす方向集合を評価する

改善点が見つかればmeshを維持または拡大し、見つからなければmesh sizeを縮小します。Searchは性能改善に使えますが、局所収束理論の中心はPollです。

## Nelder–Meadとの違い

どちらもgradientを使わない局所法ですが、MADSは単体geometryではなくmeshとpoll directionsを管理します。black-box constraint、評価失敗、非滑らかさを扱う実装もあります。

| 観点 | MADS | Nelder–Mead |
|---|---|---|
| 状態 | mesh、poll directions、incumbent | simplex頂点 |
| 制約 | progressive barrier等の変種 | 標準形は一般制約をnativeに扱わない |
| 診断 | mesh size、poll success、constraint violation | simplex diameter、operation |
| 理論 | 仮定下のClarke stationarity型 | 一般多次元では限定的 |

## 教育用の制御loop

次はAPIではなく、状態遷移を示すsyntactically validな骨格です。

```python
from collections.abc import Callable, Iterable

Point = tuple[float, ...]


def mads_loop(
    evaluate: Callable[[Point], tuple[float, float]],
    initial: Point,
    poll_points: Callable[[Point, float], Iterable[Point]],
    minimum_mesh: float = 1e-5,
) -> Point:
    incumbent = initial
    best_value, best_violation = evaluate(incumbent)
    mesh = 1.0

    while mesh > minimum_mesh:
        improved = False
        for candidate in poll_points(incumbent, mesh):
            value, violation = evaluate(candidate)
            better = (violation, value) < (best_violation, best_value)
            if better:
                incumbent = candidate
                best_value = value
                best_violation = violation
                improved = True
                break
        mesh = mesh * 2.0 if improved else mesh * 0.5

    return incumbent
```

実際のMADSでは、方向集合のdense性、mesh / poll sizeの関係、barrier rule、opportunistic evaluationなどを実装が管理します。

## 診断値

- objective evaluation数
- feasible / infeasible evaluation数
- incumbent objective
- constraint violation
- mesh size / poll size
- successful poll率
- failed evaluation数
- cache hit
- stopping reason

## 向いている条件

- 低〜中次元のblack-box
- gradientがない、信用できない、またはsimulationが分岐する
- black-box constraintや評価失敗がある
- 局所改善とstationarityの目安が欲しい
- parallel pollを利用できる

## 避ける／切り替える条件

- 高次元でpoll点数が予算を圧迫
- 1評価が高価でsurrogate利用が必要
- noise floorよりmeshを細かくしても意味がない
- global optimumや厳密gapが必要
- discrete / categorical変数を無理に連続meshへ埋め込む
- variable scalingが悪く一部方向だけ変化する

::: note
停止時のmeshが小さいことは、大域最適性の証明ではありません。初期点、評価予算、constraint handling、noise levelを併記します。
:::
