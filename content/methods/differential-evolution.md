---
content_id: differential-evolution
kind: method
method_id: M_DIFFERENTIAL_EVOLUTION
title_ja: Differential Evolution（差分進化）
title_en: Differential Evolution
summary: 個体間の差分ベクトルから候補を作り、交叉と選択で上下限付きの連続空間を探索する集団法です。
source_ids: [S006, S074]
prerequisites: [concept.derivative-free]
related_ids: [cma-es, genetic-algorithm, particle-swarm, bayesian-optimization, family.evolutionary]
aliases: [/learn/differential-evolution]
status: published
last_reviewed: 2026-10-03
---

Differential Evolution（差分進化、DE）は、集団の点どうしの差を次の移動に使う手法です。ランダムな方向を外から与えるだけでなく、**今ある点の間隔と向きから変異を作り、元の個体と比べて残す**ところが特徴です。8個体の一世代から、その計算を追います。

## 30秒でつかむ

ほかの二人の位置の差を測り、その差を三人目の位置へ足して、新しい探索候補を作るイメージです。

- 見るもの：各個体の位置と目的値
- 作るもの：差分による変異、座標ごとの交叉、試行個体
- 判断するもの：その試行個体を元の個体と置き換えるか

集団の最良値が変わらなくても、他の個体が良くなることはあります。最良値、平均値、位置の広がりを分けて見ます。

## 変異と交叉と選択

対象個体 $x_i$ と異なる3個体 $x_{r1},x_{r2},x_{r3}$ を、互いに重複しないよう選びます。DE/rand/1の変異は

$$
v_i=x_{r1}+F(x_{r2}-x_{r3})
$$

です。`rand`は基準個体をランダムに選ぶこと、`1`は差分を一組使うことを表します。

次に二項交叉（binomial crossover）で、各座標を確率 $CR$ で変異から取り、残りを対象個体から取ります。全座標を対象個体から取ることを避けるため、無作為に選んだ少なくとも1座標は必ず変異から取ります。最後に

$$
f(u_i)\le f(x_i)
$$

なら試行個体 $u_i$ へ置き換えます。ここで説明するのは制約が上下限だけの最小化問題です。一般制約がある場合には、目的値だけの比較では足りません。

## 8個体の同じ例で一世代を追う

$$
f(x_1,x_2)=(x_1-1)^2+(x_2-2)^2,\qquad x\in[-5,5]^2
$$

を使います。解析的な最小点は $(1,2)$、値は0です。初期集団を`default_rng(7)`で一様生成し、個体番号は0〜7、$F=0.5$、$CR=0.9$とします。

世代内では元の集団を固定し、置換結果は次世代用の配列へ保存します。対象個体0の更新結果を、同じ世代の個体4の変異へ混ぜない方式です。

![DE/rand/1/binの個体4の変異と置換、同じ実行の最良値と平均値の推移。差分矢印と移動先を同じ2変数空間で表示。](./media/differential-evolution-step.svg)

### 個体4を置き換える計算

対象は $x_4=(2.970694,-0.320650)$、目的値9.269055です。抽出された個体は次の3点でした。

$$
x_7=(0.045483,0.534974),\quad
x_2=(-1.998337,3.735534),\quad
x_3=(-4.947347,3.212284).
$$

したがって

$$
v_4=x_7+0.5(x_2-x_3)=(1.519987,0.796599).
$$

交叉の2乱数は約0.154461、0.267599で、どちらも0.9より小さいため、両座標を変異から取ります。$u_4=v_4$の目的値は1.718562。9.269055以下なので次世代では置き換わります。

### 境界に出た変異がそのまま候補になるとは限らない

個体0の変異は $(-6.195740,2.670179)$ と箱の外へ出ます。教材では先に`clip`して $(-5,2.670179)$ とします。しかし交叉マスクは`[False, True]`なので、第1座標は元の個体から残ります。最終候補は $(1.250955,2.670179)$ です。

この候補の値0.512118は対象の3.952307より良く、置き換わります。「変異を境界で処理すること」と「その座標が試行個体に採用されること」は別の段階です。境界処理は切り詰め以外にも方法があり、この教材の規則をすべてのDE実装へ当てはめません。

## 最良値が止まった世代で何が変わったか

| 世代 | 累積評価数 | 最良値 | 平均値 | 置換数 | 位置の広がり |
|---|---:|---:|---:|---:|---:|
| 0 | 8 | 3.057406 | 16.969049 | — | 3.592443 |
| 1 | 16 | 0.512118 | 12.640378 | 4/8 | 2.903881 |
| 2 | 24 | 0.361958 | 9.375803 | 5/8 | 2.935070 |
| 3 | 32 | 0.361958 | 5.976858 | 5/8 | 2.283061 |

位置の広がりは、集団平均 $\bar x$ からの二乗距離平均の平方根です。

$$
\sigma_{\mathrm{pop}}=\sqrt{\frac1{8}\sum_{i=0}^7\|x_i-\bar x\|^2}.
$$

世代3では最良値が同じでも5個体が置き換わり、平均値が下がりました。一方、世代2では平均値が下がっても位置の広がりは少し増えています。目的値の平均が下がることと、集団が縮むことも同一ではありません。

初期8評価と一世代8評価を数えるので、3世代で32評価です。これは固定した乱数の小例であり、DEの一般的な性能や収束速度を示す実験ではありません。

## Pythonで図と表を再現する

NumPy 2.3.5で実行しました。

```python
import numpy as np


def f(x):
    return float((x[0] - 1)**2 + (x[1] - 2)**2)


rng = np.random.default_rng(7)
population = rng.uniform(-5, 5, size=(8, 2))
values = np.array([f(x) for x in population])

for generation in range(1, 4):
    next_population, next_values = population.copy(), values.copy()
    replaced = 0
    for i in range(8):
        others = [j for j in range(8) if j != i]
        r1, r2, r3 = rng.choice(others, size=3, replace=False)
        mutant = population[r1] + 0.5 * (population[r2] - population[r3])
        mutant = np.clip(mutant, -5, 5)
        mask = rng.random(2) < 0.9
        mask[rng.integers(2)] = True
        trial = np.where(mask, mutant, population[i])
        trial_value = f(trial)
        if trial_value <= values[i]:
            next_population[i], next_values[i] = trial, trial_value
            replaced += 1
    population, values = next_population, next_values
    spread = np.sqrt(np.mean(np.sum(
        (population - population.mean(axis=0))**2, axis=1)))
    print(generation, 8 * (generation + 1),
          values.min(), values.mean(), replaced, spread)
```

このコードは変異前の点を世代内で固定する`deferred`方式です。途中の更新を次の変異へ反映する`immediate`方式では、同じ初期集団でもその後が変わります。

## SciPyを使う場合に揃える設定

同じ目的関数と8個体でのライブラリ例です。上のコードとは別実行であり、乱数の消費順などが違うため表の軌跡を再現するものではありません。

```python
from scipy.optimize import differential_evolution

initial = np.random.default_rng(7).uniform(-5, 5, size=(8, 2))
result = differential_evolution(
    f, bounds=[(-5, 5), (-5, 5)], init=initial,
    strategy="rand1bin", mutation=0.5, recombination=0.9,
    maxiter=3, polish=False, updating="deferred", workers=1, rng=7,
)
print(result.fun, result.nfev, result.success, result.message)
# SciPy 1.17.0: 0.31197476549946884, 32, False
# Maximum number of iterations has been exceeded.
```

3世代で意図的に打ち切ったため、停止基準への収束を示す`success`はFalseです。実行エラーと混同せず、停止理由と候補を読みます。

[SciPy 1.17.0の公式文書](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.optimize.differential_evolution.html)では、既定戦略は`best1bin`です。教材の`rand1bin`とは基準個体が違います。また`popsize`は通常、自由変数数に掛ける倍率で、個体数そのものではありません。上の例は8行の`init`を明示したため、集団サイズはその配列で決まります。`polish=True`なら最後の局所求解の費用・改善も含まれるので、DE部分と区別します。

## 向く条件と診断

上下限のある連続ブラックボックスで、勾配がなく、集団分の評価予算がある場合に候補です。評価が極端に高価で数十回しか呼べない場合は、初期集団だけで予算を消費しかねません。[ベイズ最適化](#/learn/bayesian-optimization)や[高価な低次元評価](#/formulations/PA014)との比較が必要です。

- 最良値が止まる：平均値、置換数、位置の広がりも確認します。
- 多様性が早期に消える：集団サイズ、戦略、$F$と評価予算を一緒に見直します。
- 境界へ張り付く：探索範囲や境界処理が問題に合うか確認します。
- 一般制約の違反が残る：目的値と制約違反を別に記録します。
- 単一乱数種だけ成功する：複数種で同じ評価予算、初期化、停止、仕上げ条件を揃えて比べます。

変数の単位は無次元化して整理します。次元が高いほど十分な探索を行う評価費用が増えるため、2変数の成功をそのまま拡張しません。

## 次に読む

- [高次元のブラックボックス最適化](#/formulations/PA015)：変数を増やしたときの評価費用
- [CMA-ES](#/learn/cma-es)：分布の平均と共分散を更新する集団法
- [進化計算の選び分け](#/learn/family.evolutionary)：集団を使う手法を条件から比べる
- [ベイズ最適化](#/learn/bayesian-optimization)：評価が高価なときの別の選択肢
