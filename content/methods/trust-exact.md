---
content_id: trust-exact
kind: method
method_id: M_TRUST_EXACT
title_ja: 厳密trust-region Newton法
title_en: Nearly Exact Trust-Region
summary: trust-region部分問題をCGで打ち切って近似するのではなく、固有値分解や行列分解に基づいてほぼ厳密に解く二階最適化法です。
source_ids: [S002, S056]
prerequisites: []
related_ids: [trust-region-newton-cg, trust-krylov, newton-method, family.trust-region]
status: published
last_reviewed: 2026-07-18
---

trust-region部分問題をCGで打ち切って近似するのではなく、固有値分解や行列分解に基づいてほぼ厳密に解く二階最適化法です。

## 30秒でつかむ

この手法の気持ちは、**trust-region部分問題を内部CGの打ち切りに任せず、dense Hessianを分解して、各stepの質を優先したい**というものです。

- 見ているもの: gradient、Hessian、trust-region部分問題の解
- 動かしているもの: trust radiusと、部分問題を解く内部反復
- 前進の判断: 実際の改善とmodel予測の一致
- 恐れていること: dense分解のcost、Hessianの誤り、問題規模の増大

外側の反復数が少なくなりやすい一方、1反復のcostは重くなります。

## 仕組み

trust-region法は各反復で局所二次modelを作り、信頼半径 $\Delta_k$ の内側だけで最小化します。

$$
\min_p\; g_k^T p + \frac{1}{2}p^T H_k p
\quad \text{subject to}\quad \lVert p\rVert \leq \Delta_k
$$

この部分問題の最適解は、ある $\lambda \geq 0$ を使って $(H_k + \lambda I)p = -g_k$ を満たし、$\lambda$ と半径境界の関係を表す secular equationを同時に満たすことが知られています。
厳密trust-region法は、$H_k$ の固有値分解や行列分解を使ってこの $\lambda$ を反復的に絞り込み、部分問題をほぼ厳密な精度で解きます。
CGのように打ち切るのではなく、1回の部分問題解法自体に複数回の内部反復を使う点が特徴です。

## CG打ち切り版との使い分け

[Trust-region Newton-CG](#/learn/trust-region-newton-cg)や[Trust-krylov](#/learn/trust-krylov)は、Hessian-vector積だけからCGやKrylov部分空間で部分問題を近似し、途中で打ち切ることで1反復あたりのcostを抑えます。
厳密trust-region法はこれと逆の設計で、dense Hessianを固有値分解できる規模を前提に、部分問題の質を優先します。

その結果、外側の反復数は少なくなりやすい一方、1反復あたりのcostは固有値分解や分解の$O(n^3)$相当のcostを含み重くなります。
dense Hessianを保持でき、中小規模の問題であれば、反復数の少なさが総costで有利になる場合があります。

## negative curvatureをどう扱うか

$H_k$ が不定で負の固有値を持つ場合、部分問題の解は負の曲率を持つ固有vector方向へ向かい、信頼半径の境界上に置かれます。
厳密trust-region法は固有値分解を通じてこの方向を正確に特定できるため、負の曲率を無視したり、CGの打ち切り位置に依存して曖昧に扱ったりすることを避けられます。
不定Hessianを含む非凸問題で、大域化の挙動を精密に制御したい場合に適しています。

## まず確認すること

向きやすい条件:

- dense Hessianを保持し固有値分解できる中小規模の問題
- Hessianとgradientをanalyticまたはautodiffでprecisionよく評価できる
- Hessianが不定になり得て、負の曲率方向を正確に扱いたい
- 反復数を減らし、各反復の部分問題品質を優先したい

避ける／切り替える条件:

- 変数数が大きくdense Hessianの保持・分解が非現実的 → [Trust-krylov](#/learn/trust-krylov)や[Trust-region Newton-CG](#/learn/trust-region-newton-cg)
- Hessianが得られない、またはnoiseに支配される → [BFGS](#/learn/bfgs)などの準Newton法
- 1反復の部分問題solveより目的評価そのものが支配的に高価

## Python

```python
import numpy as np
from scipy.optimize import minimize


def rosenbrock(x: np.ndarray) -> float:
    return float(100.0 * (x[1] - x[0] ** 2) ** 2 + (1.0 - x[0]) ** 2)


def rosenbrock_grad(x: np.ndarray) -> np.ndarray:
    dx0 = -400.0 * x[0] * (x[1] - x[0] ** 2) - 2.0 * (1.0 - x[0])
    dx1 = 200.0 * (x[1] - x[0] ** 2)
    return np.array([dx0, dx1])


def rosenbrock_hess(x: np.ndarray) -> np.ndarray:
    h00 = 1200.0 * x[0] ** 2 - 400.0 * x[1] + 2.0
    h01 = -400.0 * x[0]
    h11 = 200.0
    return np.array([[h00, h01], [h01, h11]])


result = minimize(
    rosenbrock,
    x0=np.array([-1.2, 1.0]),
    jac=rosenbrock_grad,
    hess=rosenbrock_hess,
    method="trust-exact",
    options={"gtol": 1e-8},
)
print(result.success, result.x, result.fun, result.nit)
```

`method="trust-exact"`は`hess`を必須とします。
`hess`を渡さないとSciPyはエラーで停止するため、Hessianを解析的に書けない、または安価に評価できない問題では別の手法を検討します。
利用versionに対応する挙動は[scipy.optimize.minimize](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html)の公式referenceで確認します。

## 診断値

- gradient norm
- trust radius
- actual / predicted reduction比
- rejected step数
- 部分問題内部でのlambda探索（固有値分解ベースの内部反復）の回数

## 失敗・切替の兆候

- trust radiusが縮小し続ける
- actual / predicted reduction比が改善しない
- 変数数の増加でdense Hessianの保持や分解が遅い、またはmemoryを圧迫する
- Hessianが疎・構造化されており、dense分解が本来不要なcostを払っている
- 有限差分によるgradient / Hessian checkと解析式が一致しない

## 次に読む

負の曲率をCGの打ち切り位置に依存させたくない場合はこの手法、Hessian-vector積だけで大規模問題を扱いたい場合は[Trust-region Newton-CG](#/learn/trust-region-newton-cg)や[Trust-krylov](#/learn/trust-krylov)を検討します。
Hessianを使わない探索方向の作り方は[Newton法](#/learn/newton-method)、trust-region法全体の選び分けは[信頼領域法の選び分け](#/learn/family.trust-region)で確認できます。
