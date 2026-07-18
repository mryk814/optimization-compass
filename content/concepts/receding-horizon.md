---
content_id: concept.receding-horizon
kind: concept
canonical_entity_type: method
canonical_entity_id: MF_OPTIMAL_CONTROL
title_ja: receding horizon
title_en: Receding Horizon
summary: receding horizonは有限horizonの軌道最適化を観測のたびに解き直し、計画したcontrol列の先頭だけを実行する運用の考え方です。
source_ids: [S042, S043, S076]
related_ids: [family.optimal-control, direct-shooting, multiple-shooting, direct-collocation, ilqr-ddp]
status: published
last_reviewed: 2026-07-18
---

receding horizonは有限horizonの軌道最適化を観測のたびに解き直し、計画したcontrol列の先頭だけを実行する運用の考え方です。

## 計画を全部は実行しない

時刻$t$で、現在の推定state $x_t$から先の$N$stepを最適化し、control列

$$
U_t^*=(u_{t|t}^*,u_{t+1|t}^*,\ldots,u_{t+N-1|t}^*)
$$

を得たとします。receding horizonでは先頭の$u_{t|t}^*$だけを適用し、次の観測でstateを更新して、また$N$step先まで解きます。horizonは時間とともに前へ滑るのでreceding horizonと呼びます。

open-loopの1回きりの軌道最適化と違い、観測したstateから計画を更新できるのがこの運用の核です。ただし、毎回解き直せることと、実際の閉ループ性能・安全性・安定性が自動で保証されることは別です。

## 1 cycleで分けて見るもの

| 段階 | 入力 | 出力 | 記録すべきこと |
| --- | --- | --- | --- |
| state estimation | センサ値・前回の実行 | 現在stateの推定 | timestamp、遅れ、推定の不確かさ |
| trajectory optimization | 推定state・reference・制約 | horizon内のcontrol列とstate列 | solve time、停止理由、constraint violation |
| execution | 先頭control | 次の実系の応答 | 実行時間、飽和、通信遅延 |
| shift / warm start | 前回の解 | 次cycleの初期軌道 | どの区間をshiftしたか、再初期化条件 |

この4段階を混ぜると、「solverは成功しているのに追従が悪い」理由を見失います。推定、model mismatch、solve time、入力の飽和はそれぞれ別の失敗経路です。

## horizonの長さは未来を見る距離と計算時間の交換

horizonを長くすると遠い目標や制約を計画へ入れやすくなりますが、変数と計算時間も増えます。短すぎるhorizonでは、先の制約や目標を見ずに近視眼的な入力を選ぶことがあります。実時間に間に合わないhorizonは、良いoffline解でもそのcycleのcontrolになりません。

比較では、horizonだけでなくsample time、許容solve time、初期化方法、同じstate推定、同じ制約評価を揃えます。`平均solve time`だけではなく、deadlineを越えた回数とそのとき採った制御動作も残します。

## warm startは魔法ではない

前cycleの解を1stepずらして初期軌道へ入れるwarm startは、連続するcycleの計算を助けることがあります。しかし、referenceの急変、接触状態の切替、観測の飛び、制約のactive set変化では、過去の解がかえって悪い初期値になります。

warm startを使うなら、shift後の初期軌道が初期stateと整合しているか、違反をどう初期化するか、失敗時にどの安全な制御へ移るかをsystem設計として明示します。ここでのfallbackは最適化器の比較を隠すためではなく、実行系の責務です。

::: warning
receding horizonは計画を更新する運用であり、特定のsolver・離散化・feedback保証を意味しません。結果は[時間discretization](#/learn/concept.time-discretization)、state estimation、model mismatch、実行deadlineを含めて評価します。
:::

## 次に読む

有限horizonの変数と制約の置き方は[trajectory variable](#/learn/concept.trajectory-variable)と[path・terminal制約](#/learn/concept.path-terminal-constraints)から確認できます。local feedbackの考え方を含む軌道更新は[iLQR / DDP](#/learn/ilqr-ddp)、directな制約処理は[Direct Collocation](#/learn/direct-collocation)へ進みます。
