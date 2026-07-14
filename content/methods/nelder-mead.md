---
content_id: method.nelder-mead
kind: method
method_id: M_NELDER_MEAD
title_ja: Nelder–Mead単体法
title_en: Nelder–Mead
summary: 勾配を使わず、単体を変形しながら局所探索します。
related_ids: [concept.derivative-free]
visualization_ids: [nelder-mead-quadratic]
comparison_ids: [COMPARE_GRADIENT_FAMILY]
aliases: [/learn/method.nelder-mead]
visualization_aliases: [nelder-mead-quadratic|/theater/nelder-mead]
comparison_aliases: [COMPARE_GRADIENT_FAMILY|/compare/gradient-quadratic]
source_ids: [S001, S002]
status: published
last_reviewed: 2026-07-15
---

## 直感

勾配を使わず、単体を変形しながら局所探索します。

目的関数 $f(x)$ の値だけを比べ、$n$ 次元では $n+1$ 個の頂点を動かします。

1. 最悪点を重心の反対側へ**反射**する。
2. 改善が大きければ**膨張**し、足りなければ**収縮**する。
3. どの候補も悪ければ、最良点へ単体を**縮小**する。

### 1ステップの見方

| 表示 | 読み取ること |
| --- | --- |
| simplex | 現在比較している頂点集合 |
| candidate | 次に採用を判定する試行点 |
| objective | 現在までの最良目的関数値 |

::: warning
局所探索であり、高次元・制約付き・多峰性では万能ではありません。異なる初期単体でも確認してください。
:::

## Python

```python
from scipy.optimize import minimize

result = minimize(objective, x0=[1.0, 1.0], method="Nelder-Mead")
print(result.x, result.fun)
```

SciPyの引数と停止条件は[公式リファレンス](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-neldermead.html)で確認できます。
