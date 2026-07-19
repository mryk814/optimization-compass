---
content_id: concept.path-terminal-constraints
kind: concept
canonical_entity_type: feature
canonical_entity_id: F_CONSTRAINT_CLASS
title_ja: path・terminal制約
title_en: Path and Terminal Constraints
summary: path制約は軌道の途中で守る条件、terminal制約は終端で守る条件であり、どの時刻で評価した可行性かを分けて扱います。
source_ids: [S042, S043, S050, S076]
related_ids: [family.optimal-control, direct-collocation, multiple-shooting, direct-shooting, ilqr-ddp]
status: published
last_reviewed: 2026-07-18
---

path制約は軌道の途中で守る条件、terminal制約は終端で守る条件であり、どの時刻で評価した可行性かを分けて扱います。

## 制約は「どこで守るか」まで書く

軌道最適化の制約は、同じ不等式でも時刻の範囲で意味が変わります。

![横方向に進む軌道が青緑の許容帯を通り、途中では赤い帯域外への逸脱があり、終端では別の円形目標へ到達する模式図](./media/path-terminal-constraint-geometry.png "path制約は軌道の全区間、terminal制約は終端で評価することを示す教育用模式図です。mesh点だけの評価では点と点の間の違反を見逃し得ます。")

| 種類 | 典型形 | 例 | 見落としやすい点 |
| --- | --- | --- | --- |
| initial constraint | $x_0=x_{\mathrm{measured}}$ | 現在位置・初期速度 | 推定値とmodelの初期化を混同する |
| path constraint | $g(x_k,u_k)\leq0$ for all $k$ | 入力上限、温度上限、障害物回避 | mesh点だけ確認して時刻の間を見ない |
| terminal constraint | $h(x_N)=0$ または $g_T(x_N)\leq0$ | 目標姿勢、残量、到達条件 | 終端costだけで到達を代用する |

terminal costは「終端へ近づく好み」を表せますが、terminal constraintそのものではありません。たとえば目標に少し近ければよい問題と、必ず所定の姿勢・速度で止まる必要がある問題は、定式化で区別します。

## path制約は毎時刻のチェックリスト

入力の上限を例にすると、

$$
u_{\min}\leq u_k\leq u_{\max}\qquad(k=0,\ldots,N-1)
$$

は各時刻の入力を守る制約です。状態の上限や障害物距離も同様に、軌道の途中で破れた瞬間があれば不適です。

結果の表には、`max_violation`だけでなく、どの制約が・いつ・どの程度破れたかを残します。制約ごとにscaleが違うなら、物理単位の違反量とsolver内部の正規化残差を混ぜずに表示します。

## mesh上の可行性と連続時間の可行性

direct法ではpath制約をmesh点やcollocation pointで評価します。これは実用的な近似ですが、その時刻で制約を満たしたことと、点と点の間で常に満たすことは同じではありません。

特に障害物の近傍、速いdynamics、bang-bangに近いcontrolでは、粗いmeshが違反を見逃すことがあります。候補解では次を確認します。

- より細かい時刻でforward simulationし、path制約を再評価する
- mesh refinementで最大違反・終端誤差・costが安定するかを見る
- 制約のactive化が意図した時刻に起きているかを見る

::: warning
mesh点で`max_violation = 0`でも、「連続時間で安全」とは限りません。連続時間の保証が必要な問題では、評価点の増加だけで済ませず、モデル・補間・安全marginを含む検証の設計を別に置きます。
:::

## 制約を罰則へ逃がす前に

path制約をpenaltyとしてobjectiveへ入れると、solverは違反とcostを交換できます。違反を絶対に許さない条件なら、penalty係数を大きくしただけでhard constraintになったとは扱いません。許容する違反、評価する時刻、最終判定のthresholdを明記します。

## 次に読む

path制約を疎なNLP制約として置く形は[Direct Collocation](#/learn/direct-collocation)、segmentごとに扱う形は[Direct Multiple Shooting](#/learn/multiple-shooting)で確認できます。制約が離散化にどう依存するかは[時間discretization](#/learn/concept.time-discretization)へ進みます。
