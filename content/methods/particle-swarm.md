---
content_id: particle-swarm
kind: method
method_id: M_PARTICLE_SWARM
title_ja: 粒子群最適化（PSO）
title_en: Particle Swarm Optimization
summary: 各粒子の最良経験と群全体の最良を使って速度を更新し、連続ブラックボックス空間を集団で探索する手法です。
source_ids: [S033, S040]
prerequisites: [concept.derivative-free]
related_ids: [cma-es, differential-evolution, genetic-algorithm]
aliases: [/learn/particle-swarm]
status: published
last_reviewed: 2026-09-30
---

各粒子の最良経験と群全体の最良を使って速度を更新し、連続ブラックボックス空間を集団で探索する手法です。

## 30秒でつかむ

複数の人が別々の場所を探し、自分の発見と仲間の発見を頼りに歩く場面を考えます。PSOは、各粒子が持つ二種類の経験で速度を変えます。

複数の粒子が、それぞれ異なる位置から同じ目的関数を調べます。
各粒子は「自分が見つけた最良」と「群から届いた最良」の両方へ引かれます。

- 見るもの: 現在位置、各粒子の最良経験、大域のまたは近傍最良
- 動かすもの: 各粒子の速度と位置
- 前進の判断: これまでの最良値が更新され、未探索領域も残っているか

群が一点へ集まることと、大域最適解を見つけたことは同じではありません。

## 一手の意味

### 仕組み

粒子 $i$ の位置 $x_i$ と速度 $v_i$ を、概ね

$$
v_i \leftarrow \omega v_i
+c_1r_1(p_i-x_i)
+c_2r_2(g-x_i)
$$

$$
x_i \leftarrow x_i+v_i
$$

で更新します。

- $p_i$: その粒子が見つけた各粒子の最良経験
- $g$: 群または近傍の最良
- $\omega$: 慣性係数
- $c_1,c_2$: 自分と群への引力

探索と収束のバランスは係数だけでは決まりません。
情報共有の構造、速度の上下限制限、上下限の処理にも依存します。

## 小さな例

Python節と同じ2次元Rastrigin関数、30粒子、乱数種5を使います。
最初の3回を実行して、最良値と群の広がりを記録しました。

| 更新 | これまでの最良値 | 位置の多様性 |
|---|---:|---:|
| 1 | 4.804631 | 3.206575 |
| 2 | 4.804631 | 1.945541 |
| 3 | 2.671399 | 1.117826 |

最良値は過去の記録なので悪化しません。
群の広がりは現在位置から測るため、別の動きをします。

## 向く条件・避ける条件

### まず確認すること

| 項目 | 確認内容 |
|---|---|
| 領域 | 上下限つき連続変数として表せるか |
| 尺度 | 変数ごとの範囲と意味を揃えられるか |
| 評価 | 粒子を並列評価できるか |
| 予算 | 粒子数×反復数を許容できるか |
| 制約 | 修復、罰則、可行性を優先するなどの扱いを決めたか |
| 情報共有の構造 | 群全体の最良点か局所近傍か |
| 再現性 | 複数の乱数種で結果分散を確認できるか |

向きやすい条件:

- 上下限つき連続ブラックボックス
- 勾配を得にくい
- 評価を並列化できる
- 中程度の次元
- 複数の大域の候補を探索したい

避ける条件:

- 1評価が極端に高価で群を維持できない
- 離散的な表現で速度の意味が薄れる
- 最適性ギャップや証明が必要
- 強い制約があり、ほとんどの粒子が実行不能になる
- 高次元で粒子数を十分に確保できない

## Python

図と同じ固定実行を、標準ライブラリだけで再現します。

```python
import math
import random
import statistics


def objective(point):
    return 20.0 + sum(
        x * x - 10.0 * math.cos(2.0 * math.pi * x)
        for x in point
    )


def diversity(positions):
    center = [
        statistics.fmean(point[dimension] for point in positions)
        for dimension in range(2)
    ]
    return math.sqrt(
        statistics.fmean(
            sum((point[d] - center[d]) ** 2 for d in range(2))
            for point in positions
        )
    )


rng = random.Random(5)
particle_count = 30
lower, upper = -5.12, 5.12
positions = [
    [rng.uniform(lower, upper), rng.uniform(lower, upper)]
    for _ in range(particle_count)
]
velocities = [[0.0, 0.0] for _ in positions]
personal_bests = [point.copy() for point in positions]
personal_values = [objective(point) for point in personal_bests]
initial_best = min(personal_values)
initial_diversity = diversity(positions)

for _ in range(40):
    best_index = min(range(particle_count), key=personal_values.__getitem__)
    global_best = personal_bests[best_index].copy()

    for particle in range(particle_count):
        for dimension in range(2):
            velocity = (
                0.65 * velocities[particle][dimension]
                + 1.4
                * rng.random()
                * (
                    personal_bests[particle][dimension]
                    - positions[particle][dimension]
                )
                + 1.4
                * rng.random()
                * (global_best[dimension] - positions[particle][dimension])
            )
            velocities[particle][dimension] = max(-1.5, min(1.5, velocity))
            positions[particle][dimension] = max(
                lower,
                min(
                    upper,
                    positions[particle][dimension]
                    + velocities[particle][dimension],
                ),
            )

        value = objective(positions[particle])
        if value < personal_values[particle]:
            personal_bests[particle] = positions[particle].copy()
            personal_values[particle] = value

best_index = min(range(particle_count), key=personal_values.__getitem__)
best = personal_bests[best_index]
print(f"best=({best[0]:.6f}, {best[1]:.6f})")
print(f"objective: {initial_best:.6f} -> {personal_values[best_index]:.8f}")
print(f"diversity: {initial_diversity:.3f} -> {diversity(positions):.3f}")
```

```text
best=(-0.000525, 0.000019)
objective: 6.090067 -> 0.00005485
diversity: 4.625 -> 0.213
```

この例は全粒子が同じ最良を見る群全体の最良点を共有する構造です。
局所近傍情報共有の構造では情報伝播が遅くなり、多様性を保ちやすい場合があります。

## 診断値

- 目的: 群全体の最良点、現在の中央値、乱数種間分散
- 集団: 位置の多様性、速度ノルム、各粒子の最良経験更新数
- 境界: 到達率、切り詰め後に停止した粒子数
- 制約: 可行な候補の割合、違反量
- 予算: 粒子数、反復数、総評価回数

- 別に確認するもの: 多様性、境界への到達、乱数種間分散、評価予算
- 恐れていること: 一つの局所解への早期集中

## 失敗・切替の兆候

### うまくいったサインと切替サイン

切替サイン:

- 最良が止まり多様性も小さい → 再始動、局所情報共有の構造、CMA-ESを検討
- 境界への到達が多い → 尺度、速度の上下限制限、上下限の処理を見直す
- 乱数種間分散が大きい → 予算を固定して複数の乱数種比較
- 1評価が高価 → Bayesian Optimizationや予測モデルを使う探索を検討
- 勾配が安定して使える → 勾配法も比較
- 証明が必要 → 問題構造に合う厳密法へ切り替える

::: warning
PSOの「群が一点へ集まった」は収束診断の一部であり、その点が大域最適解だという証明ではありません。
:::

### 群の広がりと最良を同時に見る

次は、多峰性のある2次元Rastrigin関数を30粒子で最小化した固定実行です。
橙の粒子が現在位置、青緑の星がその時点の群全体の最良点です。

![2次元Rastrigin関数上の30粒子によるParticle Swarm Optimization実行。反復 0では粒子が全域へ広く散り、反復 5、15、40と進むにつれて原点付近へ集中する。各区画の青緑の星は群全体の最良点、淡い整数格子は周期的な谷配置の目安を示す。下段ではこれまでの最良値が6.09から5.49e-5へ下がる一方、位置の多様性は4.63から0.21へ縮小する。2系列の縦尺度は独立している。](./media/particle-swarm-execution.svg "固定2次元Rastrigin、30粒子、乱数種5、群全体の最良点を使う結合構造、40 回の反復の実行です。淡い格子は厳密な極小点ではありません。係数、結合構造、次元、制約、他乱数種での性能や大域最適性は示しません。")

反復 5では最良が改善していますが、粒子はすでに中央付近へ寄っています。
反復 40では最良は原点近傍まで下がる一方、群の広がりは初期の5%未満です。

> これまでの最良値だけなら順調に見えます。
> 多様性を重ねると、探索余力が同時に減っていることが分かります。
> この一回の成功を、PSO一般の性能順位には使えません。

### 図の読み方

- 粒子が広く散る: 広く探す動きが残っている
- 最良周辺へ一斉に集まる: 良い領域に絞る動きが強いが、早期集中も疑う
- 同じ方向へ高速で飛び続ける: 速度や尺度が不適切
- 多峰性なのに一群へ早期集中: 早期収束の可能性

## 次に読む

- 共分散で探索分布を更新する: [CMA-ES](#/learn/cma-es)
- 差分ベクトルで候補を作る: [Differential Evolution](#/learn/differential-evolution)
- 高価な評価を予測モデルで節約する: [Bayesian Optimization](#/learn/bayesian-optimization)

- [この手法を使う問題の定式化](#/formulations/PA012)：決定変数と目的を確認します。
