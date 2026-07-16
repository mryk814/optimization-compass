---
content_id: turbo-saasbo
kind: method
method_id: M_TURBO_SAASBO
title_ja: 高次元Bayesian最適化（TuRBO / SAASBO）
title_en: TuRBO / SAASBO
summary: 標準的なGaussian-process BOが高次元で性能を落とす理由に対し、局所trust regionで探索を絞るTuRBOと、有効次元の少なさを仮定するSAASBOという2つの緩和方向をとる高次元Bayesian最適化手法群です。
source_ids: [S035, S036, S059]
prerequisites: []
related_ids: [bayesian-optimization, smac, family.expensive-black-box]
status: published
last_reviewed: 2026-07-16
---

標準的なGaussian-process BOが高次元で性能を落とす理由に対し、局所trust regionで探索を絞るTuRBOと、有効次元の少なさを仮定するSAASBOという2つの緩和方向をとる高次元Bayesian最適化手法群です。

## 高次元で標準的なGP-BOが苦しむ理由

[Bayesian Optimization](#/learn/bayesian-optimization)は、観測全体からsurrogate（多くはGaussian process）を作り、acquisitionを最大化する点を次に評価します。次元が増えると、この枠組みは複数の点で不利になります。

- search space全体を覆うsurrogateの信頼性が下がる（同じ観測数でも次元あたりの情報密度が下がるため）
- acquisition自体が高次元関数になり、その大域最適化が難しくなる
- 標準的なBOはhypercubeの境界付近にsampleが集中しやすく、中心付近の探索が薄くなりやすい

これらは「BOが原理的に使えない」ことを意味しません。global surrogateとglobal acquisition最適化という設計が、次元とともに難しくなるということです。TuRBOとSAASBOは、この難しさに対する異なる緩和策です。

## TuRBOが何をしているか

TuRBOは、探索全体を1つのglobal surrogateに任せるのではなく、現在の最良点周辺に**trust region**（box領域）を持ち、その内側だけでBOを回します。

- trust region内の観測だけでlocal surrogateとacquisitionを扱う
- 連続して改善が続けば（success）trust regionを拡大する
- 連続して改善が止まれば（failure）trust regionを縮小する
- trust regionが十分小さくなったら、その領域を放棄し新しい位置から再始動する

局所化することでsurrogateとacquisition最適化の対象領域を絞り、高次元でも扱いやすい規模に保ちます。一方で、trust regionの外側にある大域的に有望な領域を見逃す可能性は残ります。

## SAASBOが何をしているか

SAASBOは、探索空間の次元は多くても**実際に目的関数へ効く次元は少数**という仮定を、GPのkernelに直接組み込みます。各次元のlengthscale（またはその逆数）に強いsparsity-inducing prior（horseshoe priorなど）を与え、full Bayesian推論でposteriorを求めます。関係の薄い次元は事後的にlengthscaleが大きく（＝影響が小さく）推定され、有効な次元だけがsurrogateの予測に強く寄与するようになります。

TuRBOが探索領域を局所化するのに対し、SAASBOはsurrogateの構造そのものに次元選択的な仮定を入れる点が異なります。両者は排他的ではなく、局所trust regionとsparse priorを組み合わせる実装もあります。

## 向いている条件

- search spaceの形式次元は高いが、実際に効く次元が少ない、または局所探索で十分と考えられる
- 1評価が高価で、budgetが数十〜数百回程度に限られる
- 変数が主に連続で、標準的なGP-BOがacquisition最適化や境界集中で苦戦している

避ける／切り替える条件:

- 有効次元が実質的に全次元に近く、sparsityの仮定（SAASBO）が成立しない
- 大域的に離れた複数の有望領域があり、単一のtrust region（TuRBO）では取りこぼす
- 評価が安価で大量並列に実行できる → [Random Search](#/learn/random-search)や進化的手法のほうが単純な場合
- categorical / conditionalな空間が中心 → [SMAC](#/learn/smac)のようなtree-based surrogateを検討

## Python

```text
trust_region_length = initial_length
success_count = 0
failure_count = 0

for iteration in range(max_iterations):
    candidates = sample_within_box(best_point, trust_region_length)
    local_model = fit_local_surrogate(observed_x, observed_y, box=candidates.box)
    next_x = maximize_acquisition(local_model, candidates)
    next_y = evaluate_expensive_objective(next_x)

    if next_y improves_on best_observed_y:
        success_count += 1
        failure_count = 0
    else:
        success_count = 0
        failure_count += 1

    if success_count >= success_threshold:
        trust_region_length = expand(trust_region_length)
    if failure_count >= failure_threshold:
        trust_region_length = shrink(trust_region_length)

    if trust_region_length < min_length:
        best_point = restart_from_new_region()
        trust_region_length = initial_length

    record(next_x, next_y)
```

TuRBOとSAASBOの実装、および両者を組み合わせたacquisition最適化・sparse GPの具体的な挙動は、[BoTorch](https://botorch.org/)と[Ax](https://ax.dev/)の公式referenceで利用versionに対応する説明を確認します。標準的なBOの背景は[A Tutorial on Bayesian Optimization](https://arxiv.org/abs/1807.02811)で確認できます。

## 診断値

- best-so-far
- trust regionの長さ（TuRBO、拡大・縮小の推移）
- 連続success / failure回数
- 次元ごとのlengthscaleまたはinclusion probability（SAASBO、有効次元の推定）
- surrogateのcalibrationとcross-validation error
- restart回数と各restart後の改善量

## 失敗・切替の兆候

- trust regionが縮小と即restartを繰り返し、best-so-farが進まない
- SAASBOのlengthscaleがほぼ全次元で同程度になり、sparsityの仮定が支持されない
- acquisitionが依然としてtrust region内の境界付近にsampleを集中させる
- 複数の初期点・restartで到達する最良値が大きくばらつく
- surrogateのcross-validation errorが高い、またはuncertaintyが未校正

局所trust regionを使わない標準的なBOは[Bayesian Optimization](#/learn/bayesian-optimization)、categorical・条件付き空間を扱うtree-based surrogateは[SMAC](#/learn/smac)で確認できます。高価なblack-box全体の選び分けは[高価なblack-box・HPOの選び分け](#/learn/family.expensive-black-box)にまとめています。
