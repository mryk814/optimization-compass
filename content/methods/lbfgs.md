---
content_id: lbfgs
kind: method
method_id: M_LBFGS
title_ja: L-BFGS法
title_en: Limited-memory BFGS
summary: 直近m組の曲率更新だけを保持し、two-loop recursionで逆Hessianの作用を計算する大規模無制約向けの準Newton法です。
source_ids: [S002, S056, S057, S065]
prerequisites: [bfgs]
related_ids: [lbfgsb, bfgs, family.smooth-local]
aliases: [/learn/lbfgs]
status: published
last_reviewed: 2026-07-16
---

直近m組の曲率更新だけを保持し、two-loop recursionで逆Hessianの作用を計算する大規模無制約向けの準Newton法です。

## denseな行列を持たずに何を計算しているか

BFGSは逆Hessian近似$H_k$を$n \times n$のdense行列として更新し、保持します。変数数$n$が大きくなると、この行列だけで概ね$O(n^2)$のmemoryを使うため、大規模problemでは現実的ではありません。

L-BFGSは$H_k$を明示的に組み立てません。代わりに直近$m$回分の

- $s_k = x_{k+1} - x_k$
- $y_k = \nabla f(x_{k+1}) - \nabla f(x_k)$

だけを保存し、two-loop recursionと呼ばれる手続きで$H_k \nabla f(x_k)$という積だけを計算します。行列そのものを作らず、保存したvector対に対する内積とscalar倍の組み合わせで同じ作用を再現する点が、BFGSとの本質的な違いです。

## memoryとmの選び方

保存するvector対の数を$m$とすると、必要なmemoryは概ね$O(mn)$です。$n$が大きくても$m$を小さく保てば、denseなBFGSでは扱えない規模の問題にも適用できます。

$m$は曲率情報の解像度を決めるhyperparameterです。$m$を大きくすると、より長い履歴を使った曲率近似になり、Newton法に近い方向を作りやすくなりますが、memoryと1 iterationあたりの計算量が増えます。$m$を小さくすると軽量ですが、履歴が短い分だけ曲率情報が粗く、勾配降下法に近い挙動へ寄っていきます。多くの実装では数〜数十程度の値を初期候補にし、収束の遅さやiteration数を見ながら調整します。

## L-BFGS-Bとの関係

L-BFGSそのものは無制約最適化のアルゴリズムです。各変数に上下限$l_i \le x_i \le u_i$を課したい場合は、[L-BFGS-B](#/learn/lbfgsb)というbounds拡張を使います。scipyでは無制約のL-BFGSも含めて`method="L-BFGS-B"`として提供されており、`bounds`引数を省略すれば実質的に無制約のL-BFGSとして動作します。

## 向いている条件

| 条件 | 理由 |
|---|---|
| 変数が多い（数千〜数百万） | dense $H_k$を保持できないため |
| 目的が局所的に十分滑らか | 曲率情報を勾配差から取り出すため |
| 勾配が信頼できる | 誤った勾配は曲率近似を壊すため |
| 局所解でよい | 非凸問題で大域最適性を保証しないため |

denseなBFGSを使えるだけ変数が少ない場合は、[BFGS](#/learn/bfgs)のほうが少ないiterationで収束することがあります。L-BFGSは、memory制約が支配的なときに検討します。

## Python

```python
import numpy as np
from scipy.optimize import minimize


def objective(x: np.ndarray) -> float:
    return float(np.sum((x - np.arange(1, x.size + 1)) ** 2))


def gradient(x: np.ndarray) -> np.ndarray:
    return 2.0 * (x - np.arange(1, x.size + 1))


n = 200
result = minimize(
    objective,
    x0=np.zeros(n),
    jac=gradient,
    method="L-BFGS-B",
    options={"maxcor": 10, "gtol": 1e-8, "maxiter": 300},
)

print(result.success, result.fun, result.nit, result.nfev)
```

`maxcor`が保存するvector対の数$m$に対応します。boundsを渡していないため、この呼び出しは実質的に無制約のL-BFGSです。利用versionのoption名や既定値は[scipy.optimize.minimize](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html)の公式referenceで確認します。

## 診断値

- gradient norm
- line-search iteration数
- function / gradient evaluation数
- objective change
- memory parameter $m$（保存vector対の数）

## 失敗・切替の兆候

- gradient checkが有限差分と一致するか
- iterationを重ねても目的値が停滞していないか
- line search failureが繰り返し発生していないか
- $m$を増やしても改善しない、またはmemoryが問題になる
- 初期点によって収束先が大きく変わる

上下限を課したい場合は[L-BFGS-B](#/learn/lbfgsb)、denseな曲率近似を保持できる規模なら[BFGS](#/learn/bfgs)、滑らかな局所最適化全体の選び分けは[滑らかな局所最適化の選び分け](#/learn/family.smooth-local)で確認できます。
