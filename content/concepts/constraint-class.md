---
content_id: concept.constraint-class
kind: concept
canonical_entity_type: feature
canonical_entity_id: F_CONSTRAINT_CLASS
title_ja: 制約class
title_en: Constraint Class
summary: 制約classは、解として許される領域をどの式・論理・simulationで定めるかを表し、可行性の扱いとsolver選択を左右します。
source_ids: [S017, S029, S054, S055, S056]
related_ids: [family.constrained-nlp, family.discrete-structure, projected-gradient, augmented-lagrangian]
status: published
last_reviewed: 2026-07-18
---

制約classは、解として許される領域をどの式・論理・simulationで定めるかを表し、可行性の扱いとsolver選択を左右します。

## 目的値が良くても、可行でなければ候補解ではない

最小化問題では目的`f(x)`を小さくしたくなりますが、`x`が許容領域に入っていることは別の条件です。たとえば温度を下げるほど目的が改善しても、装置の下限温度を破れば実行できません。制約はこの「実行できる範囲」を定義します。

一般には、bounds、等式、不等式を次のように書きます。

$$
\min_x f(x)\quad \text{subject to}\quad l \le x \le u,\; g(x) \le 0,\; h(x) = 0.
$$

この式だけでなく、制約を評価できる情報の質が重要です。`g(x)`とそのJacobianを滑らかに計算できるのか、Boolean論理として扱うのか、simulationが失敗したとき初めて違反が分かるのかで、使える手法と診断値が変わります。

## よくあるclassと、読むべき量

| class | 例 | 解法側で読む量 |
| --- | --- | --- |
| bounds | 温度、濃度、設計範囲 | 各変数の下限・上限、active bound |
| linear | 予算、質量保存、容量 | slack、dual、線形緩和のbound |
| smooth nonlinear | 応力、反応速度、幾何条件 | constraint value、Jacobian、KKT residual |
| equality / dynamics | 収支、状態方程式、ODE | defect、初期・終端条件、integration error |
| combinatorial / logical | 排他、順序、資源割当 | domain reduction、conflict、incumbent / gap |
| implicit / failure | simulator crash、実験失敗 | failure率、再試行規則、保守的な判定 |

「制約なし」も有用な分類ですが、単にまだ制約を聞いていない状態とは区別します。不明な制約は`unknown`であり、制約なしと仮定してよい根拠にはなりません。

## 制約の形をsolverへ渡せるか

boundsやsimplexのようにprojectionが安価な集合なら、[Projected Gradient](#/learn/projected-gradient)のように一歩進んでから集合へ戻す方法を使えます。滑らかな一般制約と微分があるなら、[制約付き非線形最適化](#/learn/family.constrained-nlp)で扱うSQP、内点法、拡張Lagrange法などが候補です。

一方で、`Aを選ぶならBを選ばない`、`3台のうち2台まで`、`この順序でしか工程を通せない`のような制約は、連続微分可能な不等式へ無理に直すより、[離散・組合せ最適化](#/learn/family.discrete-structure)として論理・整数・global constraintを表現する方が自然なことがあります。

penaltyを目的へ足す方法は、制約違反を無視してよいという意味ではありません。係数を大きくするほど数値条件が悪くなることがあり、有限のpenaltyでは違反が残る場合もあります。目的値と最大違反量を別々に記録します。

## 可行性の確認を仕様にする

最適化の完了条件を`success`フラグだけにしないで、問題に応じた可行性判定を書き下します。

- 不等式は最大違反量と許容tolerance
- 等式は残差のnormと単位に応じたtolerance
- dynamicsはmesh上のdefectだけでなく、必要なら区間内の制約確認
- 論理・整数制約は丸め後ではなく、最終candidateの割当で判定
- simulation失敗は大きな目的値へ黙って置換せず、failureとして件数・条件・扱いを記録

非凸問題で小さいKKT residualが得られても、大域最適性の証明にはなりません。また、離散化されたmodelの可行性を、そのまま連続系・実機の安全性として読まないようにします。

::: note
制約は「solverへ渡す入力」である前に、解を採用してよいかを決める製品・実験上の仕様です。式、単位、tolerance、判定時点を一緒に保存すると、再現と切替がしやすくなります。
:::

## 次に読む

変数が連続・整数・trajectoryのどれかは[変数のdomain](#/learn/concept.variable-domain)、評価が高価で違反を事前に判定しにくい場合の予算配分は[評価費と予算](#/learn/concept.evaluation-cost)を確認してください。
