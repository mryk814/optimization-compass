---
content_id: concept.nested-equilibrium-complementarity-hybrid
kind: concept
canonical_entity_type: feature
canonical_entity_id: F_STRUCTURE_BILEVEL
title_ja: 入れ子・均衡・相補性・hybrid構造
title_en: Nested, Equilibrium, Complementarity, and Hybrid Structures
summary: 入れ子の最適化／均衡条件／相補性／hybridのmode切替を読み分ける語彙です。目的関数の種類ではなく、内側の解法／残差／離散状態を区別します。
source_ids: [S054, S055, S056, S064]
prerequisites: [concept.constraint-class, concept.dynamics-defect, concept.trajectory-variable]
related_ids: [family.constrained-nlp, family.optimal-control]
visualization_ids: [bilevel-regression-exact-inner, bilevel-regression-relaxed-complementarity, hybrid-mode-chattering-ledger]
comparison_ids: [COMPARE_BILEVEL_COMPLEMENTARITY_TREATMENT]
status: published
last_reviewed: 2026-07-24
---

入れ子の最適化／均衡条件／相補性／hybridのmode切替を読み分ける語彙です。目的関数の種類ではなく、内側の解法／残差／離散状態を区別します。

## 30秒でつかむ

この4つは同じ「複雑な最適化」ではありません。最初に、外側の目的値以外に何を解いているかを分けます。

| 構造 | 追加で解いているもの | まず記録するもの | 既存のcanonical vocabulary |
| --- | --- | --- | --- |
| bilevel / nested | 外側の変数ごとのinner optimization | inner tolerance、inner residual、解の選択規則 | `F_STRUCTURE_BILEVEL`、`F_DERIVATIVE_INNER_ITERATION` |
| equilibrium | 複数主体または条件が同時に満たす状態 | equilibrium residual、解の一意性、停止条件 | `F_STRUCTURE_GAME_EQUILIBRIUM`、`F_STRUCTURE_VARIATIONAL_INEQUALITY` |
| complementarity | 互いに同時に正になれない条件 | complementarity residual、violation、smoothing parameter | `F_STRUCTURE_COMPLEMENTARITY`、`F_CONSTRAINT_COMPLEMENTARITY` |
| hybrid / mode | 連続状態と離散modeの遷移 | mode sequence、switching event、chattering | `F_CONSTRAINT_LOGICAL`、`F_NUM_DISCRETE_VARIABLES`、`F_STRUCTURE_TRAJECTORY` |

hybridには現時点で専用のcanonical stable IDを追加していません。上表の既存語彙で、論理条件・離散変数・trajectoryのどこが問題を決めているかを記録します。`hybrid`という名前だけで、smoothなNLPや通常のoptimal controlと同一視しません。

## まず、内側の問題を外側から分ける

bilevel optimizationでは、外側の変数$x$を選ぶたびに、内側の問題を解いて得た$y^*(x)$を使います。典型的には次の形です。

$$
\min_x F(x,y^*(x)),
\qquad
y^*(x)\in\arg\min_y f(x,y)
\quad\text{subject to}\quad g(x,y)\le 0.
$$

ここで、外側のobjectiveを1回評価しただけではありません。inner solveについて、少なくとも次を別に記録します。

- iteration数
- toleranceと終了status
- inner objectiveまたはresidual

truncated solveはinner solveを途中で打ち切ります。unrolled solveは反復を計算グラフへ展開します。どちらも、得られた$y$が厳密な$y^*(x)$とは限りません。

hyperparameter selectionやinverse designも、このnested構造として読める場合があります。parameterを変えるたびに、学習／simulation／equilibrium solveを実行する場合です。ただし、外側の問題をbilevelと呼ぶには、内側の解が外側の評価へどう定義されるかを明示します。

### 解の選択規則と微分経路

inner problemに複数の解がある場合、どの解を$y^*(x)$とするかで外側の問題が変わります。

- **optimistic**: innerの解の集合から、外側に都合のよい解を選ぶ。
- **pessimistic**: innerの解の集合から、外側に不利な解を想定する。
- **algorithm-dependent**: 初期値／warm start／停止条件／solverの履歴が、実際に得る解を決める。

「solverの反復を微分した」のか、「十分に解いた後のsolution mapを微分した」のかも分けます。implicit differentiationは、解写像の局所的な関係を使う場合があります。ただし、次の場合にはその微分を無条件に保証できません。

- inner solveが未収束
- 解が非一意
- constraint qualificationが崩れる

## equilibriumは「最小化」と同じではない

equilibriumは、複数の主体や状態方程式が一方的な改善だけでは動けない状態を表します。その改善では、他の条件を固定します。game equilibriumだけでなく、network／market／mechanicsの状態を均衡条件で定める場合もあります。

variational inequalityなら、集合$C$上の状態$z$について、次のように書けます。

$$
\text{find }z\in C
\quad\text{such that}\quad
G(z)^\mathsf{T}(w-z)\ge 0
\quad\text{for all }w\in C.
$$

この条件を満たすことは、ある目的関数のglobal minimumを証明することと同じではありません。最適化のobjective／equilibrium residual／constraint violation／解の一意性を別々に記録します。外側で設計を最適化するなら、design updateとequilibrium solveの停止を混ぜません。

## complementarityは接触だけの語ではない

相補性（complementarity）は、非負の量$a(z)$と$b(z)$が同時には正にならない条件です。

$$
a(z)\ge 0,
\qquad b(z)\ge 0,
\qquad a(z)b(z)=0.
$$

一方が正なら他方は0で、両方が0の境界も許します。KKT条件ではactive constraintとmultiplierに現れます。ほかにも、contactのgapとnormal forceやMPECのequilibrium constraintに現れます。

exact complementarityをそのまま扱ったのか、penalty・smoothing・relaxationで近似したのかを分けます。たとえば$s_\mu(a,b)=0$のような平滑化条件を使っても、有限の$\mu$で$ab=0$を満たしたとは限りません。少なくともcomplementarity residual、非負制約のviolation、smoothingまたはpenalty parameterの履歴を保存します。

## hybridはmodeの扱いを先に決める

hybrid systemでは、連続状態$x(t)$と離散mode$m(t)$が同時に現れます。modeごとに状態方程式や制約が異なり、eventでmodeが切り替わることがあります。

次の二つは別の問題です。

- **prescribed mode schedule**: modeの順序や切替時刻を先に固定し、連続変数だけを調整する。
- **mode discovery**: 候補modeや切替時刻そのものを探索し、mode sequenceを決める。

前者を解いたからといって、後者のmode選択まで最適化したことにはなりません。modeの表現は、離散変数／logical constraint／trajectoryのeventに分けて記録します。mode sequenceとswitching eventを目的値の履歴から推測しないようにします。chatteringやrelaxation artifactがある場合は、連続状態が滑らかでもmodeの意味が壊れていないか確認します。

## 4つの構造をまたぐ診断値

同じrunに複数の構造が含まれる場合でも、次の値を一つの「収束」へまとめません。

| 判定 | 見るもの | 読み方 |
| --- | --- | --- |
| outer progress | outer objective、design change、outer iteration | 外側の目的が進んだか |
| inner solve | inner residual、inner tolerance、inner status、inner iteration数 | その外側点で内側をどこまで解いたか |
| equilibrium / complementarity | equilibrium residual、constraint violation、complementarity residual | 条件をどのtoleranceで満たしたか |
| derivative route | implicit、unrolled、solver iteration、numerical derivative | 何を微分したか |
| mode behavior | mode sequence、switching event、chattering | どのmodeを選び、どこで切り替わったか |
| stationarity | stationarity residual、constraint qualification、active set | 停止条件の意味と未保証の範囲 |

inner residualが小さくてもouter objectiveが改善するとは限りません。逆に、outer objectiveが改善してもinner solveが粗ければ、outer gradientやequilibriumの評価が変わります。異なる種類の残差を単位やtoleranceをそろえずに比較しません。

## TheaterとCompareで読む

[bilevel正則化回帰Case](#/gallery/bilevel-regularized-regression)で、外側の係数更新と内側のridge回帰を分けて確認します。

[exact innerのTheater](#/theater/learning/SCENARIO_BILEVEL_REGRESSION_EXACT)は、固定した6回のouter updateを追います。
outerとinnerのobjectiveを分け、inner iteration数も表示します。
さらにinner residual、stationarity residual、complementarity residualを同じevaluation軸に並べます。
outerの1点はinnerの1 iterationではありません。
inner toleranceを満たしてからouter updateへ進んだことも確認します。

[finite relaxationのTheater](#/theater/learning/SCENARIO_BILEVEL_REGRESSION_RELAXED)は同じouter budgetとinner policyを使います。
inner toleranceとderivative routeも固定します。
変更するのはcomplementarity treatmentだけで、$\tau=10^{-2}$の有限relaxationを使います。
[Compare](#/compare/COMPARE_BILEVEL_COMPLEMENTARITY_TREATMENT)では、relaxed側のouter objectiveがより低くても残差を確認します。
complementarity residualが残るrunを、exact KKTの達成や順位へ読み替えません。

[mode chatteringのTheater](#/theater/learning/SCENARIO_HYBRID_MODE_CHATTERING)は、既存contractで表せる最小のsecondary failure sliceです。
目的関数とdynamics defectが下がる一方で、active modeが交互に切り替わります。
switching intervalも縮む固定ledgerです。
これはcontact/friction solverや物理simulationではなく、一般的なmode discovery性能も示しません。
active contactや摩擦力の表示には、canonical authorityと実行可能artifactが別途必要です。

::: warning
教育用の小さなrunで得たstationarity／exactness／mode sequenceは、一般の問題に対するglobal guaranteeではありません。対象にはbilevel／MPEC／接触問題／hybrid systemが含まれます。結果を解釈する前に、前提を明記します。前提はinner solve policy／解の選択規則／relaxation／mode discovery／constraint qualificationです。
:::

## 次に読む

[制約class](#/learn/concept.constraint-class)で、equality／inequality／logical／complementarityを別々の可行性判定として確認します。trajectoryのstateと更新を分けるときは、[trajectory変数](#/learn/concept.trajectory-variable)と[dynamics defect](#/learn/concept.dynamics-defect)へ進みます。実際のsolver familyとの接続は、[制約付きNLP](#/learn/family.constrained-nlp)と[optimal control](#/learn/family.optimal-control)で確認します。
