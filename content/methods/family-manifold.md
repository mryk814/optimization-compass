---
content_id: family.manifold
kind: method
method_id: MF_MANIFOLD
title_ja: Riemann多様体最適化の選び分け
title_en: Choosing a Riemannian Manifold Method
summary: 変数の制約が球面、直交行列、固定rank行列、回転群などの多様体構造そのものであるとき、Riemann勾配法とRiemann trust-region法を条件に応じて選び分けるための入口です。
source_ids: [S044, S045, S071]
related_ids: [riemannian-gradient, riemannian-trust-region, family.smooth-local]
status: published
last_reviewed: 2026-07-16
---

変数の制約が球面、直交行列、固定rank行列、回転群などの多様体構造そのものであるとき、Riemann勾配法とRiemann trust-region法を条件に応じて選び分けるための入口です。

## 30秒でつかむ

このfamilyの気持ちは、**制約を「守るべき不等式・等式の集合」としてではなく、解空間そのものの形（多様体）として扱い、常にその形の上に留まりながら一歩を作ること**です。球面上のベクトル、正規直交な行列、固定rankの行列などは、一般的な不等式・等式制約としても書けますが、そう書くと反復のたびに制約違反を修正する手間が生まれます。多様体として扱えば、接空間への射影とretractionという2つの操作だけで、常に可行な点の上を動けます。

- 見ているもの: Euclid勾配（またはHessian）、現在点における接空間、多様体上の距離や曲率
- 動かすもの: 多様体上の現在点
- 前進の判断: Riemann gradient normの低下、目的値の低下、retraction後も多様体条件を満たしていること
- 主な弱点: 多様体ごとに接空間射影とretractionの実装が必要になること、chartの特異点、初期点への依存

「多様体として解くことが常に制約付きNLPより優れている」という順位ではありません。制約が幾何構造と一致するときに得られる可行性の単純さと、幾何演算を自分で用意する実装コストを交換しています。

## まず確認すること

| 確認項目 | 選択への影響 |
|---|---|
| 制約が既知の多様体に一致するか（球面、直交行列、固定rank、回転群など） | 一致しないなら、このfamilyを第一候補にしない |
| Euclid勾配（または対応する微分情報）が得られるか | 接空間へ射影する元になるため |
| 多様体ツール（接空間射影・retraction・Riemann Hessian）がライブラリにあるか | 自作の幾何演算は誤りやすく、既存実装の利用が安全なため |
| 追加の一般制約が混ざっていないか | 多様体構造だけで表現しきれない制約がある場合は別のfamilyを検討する |
| 二階情報（Riemann Hessian）が必要な精度か | 一次法で十分か、trust-regionによる高精度化が要るかが変わる |

制約が多様体と厳密には一致せず、線形・非線形の不等式や等式が中心の場合は、[制約付きNLPの選び分け](#/learn/family.constrained-nlp)のほうが素直な入口です。多様体構造に加えて追加の一般制約が残る場合も同様に、そちらを優先候補として検討します。

## 条件付きの選び分け

| 役割 | 手法 | 優先しやすい条件 | 切り替えを考える条件 |
|---|---|---|---|
| 単純な一次法の入口 | [Riemann勾配法](#/learn/riemannian-gradient) | 多様体構造が既知で、Euclid勾配が得られ、まず動く実装を作りたい | 局所解近傍で収束が遅い、鞍点付近で長く停滞する |
| 二階情報で高精度化・鞍点脱出 | [Riemann trust-region法](#/learn/riemannian-trust-region) | Riemann Hessianまたはそのvector積が得られ、頑健な局所収束が必要 | Riemann Hessianの入手性が悪い、部分問題のコストが支配的 |
| 一般制約として解く選択肢 | [制約付きNLPの選び分け](#/learn/family.constrained-nlp) | 制約が多様体に一致しない、または追加の一般制約が中心 | 常時可行性の単純さより、既存の制約付きsolverの使いやすさを優先したいとき |

これは一般性能rankingではありません。同じproblem instance、初期点、勾配の入手経路、tolerance、budgetで比較します。

## うまくいったサインと切替サイン

うまく進んでいるときは、次の観測が揃います。

- Riemannian gradient normが一貫して小さくなる
- retraction後の点が多様体条件（norm、直交性など）からほとんどずれない
- 異なる初期点でも同程度の解へ到達する
- Riemann trust-regionではactual / predicted reduction比が安定する

切替サイン:

- Riemann gradient検査（有限差分との一致確認）が合わない → 接空間射影の実装を見直す
- retraction error が反復とともに大きくなる → retractionの定義または数値精度を見直す
- chartの特異点付近でstepが不安定になる → 別のchartまたはparameterizationを検討する
- 一次法が停滞し続ける → [Riemann trust-region法](#/learn/riemannian-trust-region)への切り替えを検討する
- 多様体構造だけでは表現できない制約が増えてきた → [制約付きNLPの選び分け](#/learn/family.constrained-nlp)を検討する

## 小さな比較の型

実装比較では、iteration数だけでなくretraction回数や評価回数も記録します。

```python
experiment = {
    "problem_instance": "same-manifold-objective",
    "manifold": "sphere",
    "initial_point_seed": 0,
    "gradient_source": "euclidean-gradient-projected",
    "objective_evaluation_budget": 500,
    "gradient_evaluation_budget": 500,
    "riemannian_gradient_tolerance": 1e-6,
    "methods": ["riemannian-gradient-descent", "riemannian-trust-region"],
}

assert experiment["objective_evaluation_budget"] > 0
```

## コラム: なぜ制約が「消える」のか

多様体最適化が可行性を単純にする理由は、変数を多様体上の点として直接表現し、更新のたびにretractionで多様体上へ戻すためです。一般制約付き最適化では、反復点が制約境界からはみ出さないように射影やbarrier項、Lagrange乗数を管理する必要がありますが、多様体表現ではその管理が「接空間からの写像」という1つの操作に集約されます。

ただしこれは制約が消えるわけではなく、制約が幾何構造として暗黙に埋め込まれているということです。多様体の選び方自体を間違えると（例えば本来は固定rankでない行列にrank制約を課すなど）、解けるはずの解が最初から排除されてしまいます。

## 次に読む

一般の滑らかな局所最適化全体を見渡すには[滑らかな局所最適化の選び分け](#/learn/family.smooth-local)へ進みます。
