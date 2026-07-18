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
last_reviewed: 2026-07-17
---

接空間上に二次modelを作りtrust radiusの内側だけで最小化し、retractionで多様体上に戻す大域化された二階法です。

## 30秒でつかむ

Riemann trust-region法は、接空間上の二次modelをtrust radius内で解き、retractionで多様体上へ戻す二階法です。

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

次は単位球面を多様体として、Euclid勾配を接空間へ射影し、trust radius内のstepを正規化retractionで戻す最小例です。完全なtrust-region法ではHessianとtruncated CGも使います。

```python
import numpy as np

matrix = np.diag([1.0, 2.0, 4.0])
x = np.array([1.0, 1.0, 1.0])
x /= np.linalg.norm(x)
trust_radius = 0.25

for _ in range(30):
    euclid_gradient = 2.0 * matrix @ x
    tangent_gradient = euclid_gradient - x * (x @ euclid_gradient)
    norm = np.linalg.norm(tangent_gradient)
    if norm < 1e-8:
        break
    step = -min(trust_radius, norm) * tangent_gradient / norm
    trial = x + step
    trial /= np.linalg.norm(trial)  # sphereへのretraction
    if trial @ matrix @ trial < x @ matrix @ x:
        x = trial

print("point:", x, "cost:", x @ matrix @ x)
```

gradient、Hessian-vector product、retractionは多様体ごとに異なる幾何演算です。実務では[Pymanopt](https://pymanopt.org/)の公式referenceでtrust-region solverの利用versionに対応する説明を確認します。

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

## 次に読む

一次法から始めたいときは[Riemann勾配法](#/learn/riemannian-gradient)、多様体手法全体の選び分けは[Riemann多様体最適化の選び分け](#/learn/family.manifold)を確認します。
