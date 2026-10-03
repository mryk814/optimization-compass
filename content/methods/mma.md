---
content_id: mma
kind: method
method_id: M_MMA
title_ja: MMA
title_en: Method of Moving Asymptotes
summary: MMAは、非線形最適化を変数ごとの凸な近似問題へ分解し、移動漸近線で更新幅を制御する逐次近似手法です。
source_ids: [S100]
prerequisites: [topology-optimization, concept.constraint-class]
related_ids: [optimality-criteria-topology, simp-topology]
visualization_ids: [topology-optimization-field-evolution]
comparison_ids: [COMPARE_TOPOLOGY_OC_MMA]
aliases: [/learn/mma]
status: published
last_reviewed: 2026-09-30
---

MMAは、非線形最適化を変数ごとの凸な近似問題へ分解し、移動漸近線で更新幅を制御する逐次近似手法です。

## 30秒でつかむ

地図を一度に信じて遠くへ進まず、現在地の周囲の近似を作り直しながら設計を変えます。

- 見るもの: 目的と制約の感度、更新履歴
- 動かすもの: 設計変数と上下の漸近線
- 前進の判断: 元の問題の可行性と目的値が改善すること

## 一手の意味

上下の漸近線へ近づくほど近似値が大きくなる、逆数の項を使います。

$$
\tilde f_i(x)=r_i+\sum_j\left(\frac{p_{ij}}{U_j-x_j}+\frac{q_{ij}}{x_j-L_j}\right),\qquad p_{ij},q_{ij}\ge0
$$

係数を現在点の値と感度に合わせ、上下限と更新幅の範囲で近似問題を解きます。

### 更新問題を近似して解く

元の目的関数や制約をそのまま一度に解くのではなく、現在点の周辺で近似問題を作ります。
各変数の近似には上下の漸近線があり、反復の履歴に応じて次の更新範囲が変わります。

トポロジー最適化では、密度場の各要素が大量の設計変数になります。
MMAはこのような変数数の多い制約付き問題を、感度情報を使う逐次更新として扱います。

### OCとの違い

OCはコンプライアンス最小化と体積率の構造に強く結びついた更新則です。
MMAは近似問題を毎回組み立てるため、追加の制約や異なる目的へ拡張しやすい一方、漸近線や近似の設定を持ちます。

同じ問題で比べるときは、MMAが一般に優れていると決めつけません。
生成器／予算／初期密度／制約／フィルターを揃えます。
密度場の変化と停止状態を一緒に見ます。

MMAの「凸な近似」は、元のトポロジー最適化問題が凸になるという意味ではありません。
各反復で解く近似部分問題の形を管理し、制約違反や過大な更新を抑えながら、元の非線形問題の局所的な改善を積み重ねます。
したがって、近似問題が解けたことと、元の問題の大域最適性や製造可能性が示されたことを分けて記録します。

## 小さな例

1変数の $f(x)=(x-2)^2$ で、漸近線の間に近似を作る操作を追います。
現在点 $x_k$ の上下1に漸近線を置き、更新幅を0.5以下にします。
正負の勾配を分け、各係数に0.01を足した逆数近似を使います。

| 反復 | 漸近線 $(L,U)$ | 更新後の $x$ | 元の目的 $f(x)$ |
|---|---|---:|---:|
| 1 | $(-1,1)$ | 0.5 | 2.25 |
| 2 | $(-0.5,1.5)$ | 1.0 | 1.00 |
| 3 | $(0,2)$ | 1.5 | 0.25 |

近似の最小点は更新幅の外にあるため、3回とも更新幅の端を採ります。
これは固定幅の漸近線と制約のない逆数近似の教材です。
履歴に応じた漸近線調整や制約付き部分問題を持つ完全なMMA実装ではありません。

## 向く条件・避ける条件

感度や近似を、対象の構造に合わせて計算できるか確認します。
実際の制約と必要精度が近似の前提から外れる場合は、[制約付き連続最適化](#/learn/constrained-continuous)で表現を見直します。

## Python

小さな例の計算を再現する、実行可能な教育用コードです。

```python
from math import sqrt

x = 0.0
for iteration in range(1, 4):
    lower, upper = x - 1.0, x + 1.0
    gradient = 2.0 * (x - 2.0)
    p = max(gradient, 0.0) + 0.01
    q = max(-gradient, 0.0) + 0.01
    stationary = (sqrt(q) * upper + sqrt(p) * lower) / (sqrt(p) + sqrt(q))
    candidate = max(x - 0.5, min(x + 0.5, stationary))
    print(iteration, lower, upper, candidate, (candidate - 2.0) ** 2)
    x = candidate
```

### 実装で受け渡す情報

```text
approximation = build_convex_subproblem(design, gradient, asymptotes)
candidate = solve_subproblem(approximation)
asymptotes = update_asymptotes(asymptotes, design, candidate)
design = enforce_volume_and_bounds(candidate)
```

## 診断値

`compliance`と`volume_fraction`を保存します。
近似問題の更新幅とその上限に加え、中間密度率と交互模様の指標も保存します。
近似問題が元の問題をどの程度表しているかは、反復ごとの値で確認します。

## 失敗・切替の兆候

更新が振動する、または体積率を守っても荷重経路が安定しない場合は、漸近線と更新幅の上限を点検します。
近似問題の設定に結果が強く依存する場合も同様です。
構造が単純なコンプライアンス最小化に戻るなら、OCとの比較を残して選び分けます。

## 次に読む

[OCとMMAの比較](#/compare/COMPARE_TOPOLOGY_OC_MMA)で同じ密度場を読み、[SIMP密度法](#/learn/simp-topology)で感度がどこから来るかを確認します。

- 問題の形を確認する: [PDE制約付き最適化](#/formulations/PA045)
