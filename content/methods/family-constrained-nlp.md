---
content_id: family.constrained-nlp
kind: method
method_id: MF_CONSTRAINED_NLP
title_ja: 制約付き非線形最適化の選び分け
title_en: Choosing a Constrained Nonlinear Optimizer
summary: 滑らかな目的関数と一般制約を同時に扱うとき、SLSQP・内点法・拡張Lagrange法などを選び分ける入口です。
source_ids: [S017, S029, S030, S056, S064]
related_ids: [constrained-continuous, slsqp, interior-point-nlp, augmented-lagrangian, projected-gradient, active-set]
visualization_ids: [constrained-disk-feasible-region]
comparison_ids: []
status: published
last_reviewed: 2026-07-26
---

滑らかな目的関数と一般制約を同時に扱うとき、SLSQP・内点法・拡張Lagrange法などを選び分ける入口です。

## 30秒でつかむ

この手法群では、目的値と実行可能性を同時に考えます。
実行可能領域から外れないことに加え、外れた状態から制約を満たす方向へ戻ることも重要です。

- 見ているもの: 目的値／制約違反／勾配／ヤコビ行列／KKT残差
- 動かすもの: 現在点／Lagrange 乗数／障壁またはペナルティ／部分問題
- 前進の判断: 目的値改善と実行可能性改善の両立
- 主な弱点: 尺度の調整／誤ったヤコビ行列／実行不能なモデル／制約想定が成り立たないこと

低い目的値でも制約違反があれば候補解ではありません。`success=True`だけでなく、最大制約違反と停止理由を読みます。

## まず確認すること

| 確認項目 | 選択への影響 |
|---|---|
| 制約の種類 | 上下限、線形、滑らかな非線形、ブラックボックスのどれか |
| ヤコビ行列 | 正確に計算できるか、疎性を渡せるか |
| 初期点 | 実行可能な初期点が必要か、実行不能な初期点から回復できるか |
| 問題規模 | 密な SQP部分問題か、疎なKKT系か |
| 必要精度 | 実用的な可行解か、高精度なKKT点か |
| 凸性 | 局所KKT点と大域最適解を区別できるか |

LP・凸QP・錐形式へ落とせる場合は、一般NLPより先に専用解法を検討します。
等式制約を安全に変数消去できる場合もあります。

## 条件付きの選び分け

| 役割 | 手法 | 優先しやすい条件 | 切り替えを考える条件 |
|---|---|---|---|
| 小～中規模の実用候補 | [SLSQP](#/learn/slsqp) | 上下限と一般制約、比較的少数変数、ヤコビ行列を利用可能 | 制約違反が停滞、部分問題が不安定 |
| 高精度・疎な大規模NLP | [非線形内点法](#/learn/interior-point-nlp) | 多数の滑らかな制約、疎なKKT構造 | 障壁の進行が悪い、行列分解がメモリを圧迫 |
| 制約を段階的に強める | [拡張Lagrange法](#/learn/augmented-lagrangian) | 制約付き部分問題を解きやすい、乗数更新を管理できる | ペナルティだけが増え、実行可能性が改善しない |
| 単純集合へ戻す | [Projected Gradient](#/learn/projected-gradient) | 箱型制約、単体、球など射影が安価 | 射影自体が難しい、一般非線形制約がある |
| 有効な制約を明示 | [Active-set](#/learn/active-set) | QPや少数の有効制約、ウォームスタートが効く | 有効制約集合の出入りが激しい、退化が強い |
| 高精度な一般手法 | [SQP](#/methods/M_SQP) | 中規模、正確な微分情報、局所高精度 | QP部分問題やメリット関数調整が支配的 |

ペナルティ法は「制約付き問題が無制約問題になった」わけではありません。ペナルティ係数と残る違反量を別に記録します。

## うまくいったサインと切替サイン

追うべき値:

- 最大の制約違反
- 停留性 / KKT残差
- 相補性
- 主問題・双対問題の実行可能性
- 採用・棄却した一歩
- 障壁パラメータまたはペナルティパラメータ
- 行列分解の終了状態

切替サイン:

- 目的値だけ改善し違反が減らない → メリット関数／尺度の調整／ヤコビ行列／手法を再確認
- 乗数やペナルティが発散的に増える → 実行不能性またはモデルの不一致を疑う
- KKT 行列分解の失敗 → 正則化／尺度の調整／別の線形方程式解法を検討
- 有効制約集合が頻繁に反転 → 内点法や別の大域化を検討
- 実行可能性は良いが停留性が停滞 → 微分の検算と許容誤差を確認

## 小さな比較の型

比較では、同じ初期点だけでなく、初期点が実行可能かどうかも記録します。

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

KKT条件は、適切な正則性の下で局所最適解が満たす重要な条件です。
しかし、非凸問題でKKTの残差が小さくても大域最適性を意味しません。
制約想定が破れている場合は、乗数の解釈も難しくなります。

実務ではKKT残差／実行可能性／複数初期値／目的値／物理的妥当性を組み合わせて判断します。

## 実行可能領域を図で読む

[制約付き2次元問題の実行記録](#/theater/learning/SCENARIO_CONSTRAINED_DISK)は、目的関数の等高線と実行可能領域を同じ図に置きます。

![円内の実行可能領域と目的関数の等高線を重ね、制約を評価する経路と無視する経路の終了点を比較した固定2次元実行結果。](./media/constrained-feasibility-execution.svg "目的改善と実行可能性を別々に読む固定教材です。制約付きソルバー間の一般性能順位付けではありません。")

目的値が下がる方向と、制約を満たす方向が一致するとは限らないことを、制約違反と終了状態を分けて確認できます。

これはSLSQP、内点法、拡張Lagrange法の実装性能を順位付けする図ではありません。
固定した教育問題で、低い目的値だけを成功条件にしないための読み方を示します。

## 次に読む

制約が線形・凸二次・錐構造なら[LP・QP・錐最適化](#/learn/lp-qp-conic)を確認します。
制約が評価関数としてしか得られない場合は[局所微分不要法の選び分け](#/learn/family.local-dfo)へ進みます。
