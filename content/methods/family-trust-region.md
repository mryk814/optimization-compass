---
content_id: family.trust-region
kind: method
method_id: MF_TRUST_REGION
title_ja: 信頼領域法の選び分け
title_en: Choosing a Trust-Region Method
summary: 局所二次modelを信頼できる半径の中だけで最小化し、実測改善と予測改善の比で半径を更新するtrust-region法群を条件に応じて選び分けるための入口です。
source_ids: [S002, S003, S056]
prerequisites: []
related_ids: [trust-region-newton-cg, trust-krylov, gauss-newton, least-squares, trust-region-reflective, family.smooth-local]
status: published
last_reviewed: 2026-07-16
---

局所二次modelを信頼できる半径の中だけで最小化し、実測改善と予測改善の比で半径を更新するtrust-region法群を条件に応じて選び分けるための入口です。

## 30秒でつかむ

このfamilyの気持ちは、**「今の二次modelをどこまで信じてよいか」を半径として管理し、信頼できる範囲の中だけで一歩を決めること**です。line searchが方向を先に決めてから歩幅を調整するのに対し、trust-region法は先に「この範囲までなら信じる」という半径を決め、その中で部分問題を解いて一歩を作ります。

- 見ているもの: 目的関数値、勾配、局所二次modelの予測改善量、実際の改善量
- 動かすもの: 現在点と信頼半径
- 前進の判断: actual reduction（実測改善）とpredicted reduction（modelの予測改善）の比が十分大きいこと
- 主な弱点: 部分問題を解く精度と微分情報の品質に依存する、実装が複雑になりやすい

「trust-regionが常にline searchより優れている」という順位ではありません。負の曲率への対処や大域化の安定性と、部分問題を解く追加コストを交換しています。

## まず確認すること

| 確認項目 | 選択への影響 |
|---|---|
| 勾配・Jacobian・Hessian-vector積のどれが得られるか | 部分問題の解き方（CG打ち切り、Krylov、厳密分解）が変わる |
| 目的が一般の非線形関数か、残差の二乗和か | 一般関数ならNewton系、残差構造があるならGauss–Newton/Levenberg–Marquardt系 |
| bounds制約の有無 | Trust-region reflectiveのように境界を反映したtrust-regionが必要か |
| 変数数とHessianの扱えるscale | dense分解が可能か、Hessian-vector積だけを使うKrylov系にすべきか |
| Hessianの不定性 | 負の曲率が出る問題では、部分問題側で負曲率方向を扱える手法が必要 |
| 評価コストと精度要求 | 高精度な停留点を求めるほど、trust-region診断を丁寧に追う価値が上がる |

Hessian-vector積（HVP）は自動微分やadjoint法で得られても、方向微分checkをしないと符号や単位の誤りに気づけません。

## 条件付きの選び分け

| 役割 | 手法 | 優先しやすい条件 | 切り替えを考える条件 |
|---|---|---|---|
| CG打ち切りで部分問題を近似 | [Trust-region Newton-CG](#/learn/trust-region-newton-cg) | Hessian-vector積が得られ、中規模までの一般滑らか問題を大域化したい | CGの打ち切りが不安定、Hessianが強く不定 |
| Krylov部分空間で部分問題を近似 | [Trust-krylov](#/learn/trust-krylov) | 大規模でHessian-vector積のみ利用でき、より精密な部分問題解が欲しい | Krylov反復が伸びる、部分問題のコストが支配的 |
| 残差構造を直接利用 | [Gauss–Newton](#/learn/gauss-newton) | 目的が非線形最小二乗で、残差Jacobianから曲率近似を作れる | 残差が大きい・強い非線形性がありGN近似の質が悪い |
| damping付きで安定化した残差法 | [Levenberg–Marquardt（least-squares）](#/learn/least-squares) | 非線形最小二乗で、Gauss–Newton近似の不安定さをtrust-region的に抑えたい | damping調整だけでは収束せず、bounds制約が本質的に必要 |
| bounds付き非線形最小二乗 | [Trust-region reflective](#/learn/trust-region-reflective) | 変数に上下限があり、境界に応じてtrust-regionを変形したい | bounds以外の一般制約が中心になる |

厳密な部分問題解法（nearly exact trust-region）を使う実装もありますが、対応する記事はまだないため、名前だけの参考にとどめます。

これは一般性能rankingではありません。同じproblem instance、初期点、微分情報の入手経路、tolerance、budgetで比較します。

## うまくいったサインと切替サイン

うまく進んでいるときは、次の観測が揃います。

- actual reductionとpredicted reductionの比が1に近い値で安定する
- 信頼半径が縮小し続けずに、拡大と縮小を繰り返しながら前進する
- 部分問題の反復数（CG iterationsなど）が極端に増えない
- 勾配ノルムまたは残差ノルムが一貫して小さくなる

切替サイン:

- 信頼半径が縮小し続ける → modelの品質、微分の正しさ、問題のscaleを確認する
- actual/predicted reduction比が悪化し続ける → 二次modelが問題の局所構造を捉えていない
- 部分問題の反復数（CG iterations、rejected steps）が支配的なコストになる → より安価な部分問題解法や別のglobalizationへ切り替える
- 非線形最小二乗でGauss–Newton近似が発散気味 → Levenberg–Marquardtやtrust-region reflectiveへ切り替える

## 小さな比較の型

実装比較では、iteration数だけでなく評価回数と部分問題の反復数も記録します。

```python
experiment = {
    "problem_instance": "same-smooth-objective",
    "initial_point": [1.0, -1.0],
    "derivative_source": "hessian-vector-product-checked",
    "objective_evaluation_budget": 500,
    "gradient_evaluation_budget": 500,
    "gradient_tolerance": 1e-6,
    "methods": ["trust-ncg", "trust-krylov", "lm"],
}

assert experiment["objective_evaluation_budget"] > 0
```

## コラム: 信頼半径はなぜ縮んだり広がったりするのか

trust-region法は、一歩を踏んだあとにactual reductionとpredicted reductionの比を計算します。比が十分大きければ「modelは信用できた」と判断して半径を広げるか維持し、比が小さければ「modelは今回の範囲では信用できなかった」として半径を縮めます。この仕組みにより、Hessianが不定で負の曲率が出る局面でも、半径の内側で解ける部分問題の範囲に一歩を制限して大域化を保てます。

半径が縮小し続ける場合、それはmodelの二次近似そのものが局所的に悪いか、微分情報に誤りがある兆候です。半径を人為的に固定して無理に前進させるより、まず微分のcheckと問題のscalingを見直します。

## 次に読む

一般の滑らかな局所最適化全体を見渡すには[滑らかな局所最適化の選び分け](#/learn/family.smooth-local)へ進みます。
