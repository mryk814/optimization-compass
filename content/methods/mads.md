---
content_id: mads
kind: method
method_id: M_MADS
title_ja: Mesh Adaptive Direct Search（MADS）
title_en: Mesh Adaptive Direct Search
summary: 格子上の近傍調査方向を適応させ、微分を使わずにブラックボックス目的と制約の局所停留点を探す直接探索法です。
source_ids: [S031, S060, S094]
prerequisites: [concept.derivative-free]
related_ids: [method.nelder-mead, differential-evolution]
aliases: [/learn/mads]
visualization_ids: [failed-simulation-feasible-ledger, failed-simulation-failure-ledger]
comparison_ids: [COMPARE_FAILED_SIMULATION_STATUS_LEDGER]
status: published
last_reviewed: 2026-09-30
---

格子上の近傍調査方向を適応させ、微分を使わずにブラックボックス目的と制約の局所停留点を探す直接探索法です。

## 30秒でつかむ

地面の升目をたどり、足元に良い場所がなければ升目を細かくする感覚です。

現在の採用点の周囲を設計空間の格子上で確かめ、改善できなければ格子を細かくします。

- **見るもの**: 近傍調査候補の目的関数値、制約違反、評価成否
- **動かすもの**: 現在の採用点、格子の間隔、近傍を調べる方向
- **前進の判断**: 制約処理の規則に従い、制約違反を減らすか、同等の可行性で`incumbent objective`を改善すること

## 一手の意味

現在の採用点 $x_k$ から、格子間隔 $\Delta_k$ と方向 $d$ で候補を作ります。

$$
y=x_k+\Delta_k d.
$$

候補を採用するかは、目的値だけでなく制約違反と評価成否で判断します。

### 探索と近傍調査

MADSは候補点を評価する処理を大きく二つに分けます。

- **探索段階**: 代理モデル、経験則、履歴などを使って任意の有限個の候補を試す
- **近傍調査段階**: 現在の採用点近傍で、理論条件を満たす方向集合を評価する

改善点が見つかれば格子を維持または拡大し、見つからなければ格子の間隔を縮小します。探索は性能改善に使えますが、局所収束理論の中心は近傍調査です。

### Nelder–Meadとの違い

どちらも勾配を使わない局所法です。
MADSは単体配置ではなく、`mesh`と`poll directions`を管理します。
ブラックボックス制約・評価失敗・非滑らかさを扱う実装もあります。

| 観点 | MADS | Nelder–Mead |
|---|---|---|
| 状態 | 格子、近傍を調べる方向、現在の採用点 | 単体頂点 |
| 制約 | progressive barrier等の変種 | 標準形は一般制約を標準の形でに扱わない |
| 診断 | 格子の間隔、近傍調査 成功、制約違反 | 単体 直径、操作 |
| 理論 | 仮定下のClarke 停留性型 | 一般多次元では限定的 |

## 小さな例

1変数 $f(x)=(x-1)^2$ を、初期点0から調べます。
近傍の2点 $x+\Delta$ と $x-\Delta$ を評価する骨格を実行しました。
改善時に格子間隔を2倍、改善がなければ半分にします。

| 調査 | 間隔 $\Delta$ | 候補 | 採用点 | 目的値 | 改善 |
|---|---:|---|---:|---:|---|
| 1回目 | 1.0 | $1,-1$ | 1 | 0 | あり |
| 2回目 | 2.0 | $3,-1$ | 1 | 0 | なし |
| 3回目 | 1.0 | $2,0$ | 1 | 0 | なし |

最良点が変わらなくても、格子の間隔は変わります。
近傍を調べて改善がないと分かれば、次は狭い範囲を調べます。
これは1変数の状態遷移を示す例です。
MADSの方向集合の条件や制約処理をすべて実装した例ではありません。

## 向く条件・避ける条件

### 向いている条件

- 低〜中次元のブラックボックス
- `gradient`がない、信用できない、またはシミュレーションが分岐する
- ブラックボックス制約や評価失敗がある
- 局所改善と停留性の目安が欲しい
- 並列 近傍調査を利用できる

### 避ける／切り替える条件

- 高次元で近傍調査点数が予算を圧迫
- 1評価が高価で代理モデル利用が必要
- 雑音の大きさより格子を細かくしても意味がない
- 大域最適解や厳密最適性の差が必要
- 離散 / カテゴリ変数を無理に連続格子へ埋め込む
- 変数 尺度合わせが悪く一部方向だけ変化する

::: note
停止時の格子が小さいことは、大域最適性の証明ではありません。
初期点／評価予算／制約処理／雑音の水準を併記します。
:::

## Python

次は状態遷移を示す実行可能な骨格です。

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

実際のMADSでは、方向集合の密に広がる性質／`mesh`と`poll size`の関係／barrier rule／最初の改善で打ち切る 評価を実装が管理します。

## 診断値

- 目的関数評価数
- 可行 / 不可行 評価数
- 現在の採用点 目的関数
- 制約違反
- 格子の間隔 / 近傍調査の半径
- 成功した 近傍調査率
- 失敗した 評価数
- 記憶済み評価の再利用
- 停止理由

## 失敗・切替の兆候

格子を細かくしても評価の雑音が改善量を上回る場合は、反復評価を検討します。
方向数が評価予算を圧迫する場合は、次元と代理モデルの利用を見直します。



[全評価が成功するTrace](#/traces/failed-simulation-feasible-ledger)と[非物理的な評価を含むTrace](#/traces/failed-simulation-failure-ledger)は、同じ候補列を使います。
変えるのは第5候補の状態区分だけです。
[失敗の状態区分を比べる](#/compare/COMPARE_FAILED_SIMULATION_STATUS_LEDGER)ときは、評価不能を大きい目的値へ置換しません。
状態区分・可行 率・成功した値だけからのbestを別々に読みます。

これはMADS／シミュレーション 実行環境／回復方策／実設計品質のベンチマークではありません。
失敗した 評価を「悪いが評価できた点」と誤認しないための固定教材です。

## 次に読む

- [制約付きの微分なし問題](#/formulations/PA014)：可行性と評価値
- [Pattern 探索](#/learn/pattern-search)：近傍候補による局所探索
- [Nelder–Mead](#/learn/method.nelder-mead)：単体を使う方法
