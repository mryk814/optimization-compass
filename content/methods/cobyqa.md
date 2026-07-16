---
content_id: cobyqa
kind: method
method_id: M_COBYQA
title_ja: COBYQA
title_en: Constrained Optimization by Quadratic Approximations
summary: 関数値と制約値から局所的な二次近似modelを育て、微分なしでboundsや一般制約を扱うtrust-region型の局所法です。
source_ids: [S002, S056]
related_ids: [family.local-dfo, cobyla, mads]
status: published
last_reviewed: 2026-07-16
---

関数値と制約値から局所的な二次近似modelを育て、微分なしでboundsや一般制約を扱うtrust-region型の局所法です。

## 30秒でつかむ

この手法の気持ちは、**勾配を直接聞けないなら、近くで試した複数点から目的関数と制約の曲がり方を推測し、そのmodelを信用できる範囲だけで次の点を選びたい**というものです。

- 見ているもの: 関数値、制約値、補間点のgeometry
- 動かしているもの: 二次model、補間集合、trust radius、候補点
- 前進の判断: model予測と実評価の一致、feasibilityと目的値の改善
- 恐れていること: 補間geometryの退化、悪いscaling、評価budget不足

COBYLAが局所線形近似を使うのに対し、COBYQAは二次近似を使うfamilyです。ただし実装optionや対応制約は必ず公式documentationで確認します。

## まず確認すること

| 項目 | 確認内容 |
|---|---|
| dimension | 補間点を維持できる低〜中次元か |
| evaluations | modelを作り直すだけのbudgetがあるか |
| constraints | bounds、線形、滑らかな非線形制約のどれか |
| noise | 二次modelを壊すほど値が揺れないか |
| scaling | 変数と制約の単位が揃っているか |
| guarantee | 局所候補でよいか、大域証明が必要か |

正確な勾配とJacobianを用意できるならSLSQPやinterior-pointも比較します。一評価が極端に高価ならsurrogate-based global searchとのbudget比較が必要です。

## 仕組み

補間点で得た値から、目的関数と制約の局所modelを作ります。候補stepはtrust region内でmodelを改善するよう選び、実評価後にmodelと半径を更新します。

重要なのは、二次式を使うこと自体より、**どの範囲でその近似を信頼するか**です。候補が予測どおり改善すれば半径を維持・拡大し、外れれば縮小します。補間点の配置が悪ければgeometry改善用の評価も必要になります。

## 向く条件・避ける条件

向きやすい条件:

- 微分を得られない低〜中次元連続問題
- boundsや一般制約がある
- 比較的滑らかで局所二次modelが役立つ
- Nelder–Meadより制約とmodel診断を重視したい

避ける条件:

- 強いnoise、不連続、頻繁な評価失敗
- 高次元で補間点数がbudgetを圧迫
- 離散・カテゴリ変数
- 大域最適性certificateが必要

## うまくいったサインと切替サイン

見る値:

- trust radius
- actual / predicted improvement
- constraint violation
- interpolation geometry
- model rebuilding回数
- objective / constraint evaluation数

切替サイン:

- 半径が縮み続ける → noise、scaling、model mismatchを確認
- geometry修復ばかりで進まない → dimensionとbudgetを見直す
- constraint violationが減らない → formulation、初期点、MADSや滑らかNLPを検討
- 評価noiseが支配的 → repeated evaluationやnoise-aware methodへ
- 多峰性で初期点依存が強い → global searchまたはmulti-startへ

## Python

```python
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, minimize


def objective(x: np.ndarray) -> float:
    return float((x[0] - 1.0) ** 2 + 2.0 * (x[1] + 0.5) ** 2)


bounds = Bounds([-2.0, -2.0], [2.0, 2.0])
constraint = LinearConstraint([[1.0, 1.0]], lb=[0.0], ub=[np.inf])
result = minimize(
    objective,
    x0=np.array([0.5, 0.5]),
    method="COBYQA",
    bounds=bounds,
    constraints=[constraint],
)
print(result.success, result.x, result.fun, result.message)
```

API対応は利用するSciPy versionで確認してください。上の例はmethodとmodelの関係を示す最小形です。

## コラム: model-based DFOの評価はどこへ使われるか

すべての評価が直接best pointを改善するとは限りません。補間geometryを整え、後続stepのmodel精度を上げる評価にも価値があります。ただし教育用の小問題で有効でも、高価な実験でそのoverheadが許されるとは限りません。

[局所Derivative-free最適化の選び分け](#/learn/family.local-dfo)でCOBYLA、MADS、Nelder–Meadとの制約・noise・budget差を確認してください。