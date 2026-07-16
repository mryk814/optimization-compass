---
content_id: family.constrained-nlp
kind: method
method_id: MF_CONSTRAINED_NLP
title_ja: 制約付き非線形最適化の選び分け
title_en: Choosing a Constrained Nonlinear Optimizer
summary: 滑らかな目的関数と一般制約を同時に扱うとき、SLSQP、内点法、拡張Lagrange法などを選び分ける入口です。
source_ids: [S017, S029, S030, S056, S064]
related_ids: [constrained-continuous, slsqp, interior-point-nlp, augmented-lagrangian, projected-gradient, active-set]
status: published
last_reviewed: 2026-07-16
---

滑らかな目的関数と一般制約を同時に扱うとき、SLSQP、内点法、拡張Lagrange法などを選び分ける入口です。

## 30秒でつかむ

このfamilyの気持ちは、**目的値を下げるだけでなく、実行可能領域から外れないこと、または外れた状態から制約を満たす方向へ戻ることを同時に考える**ことです。

- 見ているもの: 目的値、constraint violation、勾配、Jacobian、KKT residual
- 動かすもの: 現在点、Lagrange multiplier、barrierまたはpenalty、部分問題
- 前進の判断: objective改善とfeasibility改善の両立
- 主な弱点: scaling、誤ったJacobian、infeasible model、constraint qualification failure

低い目的値でも制約違反があれば候補解ではありません。`success=True`だけでなく、最大制約違反と停止理由を読みます。

## まず確認すること

| 確認項目 | 選択への影響 |
|---|---|
| 制約の種類 | bounds、線形、滑らかな非線形、black-boxのどれか |
| Jacobian | 正確に計算できるか、疎性を渡せるか |
| 初期点 | feasible startが必要か、infeasible startから回復できるか |
| 問題規模 | dense SQP部分問題か、sparse KKT系か |
| 必要精度 | 実用的な可行解か、高精度なKKT点か |
| convexity | 局所KKT点と大域最適解を区別できるか |

LP、凸QP、conic formへ落とせる場合は、一般NLPより先に専用solverを検討します。等式制約を安全に変数消去できる場合もあります。

## 条件付きの選び分け

| 役割 | 手法 | 優先しやすい条件 | 切り替えを考える条件 |
|---|---|---|---|
| 小～中規模の実用候補 | [SLSQP](#/learn/slsqp) | boundsと一般制約、比較的少数変数、Jacobianを利用可能 | constraint violationが停滞、部分問題が不安定 |
| 高精度・疎な大規模NLP | [非線形内点法](#/learn/interior-point-nlp) | 多数の滑らかな制約、sparse KKT構造 | barrier progressが悪い、factorizationがmemoryを圧迫 |
| 制約を段階的に強める | [拡張Lagrange法](#/learn/augmented-lagrangian) | 制約付き部分問題を解きやすい、multiplier更新を管理できる | penaltyだけが増え、feasibilityが改善しない |
| 単純集合へ戻す | [Projected Gradient](#/learn/projected-gradient) | box、simplex、球などprojectionが安価 | projection自体が難しい、一般非線形制約がある |
| active constraintを明示 | [Active-set](#/learn/active-set) | QPや少数の有効制約、warm startが効く | active setの出入りが激しい、degeneracyが強い |
| 高精度な一般手法 | [SQP](#/methods/M_SQP) | 中規模、正確なderivative、局所高精度 | QP部分問題やmerit調整が支配的 |

penalty法は「制約付き問題が無制約問題になった」わけではありません。penalty係数と残る違反量を別に記録します。

## うまくいったサインと切替サイン

追うべき値:

- maximum constraint violation
- stationarity / KKT residual
- complementarity
- primal / dual feasibility
- accepted / rejected step
- barrier parameterまたはpenalty parameter
- factorization status

切替サイン:

- 目的値だけ改善し違反が減らない → merit、scaling、Jacobian、手法を再確認
- multiplierやpenaltyが発散的に増える → infeasibilityまたはmodel mismatchを疑う
- KKT factorization failure → regularization、scaling、別linear solverを検討
- active setが頻繁に反転 → interior-pointや別のglobalizationを検討
- feasibilityは良いがstationarityが停滞 → derivative checkとtoleranceを確認

## 小さな比較の型

比較では、同じ初期点だけでなく、初期点がfeasibleかどうかも記録します。

```python
comparison = {
    "problem_instance": "same-constrained-problem",
    "initial_point": [0.0, 2.0],
    "initial_point_feasible": True,
    "objective_tolerance": 1e-8,
    "constraint_tolerance": 1e-7,
    "evaluation_budget": 1_000,
    "methods": ["SLSQP", "interior-point", "augmented-Lagrangian"],
}

assert comparison["constraint_tolerance"] > 0.0
```

## コラム: KKT条件は合格証ではない

KKT条件は、適切な正則性の下で局所最適解が満たす重要な条件です。しかし、非凸問題で小さなKKT residualが得られても、大域最適性を意味しません。また、constraint qualificationが破れている場合にはmultiplierの解釈も難しくなります。

実務では、KKT residual、feasibility、複数初期値、目的値、物理的妥当性を組み合わせて判断します。

## 次に読む

制約が線形・凸二次・錐構造なら[LP・QP・錐最適化](#/learn/lp-qp-conic)、制約が評価関数としてしか得られない場合は[局所Derivative-freeの選び分け](#/learn/family.local-dfo)も確認します。