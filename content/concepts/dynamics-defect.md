---
content_id: concept.dynamics-defect
kind: concept
canonical_entity_type: feature
canonical_entity_id: F_STRUCTURE_TRAJECTORY
title_ja: dynamics defect
title_en: Dynamics Defect
summary: dynamics defectは、離散化したtrajectoryがモデルの時間発展とどれだけずれているかを表す残差で、costとは別に可行性として追う指標です。
source_ids: [S042, S043, S050, S076]
related_ids: [family.optimal-control, multiple-shooting, direct-collocation, direct-shooting]
status: published
last_reviewed: 2026-07-18
---

dynamics defectは、離散化したtrajectoryがモデルの時間発展とどれだけずれているかを表す残差で、costとは別に可行性として追う指標です。

## 「次のstateが合っているか」の誤差

離散化したdynamicsを

$$
x_{k+1}=f_d(x_k,u_k)
$$

と書くと、時刻$k$のdefectは

$$
d_k=x_{k+1}-f_d(x_k,u_k)
$$

です。$d_k=0$なら、列として置いたstateはそのdynamicsと整合します。$\lVert d_k\rVert$が大きいなら、見た目が滑らかな軌道でも、指定したmodelをたどってはいません。

この残差はobjectiveに混ぜて小さくする場合も、NLPの等式制約として0へ押し込む場合もあります。どちらでも、結果を読むときは「costが下がったか」と「defectが許容値内か」を別に見ます。

## defectが現れる場所

| 手法 | stateをどう扱うか | defectの読み方 |
| --- | --- | --- |
| Direct Shooting | rolloutでstateを生成 | 同じ積分器・初期stateなら離散dynamicsは構成上満たしやすい。モデル誤差や積分誤差は別に残る。 |
| Direct Multiple Shooting | segment境界のstateも変数 | 各segmentの終点と次segmentの開始点の差がcontinuity defect。 |
| Direct Collocation | mesh上のstateを変数 | 多項式近似とcollocation条件から作るdynamics defect。 |
| iLQR / DDP | nominal trajectoryをrollout | update後のforward rolloutがlocal modelの外へ出ていないかを合わせて確認。 |

defectの定義は積分器、collocation scheme、stateのscaleで変わります。別の実装どうしで数値だけを並べる前に、どのnorm・正規化・時刻点を使った値かを揃えます。

## 1個のnormだけで安心しない

`max_k ||d_k||`は最悪の結び目、`sum_k ||d_k||^2`は全体量を見ます。両方が役に立ちますが、どちらも違反の位置を隠します。次の3つを一緒に記録すると、切り分けしやすくなります。

- 最大defectと、それが出た時刻
- 時刻ごとのdefect列。境界・接触・急な入力の近くで跳ねていないか
- stateごとのscaleで正規化したdefect。単位の大きい状態だけが支配していないか

costが改善してもdefectが停滞するなら、停止判定を緩める前に、初期軌道、scale、regularization、mesh、積分器のいずれが原因かを分けて確認します。

## defectが小さくても残る問い

defectが小さいことは、**離散化したモデル**に対する整合性の証拠です。実測dynamicsが合っていること、途中のpath制約を連続時間で満たすこと、より細かいmeshでも同じ解が出ることまでは意味しません。

そのため、最終候補はcontrolを独立した高精度simulationに通し、state・path制約・終端状態を再評価します。これはsolverの成否とは別の検証です。

## 次に読む

defectをsegment境界で扱う方法は[Direct Multiple Shooting](#/learn/multiple-shooting)、mesh全体の制約として扱う方法は[Direct Collocation](#/learn/direct-collocation)で確認できます。離散化そのものの読み方は[時間discretization](#/learn/concept.time-discretization)へ進みます。
