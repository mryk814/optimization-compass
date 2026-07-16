---
content_id: riemannian-trust-region
kind: method
method_id: M_RIEMANNIAN_TRUST_REGION
title_ja: Riemann trust-region法
title_en: Riemannian Trust-Region
summary: 接空間上に二次modelを作りtrust radiusの内側だけで最小化し、retractionで多様体上に戻す大域化された二階法です。
source_ids: [S044, S045, S071]
related_ids: [riemannian-gradient, trust-region-newton-cg, family.manifold, family.trust-region]
status: published
last_reviewed: 2026-07-16
---

接空間上に二次modelを作りtrust radiusの内側だけで最小化し、retractionで多様体上に戻す大域化された二階法です。

## Euclid版trust-regionとの対応

[Trust-region Newton-CG](#/learn/trust-region-newton-cg)は、現在点まわりの二次modelをEuclid空間上のtrust radius $\Delta_k$ の内側だけで信用し、truncated CGで近似解を求めます。Riemann trust-region法はこの考え方を多様体上へそのまま持ち込みます。二次modelを作る場となる空間が、Euclid空間ではなく現在点の接空間に置き換わる点だけが違います。接空間は局所的に平坦なので、Euclid版の部分問題の解法や採用判定の枠組みをほぼそのまま流用できます。

## 接空間上で何を解いているか

各stepでは、Riemann勾配とRiemann Hessian（接空間上の二次形式）を使って部分問題

$$
\min_{\|p\|\le \Delta_k,\, p \in T_x M} \; m_k(p)
$$

をtruncated CGで近似的に解きます。$T_xM$ は現在点$x$における接空間です。得られた候補stepをretractionで多様体上の点へ写し、実際の目的値の改善と modelが予測した改善の比 $\rho_k$ を見て採用・棄却とtrust radiusの更新を判断します。この流れはEuclid版trust-regionの判定ロジックと同じで、幾何の分だけ「二次modelを作る場所」と「stepを多様体へ戻す操作」が追加されています。

## Riemann Hessianの入手性という課題

Riemann Hessianは、Euclid Hessianを接空間へ射影し、さらに多様体の曲率に由来する補正項を加えて得られます。この補正項は多様体ごとに異なる幾何量で、Euclid Hessianをそのまま接空間へ落とすだけでは正しいRiemann Hessian-vector積になりません。多くの実務ではこの計算を手で導出せず、Pymanopt（S044）やManopt（S045）が提供する自動微分ベースのRiemann Hessian近似を利用します。

## 一次法から乗り換える理由

[Riemann勾配法](#/learn/riemannian-gradient)は実装が単純で初期の収束が速いことがありますが、局所解付近での収束が遅くなったり、鞍点付近で長く停滞したりすることがあります。Riemann trust-region法は二次情報を使うため、良い近傍では収束が速く、また負の曲率方向を検出しやすいという性質から、鞍点からの脱出にも使われます。一次法で目的値の減少が長時間止まったときに、高精度化の手段として検討する位置づけです。

## 向いている条件

- 変数が既知の多様体構造を持つ（球面、Stiefel、Grassmann、SO(3)など）
- Riemann勾配に加えてRiemann Hessianまたはそのvector積が利用できる
- Riemann勾配法が停滞し、局所解近傍での高精度化や鞍点脱出が必要
- 多様体上での頑健な大域化（trust radiusによる棄却）を使いたい

Hessian情報が得られない、または多様体構造自体が本質でない場合は、[Riemann勾配法](#/learn/riemannian-gradient)や[Riemann多様体最適化の選び分け](#/learn/family.manifold)から検討します。

## Python

多様体上のRiemann Hessianとtruncated CGを自作でnumpy/scipyだけで忠実に再現するのは無理があるため、ここでは教育用のpseudocodeで流れだけを示します。

```text
initialize x on manifold M, trust_radius Delta
loop until stopping criterion:
    grad = riemannian_gradient(x)          # tangent-space gradient at x
    if norm(grad) < grad_tolerance:
        break
    # truncated CG on the tangent-space quadratic model
    p = truncated_cg_subproblem(
        gradient=grad,
        hessian_vector_product=riemannian_hvp_at(x),
        trust_radius=Delta,
    )
    x_trial = retract(x, p)
    rho = (cost(x) - cost(x_trial)) / model_reduction(p)
    if rho > accept_threshold:
        x = x_trial
    Delta = update_trust_radius(Delta, rho)
```

`riemannian_gradient`、`riemannian_hvp_at`、`retract`は多様体ごとに異なる幾何演算です。実装は自作せず、[Pymanopt](https://pymanopt.org/)の公式referenceでtrust-region solverの利用versionに対応する説明を確認します。

## 診断値

- Riemannian gradient norm
- trust radius $\Delta_k$
- actual / predicted reduction ratio $\rho_k$
- inner truncated CG iteration数
- retraction error
- accepted / rejected step数

## 失敗・切替の兆候

- Riemann gradient検査（有限差分との一致確認）が合わない
- retraction後に多様体制約からのずれが大きい
- chart依存の特異点付近でstepの挙動が不安定になる
- trust radiusが縮み続け候補stepがほぼ採用されない
- Riemann Hessian近似の質がsolverによって大きく違う

一次法から始めたいときは[Riemann勾配法](#/learn/riemannian-gradient)、多様体手法全体の選び分けは[Riemann多様体最適化の選び分け](#/learn/family.manifold)を確認します。
