# Conditional priority audit

Issue #97で求めた「まず試す」「この条件なら切り替える」という条件付き優先度について、dataset `0.15.1`のcanonical DB、atomic predicates、decision rules、published family guideを照合した。この監査は不完全な総合scoreを追加せず、現在のauthorityで何が言えるかを確定するものである。

## Authorityの分離

| 問い | Authority | この監査での扱い |
|---|---|---|
| 条件付きの読み方や切替サイン | family guideと`methods` 4条件欄 | 人が読む選択理由。global rankingにしない |
| 候補のpromotion | `decision_rules` | 既存のrecommendation behaviorを維持する |
| 前提衝突による候補の制限 | atomic predicates / predicate policies | ADR 0004どおり`require`と`exclude`に限定する |
| 学習上の近縁関係 | `learning_edges` | `related_method_ids`との所有関係が未確定なため二重更新しない |

`default_start`、`preferred_when`、`fallback_when`はfamily guide上の説明役割であり、atomic policyの新しいeffectではない。これらを数値化したり、atomic predicatesへpromotionを持たせたりすると、`decision_rules`と競合する第二のrecommendation systemになる。

## 欠落と重複

canonical `methods`はfamily 16件と具体手法83件の計99件だった。全件で次の4欄は非空であり、文字列としての欠落はない。

- `first_choice_conditions`
- `second_choice_conditions`
- `avoid_conditions`
- `switch_signals`

ただし、具体手法83件のうちfamily rowと文字列が完全一致したものは次のとおりである。

| Field | Family文面と完全一致 |
|---|---:|
| `first_choice_conditions` | 30 / 83 |
| `second_choice_conditions` | 82 / 83 |
| `avoid_conditions` | 82 / 83 |
| `switch_signals` | 82 / 83 |

これは空欄よりも発見しにくい種類の欠落である。familyの共通文面はあるが、個々の手法に必要な切替観測量や例外条件が表現されていない。

`related_method_ids`は99件中95件が空で、Trust Region Reflective周辺だけが使用している。一方、`atlas_metadata.json`の`learning_edges`もmethodからmethodへのedgeは15件である。どちらが正規relation authorityかを決めずに両方へbackfillするとdriftが生じるため、この監査では更新しない。

## Atomic coverage

atomic predicate coverageは99件中15件で、`complete` 6件、`partial` 9件だった。

- complete: `M_NELDER_MEAD`, `M_BFGS`, `M_SLSQP`, `M_INTERIOR_POINT_NLP`, `M_BAYESIAN_OPT_GP`, `M_CMA_ES`
- partial: `M_GRADIENT_DESCENT`, `M_LBFGS`, `M_LBFGSB`, `M_BRANCH_BOUND`, `M_BRANCH_CUT`, `M_CP_SAT`, `M_SIMPLEX`, `M_ACTIVE_SET_QP`, `M_PRIMAL_DUAL_CONIC`

ここでの`complete`は、現行recommendationが必要とする不適合判定を移行済みという意味である。4条件欄の全文をatomic化したという意味ではない。

## 優先して明確化する手法

family guideの説明とcanonical条件を照合すると、次の手法は単なる共通文面では誤解しやすい。

| Method IDs | 曖昧さまたは衝突 |
|---|---|
| `M_SPSA` | 高次元で座標ごとの有限差分が高価な場合をfirst choiceにしながら、継承したavoidが高次元・高価を除外する |
| `M_SUBGRADIENT` | proxが使えない場合をfirst choiceにしながら、継承したavoidがproxの高価さを除外条件にする |
| `M_RANDOM_SEARCH` | second-choice文面が自分自身を「random searchで予算不足」の時の候補として扱う |
| `M_HYPERBAND_ASHA`, `M_PBT` | surrogateの交差検証・不確実性校正・acquisition重複というswitch signalが手法の観測量に合わない |
| `M_DIRECT`, `M_SHGO` | populationの多様性喪失をswitch signalとするが、実際には矩形分割やsampling complexが診断対象になる |
| `M_DIRECT_SHOOTING`, `M_ILQR_DDP` | collocation固有のdefectやmesh refinementが共通switch signalに入っている |
| `M_COORDINATE_DESCENT`, `M_MIRROR_DESCENT` | ADMM/prox寄りのresidual文面で、特徴間相関やmirror mapの不適合を表せない |
| `M_ADMM_QP` | LP/QP/conic一般のgapとmemory文面で、primal/dual residualのbalanceを表せない |
| `M_DIJKSTRA_ASTAR`, `M_HUNGARIAN`, `M_NETWORK_SIMPLEX`, `M_LOCAL_SEARCH_COMBINATORIAL` | DP寄りのstate count explosionを一律にswitch signalにし、side constraintや問題構造の違いを表せない |

これらは一括でfamily文面を書き換えず、手法固有のobservableと根拠を確定できた単位ごとにcanonical migrationとして扱う。

## 参照整合性

published guide `dual-annealing`は、canonical DBに存在しない`M_DUAL_ANNEALING`を参照していた。既存の`M_SIMULATED_ANNEALING`は`dual annealing`をaliasに持ち、SciPy実装`I_SCIPY_DUAL_ANNEALING`もこの手法に接続されている。したがって新しいmethod IDを作らず、guideを`M_SIMULATED_ANNEALING`へ接続する。

published method guideのmethod IDはcontent validationでcanonical `methods`と照合する。これにより、density reportではpassするがAtlasに存在しない、というphantom methodの再発を防ぐ。

## 影響と次の仕分け

- recommendation behavior: 変更なし
- dataset release identity: 変更なし
- schema / migration: 変更なし
- generated site data: corrected Markdownをcanonical exporterから再生成する
- density audit: published guideの現在数と生成reportの一致をtestで固定する

次のcanonical data修正では、上記の優先IDをfamilyごとに分け、利用可能なobservableとswitch conditionの根拠を揃える。`related_method_ids`の大規模backfillは、`learning_edges`とのauthorityを決める別のrelation cleanupとする。
