---
content_id: differential-evolution
kind: method
method_id: M_DIFFERENTIAL_EVOLUTION
title_ja: Differential Evolution（差分進化）
title_en: Differential Evolution
summary: 個体間の差分vectorから候補を作り、crossoverとselectionでbounded連続空間を探索するpopulation法です。
source_ids: [S006, S074]
prerequisites: [concept.derivative-free]
related_ids: [cma-es, genetic-algorithm, particle-swarm, bayesian-optimization, family.evolutionary]
aliases: [/learn/differential-evolution]
status: published
last_reviewed: 2026-09-30
---

個体間の差分vectorから候補を作り、crossoverとselectionでbounded連続空間を探索するpopulation法です。

## 30秒でつかむ

探検隊が、山中で宝を探しています。隊員は、それぞれ自分の足元の価値しか分かりません。
新しい探索地点は、二人の隊員の位置の差から作ります。その方向と距離を、三人目の隊員の位置に足します。
新しい地点が元の隊員の位置より良ければ、その隊員はそこへ移ります。

- **見るもの**: 集団（population）の各個体の目的関数値
- **動かすもの**: 個体の位置。ほかの個体同士の差分を使って、候補を作る
- **前進の判断**: 個体ごとに、候補が現在の位置より良ければ置き換わる。集団の最良値が改善すること

探索の歩幅は、集団の広がりから自動的に決まります。集団が集まるにつれて、歩幅も小さくなります。

## 一手の意味

一世代（generation）は、集団の個体を一つずつ、対象個体（target）として順に処理します。
代表的なDE/rand/1では、対象個体 $x_i$ と異なる3個体 $x_{r1},x_{r2},x_{r3}$ を選び、変異ベクトル（mutant）を作ります。

$$
v_i=x_{r1}+F(x_{r2}-x_{r3})
$$

この式は「二つの個体の差を $F$ 倍して、三つ目の個体に足す」と読みます。
次に、交叉（crossover）で試行個体（trial）$u_i$ を作ります。交叉率 $CR$ の確率で座標ごとに変異ベクトルの値を取り、少なくとも一つの座標は必ず変異ベクトルから取ります。
最後に選択（selection）です。試行個体が対象個体と同じか、より良ければ、次の世代へ残します。

次の量が、探索の性格を変えます。

- $F$: 差分の拡大率
- $CR$: 交叉率
- 集団の大きさ（population size）
- 戦略（strategy）: 基準にする個体と、使う差分の数の選び方

## 小さな例

目的関数 $f(x_1,x_2)=(x_1-1)^2+(x_2-2)^2$ を、$[-5,5]^2$ の範囲で最小化します。最小点は $(1,2)$ です。
戦略はDE/rand/1で、集団の大きさは8です。差分の拡大率は $F=0.5$、交叉率は $CR=0.9$ とします。
乱数の seed は 7 に固定しました。初期の集団は、この範囲から一様に生成した8点です。

世代1の個体4を例に、手で追います。

- 対象個体: $x_4=(2.971,\,-0.321)$、値は $9.269$
- 選ばれた3個体: $x_7=(0.045,\,0.535)$、$x_2=(-1.998,\,3.736)$、$x_3=(-4.947,\,3.212)$
- 変異ベクトル: $x_7+0.5\,(x_2-x_3)=(1.520,\,0.797)$
- 交叉: 両方の座標が変異ベクトルから来て、試行個体は $(1.520,\,0.797)$
- 選択: 値は $1.719$ で、対象個体の $9.269$ より良いので、置き換わる

個体0では、変異ベクトルの第1座標が範囲の外に出ます。値は $-6.195$ で、この例では範囲の端 $-5$ に切り詰めました。
交叉で第1座標は元の個体から取られ、試行個体は $(1.251,\,2.670)$、値は $0.512$ です。$3.952$ より良いので、置き換わります。
範囲の外へ出た候補の扱いは、実装によって違います。

世代ごとの推移です。

| 世代 | 累積評価数 | 最良値 | 平均値 | 置き換わった個体 |
|---:|---:|---:|---:|---:|
| 0 | 8 | 3.057 | 16.969 | |
| 1 | 16 | 0.512 | 12.640 | 8個中4個 |
| 2 | 24 | 0.362 | 9.376 | 8個中5個 |
| 3 | 32 | 0.362 | 5.977 | 8個中5個 |

世代3では最良値が変わりませんが、平均値は下がっています。集団全体が最小点の方へ寄っています。
この数値は seed 固定の一例で、別の seed では変わります。評価数は、世代あたり集団の大きさの分だけ増えます。

## 向く条件・避ける条件

向く条件です。

- 上下限を持つ連続のblack-box
- 勾配が利用できない、または目的関数が不連続・多峰性
- 目的関数の評価を、集団の単位で並列にできる
- 局所法の、初期値への依存を和らげたい
- 最適性の証明ではなく、良い大域的な候補が欲しい

避ける、または切り替える条件です。

- 評価が高価で、数十回しか呼べない → 集団を維持するだけで予算を使い切ります。[ベイズ最適化](#/learn/bayesian-optimization)との比較が必要です。[高価な低次元評価（PA014）](#/formulations/PA014)を確認する
- 変数の尺度が極端に違う → 差分ベクトルが一部の座標だけを支配する。変数を無次元化する
- 次元が高い → [高次元のblack-box最適化（PA015）](#/formulations/PA015)を確認する。[CMA-ES](#/learn/cma-es)も候補

## Python

次の例は、Rastrigin関数を `scipy.optimize.differential_evolution` で解きます。

```python
import numpy as np
from scipy.optimize import differential_evolution


def rastrigin(x: np.ndarray) -> float:
    return float(10.0 * len(x) + np.sum(x * x - 10.0 * np.cos(2.0 * np.pi * x)))


result = differential_evolution(
    rastrigin,
    bounds=[(-5.12, 5.12), (-5.12, 5.12)],
    strategy="best1bin",
    popsize=12,
    maxiter=300,
    seed=7,
    polish=False,
    updating="deferred",
    workers=1,
)

print(result.success, result.x, result.fun, result.nfev)
# True [1.61029334e-09 2.82999508e-10] 0.0 2184（SciPy 1.18.1）
```

「小さな例」は、DE/rand/1を自分で書くと再現できます。上の `best1bin` とは、基準にする個体が違います。

```python
import numpy as np


def f(x: np.ndarray) -> float:
    return float((x[0] - 1.0) ** 2 + (x[1] - 2.0) ** 2)


rng = np.random.default_rng(7)
pop_size, dim, scale, crossover = 8, 2, 0.5, 0.9
population = rng.uniform(-5.0, 5.0, size=(pop_size, dim))
values = np.array([f(x) for x in population])

for generation in range(1, 4):
    next_population, next_values = population.copy(), values.copy()
    for i in range(pop_size):
        others = [j for j in range(pop_size) if j != i]
        r1, r2, r3 = rng.choice(others, size=3, replace=False)
        mutant = np.clip(population[r1] + scale * (population[r2] - population[r3]), -5.0, 5.0)
        mask = rng.random(dim) < crossover
        mask[rng.integers(dim)] = True
        trial = np.where(mask, mutant, population[i])
        trial_value = f(trial)
        if trial_value <= values[i]:
            next_population[i], next_values[i] = trial, trial_value
    population, values = next_population, next_values
    print(generation, round(values.min(), 3), round(values.mean(), 3))
# 1 0.512 12.64
# 2 0.362 9.376
# 3 0.362 5.977
```

## 診断値

最良値だけでなく、集団の広がりを一緒に見ます。

| 診断値 | 見方 | 判断 |
|---|---|---|
| 最良値 | 世代ごとに改善しているか | 改善が止まったら、停滞した世代の数を数える |
| 集団の多様性（diversity） | 個体がどれだけ散らばっているか | 早期に消えたら、集団の大きさや $F$ を見直す |
| 実行可能な個体の割合 | 制約を満たす個体の比率 | 低いなら、penaltyや上下限の扱いを見直す |
| 上下限の付近への集中 | 個体が境界へ張り付いていないか | 張り付いているなら、探索範囲か境界の扱いを見直す |
| 世代あたりの評価数 | 予算に対する世代数 | 世代数が少なすぎないか確認する |
| seed間の結果のばらつき | 結果が偶然の成功でないか | 複数のseedで比べる |
| 停滞した世代の数 | 最良値が更新されない期間 | 続くなら、停止か別手法へ |

::: warning
`polish=True` で最後に局所法を使う実装では、最終結果はDEだけの成果ではありません。集団による探索と、局所的な仕上げの評価回数を分けて記録します。
:::

## 失敗・切替の兆候

| 症状 | 考えられる原因 | 対処・切替先 |
|---|---|---|
| 集団の多様性が早期に消える | 集団が小さい、または戦略が最良個体に寄りすぎる | 集団の大きさを増やす。戦略や $F$ を見直す |
| 全個体が上下限に張り付く | 最小点が境界の外、または境界の扱いが合わない | 探索範囲を見直す |
| 評価予算に対し、世代数が少なすぎる | 集団の大きさが予算に対して大きい | 集団を小さくする。評価が高価なら[ベイズ最適化](#/learn/bayesian-optimization)と比べる |
| penaltyの設計のせいで、実行不可能な個体しか生まれない | 目的値と制約違反を混ぜた | 制約違反を別に記録する |
| 変数の尺度が極端で、差分ベクトルが一部の座標だけを支配する | 座標ごとに、差分の大きさが違う | 変数を無次元化する |
| 単一のseedの成功例を、一般性能として扱っている | seedによる偶然 | 複数のseedで、同じ評価予算で比べる |

## コラム: 比較で揃える条件

他の手法と比べるときは、次を揃えます。

- 探索の上下限
- 集団の大きさと、初期の集団
- 乱数のseed
- 目的関数の評価予算
- 制約の扱い
- 最後に局所探索で仕上げる（polishing）かどうか
- 停止条件と、停滞の条件

主な予算は、反復の回数でなく、目的関数の評価数にします。

## 次に読む

- [高次元のblack-box最適化（PA015）](#/formulations/PA015)：勾配なしで多くの変数を決めるとき、何が難しくなるか
- [CMA-ES](#/learn/cma-es)：もう一つの集団法。分布の平均と共分散を更新する
- [進化計算の選び分け](#/learn/family.evolutionary)：集団を使う手法を条件から比べる
- [ベイズ最適化](#/learn/bayesian-optimization)：評価が高価なときの、予算を節約する選択肢
