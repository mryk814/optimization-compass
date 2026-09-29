---
content_id: method.gradient-descent
kind: method
method_id: M_GRADIENT_DESCENT
title_ja: 勾配降下法
title_en: Gradient Descent
summary: 現在点の勾配が示す局所的な上り方向と反対へstepを取り、滑らかな目的関数の値を反復的に下げる一次法です。
prerequisites: [concept.convexity]
related_ids: [bfgs, proximal-gradient, trust-region-newton-cg]
visualization_ids: [gradient_descent-quadratic-divergence]
comparison_ids: [COMPARE_GRADIENT_FAMILY, COMPARE_GRADIENT_DIVERGENCE]
aliases: [/learn/method.gradient-descent]
comparison_aliases: [COMPARE_GRADIENT_FAMILY|/compare/gradient-quadratic]
source_ids: [S001, S002]
status: published
last_reviewed: 2026-09-29
---

現在点の勾配が示す局所的な上り方向と反対へstepを取り、滑らかな目的関数の値を反復的に下げる一次法です。

## 30秒でつかむ

この手法の気持ちは、霧の中で山を下りる場面に似ています。見えるのは足元の傾きだけです。
いちばん急な下り方向へ一歩進み、また足元の傾きを測ります。この繰り返しが勾配降下法です。

- **見るもの**: 現在の目的関数値、勾配、試したstepの結果
- **動かすもの**: 現在点とstep size
- **前進の判断**: 目的関数値が下がり、gradient normが小さくなること

足元の傾きが正しいのは、足元の近くだけです。一歩を長く取りすぎると、下っているつもりで谷の反対側を登ります。
挙動を左右する最初の要因は、この一歩の長さ（learning rate）です。

勾配を使えることが、この手法を選ぶ出発点です。目的関数が滑らかでも、勾配のscaleや制約の扱いが合わなければ、stepは安定しません。

## 実行結果を先に見る

![同じ二次目的、初期点、40回の評価予算で実行したGradient Descent、Momentum、Adamの軌跡。Gradient Descentは細長い谷をゆっくり進み、Momentumは谷を横切って振動し、Adamは座標ごとのstepで別の経路を取る。](./media/gradient-family-execution.svg "Optimization Compassの固定Python generatorを実行した結果です。軌跡と最終目的値は同じrunから描画しています。一般的な性能rankingではありません。")

図では、勾配を下るという同じ目的でも、update ruleによって点の運び方が変わります。まず線の形を見てから、下の式と診断値へ進んでください。

## 何が必要か

| 項目 | 確認すること |
|---|---|
| variable | 連続変数であるか、projection可能な単純制約か |
| objective | 局所的に滑らかで有限値を返すか |
| gradient | analytic、automatic differentiation、検証済み数値微分のいずれかか |
| scale | 座標ごとの単位や曲率が極端に違わないか |
| goal | 局所停留点でよいか、凸性により大域解を期待できるか |

勾配を計算できることと、勾配が正しいことは別です。実装前に有限差分とのdirectional derivative checkを行います。

## 一手の意味

勾配 $\nabla f(x_k)$ は、現在点で目的関数が最も急に増える方向です。その反対へ進む更新は次の式です。

$$
x_{k+1}=x_k-\eta_k\nabla f(x_k)
$$

式は「足元の傾きを信じて、$\eta_k$ だけ進む」と言っています。
傾きは足元でしか保証されません。有限の距離を進んだ先で目的値が下がるかは、step size $\eta_k$ と、進む先までの曲率で決まります。

## 学習率を読む

いちばん単純な谷で、learning rateの効き方を計算してみます。
二次関数 $f(x,y)=(x-1)^2+\kappa(y+2)^2$ では、一手が座標ごとに独立に働きます。
最小点からのずれを $e$ と書くと、1回の更新でずれは次のように変わります。

$$
e_{k+1}=(1-\eta\lambda)\,e_k
$$

$\lambda$ はその方向の曲率で、$x$ 方向は $2$、$y$ 方向は $2\kappa$ です。倍率 $1-\eta\lambda$ が、ずれの行き先を決めます。

- 倍率の絶対値が1未満なら、ずれは縮みます。
- 倍率が負なら、最小点を飛び越えて符号が反転します。絶対値が1未満のあいだは、振動しながら縮みます。
- 倍率の絶対値が1を超えると、ずれは増え続けます。これが発散です。

すべての方向で絶対値が1未満になる条件は、最も急な方向の曲率を $L$ として $\eta<2/L$ です。$\kappa=20$ なら $L=40$ なので、限界は $\eta=0.05$ です。

細長い谷が厄介なのは、この限界が急な方向で決まるからです。急な方向に合わせて $\eta$ を小さくすると、ゆるやかな方向の倍率は $1$ に近づき、進みが遅くなります。
二つの方向の倍率を、同時に良くすることはできません。

次の図で、learning rateと谷の細長さを動かしてください。初期点はドラッグでも動かせます。

::: explorable gradient-descent-valley
橙の点が勾配降下法の軌跡です。η と κ を動かすと、二つの方向の倍率と目的関数値の推移が変わり、いまの一手の計算も同時に更新されます。二次関数を厳密な勾配で解いた教材用の実験であり、実問題で良いlearning rateを示すものではありません。
:::

図の確認手順です。まず $\kappa=5$ にして $\eta$ を上げていくと、限界の $0.2$ を超えたところで発散します。次に $\kappa=20$ へ戻すと限界は $0.05$ まで下がり、収束できる範囲でも二つの方向の倍率が大きく離れていくことが分かります。

細長い谷でzig-zagする現象は、勾配方向が最適点への直線方向とは限らないことを示します。[Gradient family comparison](#/compare/gradient-quadratic)では、MomentumやAdamと同じ初期点・budgetで確認できます。固定stepが難しい場合は、line search／schedule／preconditioningを検討します。

## 向いている条件

- smoothな連続最適化
- gradientが安価で信頼できる
- 一反復を軽くして大規模化したい
- convex問題、または局所解でよい非凸問題
- stochastic gradient変種へ移行できるmachine-learning問題

## 避ける／切り替える条件

- 離散・カテゴリ変数
- 不連続や評価失敗が頻発する
- gradient noiseがstepを支配する
- 強い一般制約を無視している
- 条件数が悪く極端に遅い → scaling、preconditioning、BFGS系を検討する
- 非滑らか正則化がある → [近接勾配法](#/learn/proximal-gradient)へ切り替える
- 曲率情報を使える → [BFGS](#/learn/bfgs)やtrust-region法を比較する

## Python

次の例は、二次関数に対してgradient descentを実行する最小例です。簡易backtrackingで、候補点の目的関数値が増えたときだけlearning rateを半分にします。

```python
import numpy as np


def objective(x: np.ndarray) -> float:
    return float((x[0] - 1.0) ** 2 + 20.0 * (x[1] + 2.0) ** 2)


def gradient(x: np.ndarray) -> np.ndarray:
    return np.array([2.0 * (x[0] - 1.0), 40.0 * (x[1] + 2.0)])


x = np.array([4.0, 3.0])
learning_rate = 0.04
for _ in range(2_000):
    g = gradient(x)
    if np.linalg.norm(g) < 1e-8:
        break
    candidate = x - learning_rate * g
    if objective(candidate) > objective(x):
        learning_rate *= 0.5
        continue
    x = candidate

print(x, objective(x), np.linalg.norm(gradient(x)))
```

この例の簡易backtrackingは教育用です。実務ではWolfe条件など、利用するline-search contractを明示します。

## 診断値

目的値の変化だけで停止すると、scaleが小さいだけの点を収束と誤認することがあります。最低限、次を記録します。

- gradient norm
- projected gradient norm（boundsがある場合）
- step norm
- objective valueとbest-so-far
- function / gradient evaluation数
- learning rate
- NaN / overflow / line-search status
- iteration / wall-clock budget

凸問題でも、停止許容値が粗ければ高精度解ではありません。
非凸問題ではgradient normが小さくても、局所解／saddle／flat regionの可能性があります。

## 失敗・切替の兆候

- 目的関数値が下がらず振動する → learning rateを下げ、scaleとline searchを確認する
- zig-zagが長く続く → scaling、preconditioning、Momentum、BFGS系を比較する
- gradient normが小さいのに目的値が改善しない → saddleやflat regionの可能性を確認する
- boundsや一般制約の違反が残る → projectionや制約対応のある手法へ切り替える

## 大きいlearning rateのfailureを見る

[勾配降下法のfailure Trace](#/theater/learning/SCENARIO_GRADIENT_DESCENT_QUADRATIC_DIVERGENCE)では、固定した二次目的でhigh learning rateの軌跡と終了statusを追えます。
[Momentum・Adamとの感度Compare](#/compare/COMPARE_GRADIENT_DIVERGENCE)は、同じ目的・初期点・40回のoracle evaluation budgetを使います。

各手法には発散を説明する固定presetを使っています。
良いparameterを探索する比較でも、手法の一般性能rankingでもありません。

::: warning
同じ反復回数でも、目的評価／gradient評価／line searchの追加評価は異なります。
手法比較ではoracle budgetと停止条件を揃えます。
:::

## 次に読む

曲率情報を使ってzig-zagを抑えたい場合は[BFGS](#/learn/bfgs)、制約や非滑らか正則化がある場合は[近接勾配法](#/learn/proximal-gradient)を参照してください。
