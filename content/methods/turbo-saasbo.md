---
content_id: turbo-saasbo
kind: method
method_id: M_TURBO_SAASBO
title_ja: 高次元Bayesian最適化（TuRBO / SAASBO）
title_en: TuRBO / SAASBO
summary: 高次元では、ガウス過程（Gaussian process）を使うベイズ最適化（Bayesian Optimization, BO）は性能を落としやすくなります。TuRBOは局所的な探索領域（trust region）に絞り、SAASBOは有効次元が少ないという仮定を置くことで、この難しさを緩和します。どちらも高次元のベイズ最適化に使う手法です。
source_ids: [S035, S036, S059]
prerequisites: []
related_ids: [bayesian-optimization, smac, family.expensive-black-box]
status: published
last_reviewed: 2026-07-18
---

高次元では、ガウス過程（Gaussian process）を使うベイズ最適化（Bayesian Optimization, BO）は性能を落としやすくなります。TuRBOは局所的な探索領域（trust region）に絞り、SAASBOは有効次元が少ないという仮定を置くことで、この難しさを緩和します。どちらも高次元のベイズ最適化に使う手法です。

## 高次元で標準的なGP-BOが苦しむ理由

[Bayesian Optimization](#/learn/bayesian-optimization)では、観測全体からsurrogate（通常はGaussian process）を作り、acquisition（獲得関数）を最大化する点を次に評価します。
次元が増えると、この枠組みは複数の点で不利になります。

- 同じ観測数でも次元あたりの情報密度が下がり、search space全体を覆うsurrogateの信頼性が下がる
- acquisition自体が高次元関数になり、その大域最適化が難しくなる
- 標準的なBOではhypercubeの境界付近にsampleが集中しやすく、中心付近の探索が薄くなりやすい

BOが原理的に使えないわけではありません。
global surrogateとglobal acquisitionの最適化を組み合わせる設計が、次元とともに難しくなるということです。
TuRBOとSAASBOは、この難しさに対する異なる緩和策です。

## TuRBOが何をしているか

TuRBOは、探索全体を1つのglobal surrogateに任せません。
現在の最良点周辺に**trust region**（box領域）を持ち、その内側だけでBOを回します。

- trust region内の観測だけでlocal surrogateとacquisitionを扱う
- 連続して改善が続けば（success）trust regionを拡大する
- 連続して改善が止まれば（failure）trust regionを縮小する
- trust regionが十分小さくなったら、その領域を放棄し新しい位置から再始動する

局所化すると、surrogateとacquisition最適化の対象領域を絞れます。
高次元でも扱いやすい規模に保てます。
探索範囲は狭まります。
その代わり、trust regionの外側にある大域的に有望な領域を見逃す可能性は残ります。

## SAASBOが何をしているか

SAASBOは、探索空間の次元が多くても、**実際に目的関数へ効く次元は少数**だと仮定します。
この仮定をGPのkernelに直接組み込みます。
各次元のlengthscale（またはその逆数）に強いsparsity-inducing prior（horseshoe priorなど）を与え、full Bayesian推論でposteriorを求めます。
関係の薄い次元はlengthscaleが大きく（＝影響が小さく）推定され、有効な次元だけがsurrogateの予測に強く寄与します。

TuRBOは探索領域を局所化し、SAASBOはsurrogateの構造そのものに次元選択的な仮定を入れます。
両者は排他的ではありません。
局所trust regionとsparse priorを組み合わせる実装もあります。

## 向いている条件

- search spaceの形式次元は高いが、実際に効く次元が少ない、または局所探索で十分と考えられる
- 1評価が高価で、budgetが数十〜数百回程度に限られる
- 変数が主に連続で、標準的なGP-BOがacquisition最適化や境界集中で苦戦している

避ける／切り替える条件:

- 有効次元が実質的に全次元に近く、sparsityの仮定（SAASBO）が成立しない
- 大域的に離れた複数の有望領域があり、単一のtrust region（TuRBO）では取りこぼす
- 評価が安価で大量並列に実行できる場合は、[Random Search](#/learn/random-search)や進化的手法のほうが単純な場合がある
- カテゴリ変数や条件付きparameterが中心なら、[SMAC](#/learn/smac)のようなtree-based surrogateを検討する

## Python

次はTuRBOの核となる、局所boxとsuccess / failureに応じた長さの更新だけを取り出した最小例です。
実際の候補選択は、局所surrogateとacquisitionが担います。

```python
import numpy as np

rng = np.random.default_rng(7)
best_x = np.array([0.8, 0.2])
best_y = float(np.sum((best_x - 0.5) ** 2))
length = 0.4
successes = 0
failures = 0

for _ in range(12):
    lower = np.maximum(0.0, best_x - length / 2.0)
    upper = np.minimum(1.0, best_x + length / 2.0)
    candidate = rng.uniform(lower, upper)
    value = float(np.sum((candidate - 0.5) ** 2))
    if value < best_y:
        best_x, best_y = candidate, value
        successes, failures = successes + 1, 0
    else:
        successes, failures = 0, failures + 1
    if successes >= 2:
        length = min(1.0, 2.0 * length)
        successes = 0
    elif failures >= 3:
        length = max(0.05, length / 2.0)
        failures = 0

print("best:", best_x, best_y, "trust-region length:", length)
```

TuRBOとSAASBOの実装は、[BoTorch](https://botorch.org/)と[Ax](https://ax.dev/)の公式referenceで確認します。
両者を組み合わせたacquisition最適化やsparse GPの具体的な挙動も、利用するversionに対応する説明を参照してください。
標準的なBOの背景は[A Tutorial on Bayesian Optimization](https://arxiv.org/abs/1807.02811)で確認できます。

## 診断値

- best-so-far
- TuRBOのtrust regionの長さと、その拡大・縮小の推移
- 連続success / failure回数
- SAASBOの次元ごとのlengthscaleまたはinclusion probability（有効次元の推定）
- surrogateのcalibrationとcross-validation error
- restart回数と各restart後の改善量

## 失敗・切替の兆候

- trust regionが縮小してすぐrestartを繰り返し、best-so-farが進まない
- SAASBOのlengthscaleがほぼ全次元で同程度になり、sparsityの仮定が支持されない
- acquisitionが依然としてtrust region内の境界付近にsampleを集中させる
- 複数の初期点・restartで到達する最良値が大きくばらつく
- surrogateのcross-validation errorが高い、またはuncertaintyが未校正

局所trust regionを使わない標準的なBOは、[Bayesian Optimization](#/learn/bayesian-optimization)で確認できます。
カテゴリ変数や条件付き空間を扱うtree-based surrogateは、[SMAC](#/learn/smac)で確認できます。
高価なblack-box全体の選び分けは、[高価なblack-box・HPOの選び分け](#/learn/family.expensive-black-box)にまとめています。
