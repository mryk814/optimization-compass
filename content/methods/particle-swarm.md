---
content_id: particle-swarm
kind: method
method_id: M_PARTICLE_SWARM
title_ja: 粒子群最適化（PSO）
title_en: Particle Swarm Optimization
summary: 各粒子のbest経験と群全体のbestを使って速度を更新し、連続black-box空間を集団で探索する手法です。
source_ids: [S033, S040]
prerequisites: [concept.derivative-free]
related_ids: [cma-es, differential-evolution, genetic-algorithm]
aliases: [/learn/particle-swarm]
status: published
last_reviewed: 2026-07-26
---

各粒子のbest経験と群全体のbestを使って速度を更新し、連続black-box空間を集団で探索する手法です。

## 30秒でつかむ

複数の粒子が、それぞれ異なる位置から同じ目的関数を調べます。
各粒子は「自分が見つけたbest」と「群から届いたbest」の両方へ引かれます。

- 見ているもの: 現在位置、personal best、globalまたはneighborhood best
- 動かすもの: 各粒子のvelocityとposition
- 前進の判断: best-so-farが更新され、未探索領域も残っているか
- 別に確認するもの: diversity、boundary hit、seed間分散、evaluation budget
- 恐れていること: 一つの局所解への早期集中

群が一点へ集まることと、大域最適解を見つけたことは同じではありません。

## まず確認すること

| 項目 | 確認内容 |
|---|---|
| domain | bounded continuous variablesとして表せるか |
| scale | 変数ごとの範囲と意味を揃えられるか |
| evaluation | 粒子を並列評価できるか |
| budget | 粒子数×iteration数を許容できるか |
| constraints | repair、penalty、feasible-firstなどの扱いを決めたか |
| topology | global-bestかlocal neighborhoodか |
| repeatability | 複数seedで結果分散を確認できるか |

## 仕組み

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

- $p_i$: その粒子が見つけたpersonal best
- $g$: swarmまたはneighborhoodのbest
- $\omega$: inertia
- $c_1,c_2$: personal / social attraction

探索と収束のバランスは係数だけでは決まりません。
topology、velocity clamp、bound handlingにも依存します。

## 群の広がりとbestを同時に見る

次は、多峰性のある2次元Rastrigin関数を30粒子で最小化した固定実行です。
橙の粒子が現在位置、青緑の星がその時点のglobal bestです。

![2次元Rastrigin関数上の30粒子によるParticle Swarm Optimization実行。iteration 0では粒子が全域へ広く散り、iteration 5、15、40と進むにつれて原点付近へ集中する。各panelの青緑の星はglobal best、淡い整数格子は周期的なbasin配置の目安を示す。下段ではbest-so-farが6.09から5.49e-5へ下がる一方、position diversityは4.63から0.21へ縮小する。2系列の縦scaleは独立している。](./media/particle-swarm-execution.svg "固定2次元Rastrigin、30粒子、seed 5、global-best topology、40 iterationsの実行です。淡い格子は厳密な極小点ではありません。係数、topology、dimension、constraints、他seedでの性能や大域最適性は示しません。")

iteration 5ではbestが改善していますが、粒子はすでに中央付近へ寄っています。
iteration 40ではbestは原点近傍まで下がる一方、群の広がりは初期の5%未満です。

> best-so-farだけなら順調に見えます。
> diversityを重ねると、探索余力が同時に減っていることが分かります。
> この一回の成功を、PSO一般の性能rankingには使えません。

## 図の読み方

- 粒子が広く散る: explorationが残っている
- best周辺へ一斉に集まる: exploitationが強いが、早期集中も疑う
- 同じ方向へ高速で飛び続ける: velocityやscaleが不適切
- 多峰性なのに一群へ早期集中: premature convergenceの可能性

## 向く条件・避ける条件

向きやすい条件:

- bounded continuous black-box
- 勾配を得にくい
- evaluationを並列化できる
- moderate dimension
- 複数のglobal candidateを探索したい

避ける条件:

- 1評価が極端に高価でswarmを維持できない
- discrete encodingでvelocityの意味が薄れる
- 最適性gapやcertificateが必要
- 強い制約があり、ほとんどの粒子がinfeasibleになる
- 高次元で粒子数を十分に確保できない

## Python

図と同じ固定実行を、標準libraryだけで再現します。

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

この例は全粒子が同じbestを見るglobal-best topologyです。
local neighborhood topologyでは情報伝播が遅くなり、多様性を保ちやすい場合があります。

## 診断値

- objective: global best、current median、seed間分散
- population: position diversity、速度norm、personal best更新数
- boundary: hit率、clip後に停止した粒子数
- constraints: feasible fraction、violation量
- budget: 粒子数、iteration数、total evaluations

## うまくいったサインと切替サイン

切替サイン:

- bestが止まりdiversityも小さい → restart、local topology、CMA-ESを検討
- boundary hitが多い → scale、velocity clamp、bound handlingを見直す
- seed間分散が大きい → budgetを固定して複数seed比較
- 1評価が高価 → Bayesian Optimizationやsurrogate-assisted探索を検討
- 勾配が安定して使える → 勾配法も比較
- certificateが必要 → 問題構造に合う厳密法へ切り替える

::: warning
PSOの「群が一点へ集まった」は収束診断の一部であり、その点が大域最適解だという証明ではありません。
:::

## 次に読む

- covarianceで探索分布を更新する: [CMA-ES](#/learn/cma-es)
- 差分vectorで候補を作る: [Differential Evolution](#/learn/differential-evolution)
- 高価な評価をsurrogateで節約する: [Bayesian Optimization](#/learn/bayesian-optimization)
