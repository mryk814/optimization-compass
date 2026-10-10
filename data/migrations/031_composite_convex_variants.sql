-- Add Douglas-Rachford splitting, Frank-Wolfe, CCCP and DCA (editorial scope TOPIC_DOUGLAS_RACHFORD / TOPIC_FRANK_WOLFE / TOPIC_CCCP / TOPIC_DCA).
-- All four are placed in MF_COMPOSITE_CONVEX. Douglas-Rachford is the prox-splitting sibling of ADMM and proximal gradient.
-- Frank-Wolfe: the family definition (convex structure, projection/prox/decomposition oracles, primal-dual gap certificate, convex_global scope)
-- fits an oracle-based method whose oracle is a linear minimization; MF_CONSTRAINED_NLP is defined by smooth KKT-based NLP (SQP, interior point, active set),
-- and M_PROJECTED_GRADIENT there is the local-NLP framing. Frank-Wolfe's guarantee is the convex O(1/k) gap (Jaggi 2013), so it sits with the composite/oracle family.
-- CCCP and DCA solve a sequence of convex subproblems for difference-of-convex objectives; they are placed in the same family (convex subproblem oracle) with
-- solution_scope local. CCCP is kept distinct from DCA: CCCP is the differentiable concave-part form, DCA the subgradient (nonsmooth) general form.
-- No implementation rows: no existing implementation row covers these algorithms.
PRAGMA foreign_keys = ON;

INSERT INTO sources (
  source_id, source_type, title, author_or_organization, publication_date,
  accessed_date, url, supported_claim, source_quality, notes, currentness_status
) VALUES
(
  'S128', 'original_paper',
  'On the numerical solution of heat conduction problems in two and three space variables',
  'Jim Douglas Jr.; H. H. Rachford Jr.', '1956-01-01', '2026-10-10',
  'https://doi.org/10.1090/S0002-9947-1956-0084194-4',
  'The Douglas-Rachford scheme: an implicit alternating-direction finite-difference method for heat conduction whose operator-splitting form is the origin of the Douglas-Rachford iteration.',
  'primary', 'Transactions of the American Mathematical Society 82(2), 421-439 (1956), DOI 10.1090/S0002-9947-1956-0084194-4. Volume and pages confirmed on 2026-10-10 against the AMS listing via search. The paper treats linear heat-conduction finite differences; its extension to maximal monotone operators and convex minimization is Lions and Mercier (S129).',
  'historical_primary'
),
(
  'S129', 'original_paper',
  'Splitting algorithms for the sum of two nonlinear operators',
  'P.-L. Lions; B. Mercier', '1979-01-01', '2026-10-10',
  'https://doi.org/10.1137/0716071',
  'Douglas-Rachford and forward-backward splitting for the sum of two maximal monotone operators, with convergence results and application to convex minimization.',
  'primary', 'SIAM Journal on Numerical Analysis 16(6), 964-979 (1979), DOI 10.1137/0716071. Volume, issue and pages confirmed on 2026-10-10 via search (the SIAM page exists for the DOI; the page range was confirmed from citing literature because the SIAM page is paywalled).',
  'historical_primary'
),
(
  'S130', 'original_paper',
  'An algorithm for quadratic programming',
  'Marguerite Frank; Philip Wolfe', '1956-01-01', '2026-10-10',
  'https://doi.org/10.1002/nav.3800030109',
  'Frank-Wolfe algorithm: iterate by solving a linear program over the feasible polytope and moving toward its solution, originally for quadratic programming with linear constraints.',
  'primary', 'Naval Research Logistics Quarterly 3(1-2), 95-110 (1956), DOI 10.1002/nav.3800030109. Volume, issue, pages and DOI confirmed on 2026-10-10 via search against bibliographic listings (Wikipedia, MacTutor, INFORMS). The O(1/k) rate is not from this paper; see Jaggi (S131).',
  'historical_primary'
),
(
  'S131', 'original_paper',
  'Revisiting Frank-Wolfe: Projection-Free Sparse Convex Optimization',
  'Martin Jaggi', '2013-06-01', '2026-10-10',
  'https://proceedings.mlr.press/v28/jaggi13.html',
  'Primal-dual convergence analysis of Frank-Wolfe for constrained convex problems via duality gap certificates, valid for approximately solved linear subproblems, with sparsity guarantees.',
  'primary', 'Proceedings of the 30th International Conference on Machine Learning, PMLR 28(1), 427-435 (2013). Confirmed on 2026-10-10 against the PMLR listing via search. The publication_date records the month only approximately (ICML 2013, June).',
  'historical_primary'
),
(
  'S132', 'original_paper',
  'The Concave-Convex Procedure',
  'A. L. Yuille; Anand Rangarajan', '2003-04-01', '2026-10-10',
  'https://doi.org/10.1162/08997660360581958',
  'CCCP: iterative scheme for minimizing a sum of a convex and a concave function that decreases the objective monotonically; EM and some other algorithms can be rewritten in this form.',
  'primary', 'Neural Computation 15(4), 915-936 (2003), DOI 10.1162/08997660360581958. Volume, pages and DOI confirmed on 2026-10-10 via search (mlanthology); the issue number 4 and the month were not confirmed against the MIT Press page and are taken from common citation; treat the month as approximate. Preliminary version: NIPS 2001, pp. 1033-1040.',
  'historical_primary'
),
(
  'S133', 'original_paper',
  'Convex analysis approach to d.c. programming: theory, algorithms and applications',
  'Pham Dinh Tao; Le Thi Hoai An', '1997-01-01', '2026-10-10',
  'https://math.ac.vn/acta/1997-Volume22/1/pconvex-analysis-approachnbspto-d-c-programming-theory-algorithms-and-applicationsp',
  'DC programming theory (duality, local and global optimality conditions) and the DC algorithm (DCA), including convergence and finite convergence in polyhedral DC programming.',
  'primary', 'Acta Mathematica Vietnamica 22(1), 289-355 (1997). Volume, issue and pages confirmed on 2026-10-10 against the journal page and the HAL record via search. The url is the journal landing page as returned by search.',
  'historical_primary'
);

INSERT INTO methods (
  method_id, name_ja, name_en, aliases, method_family_id, method_level, summary, problem_classes, required_assumptions, derivative_information, variable_types, constraint_support, convex_fit, nonconvex_applicability, solution_scope, determinism, exactness, theoretical_guarantee, optimality_certificate, scalability, memory_tendency, per_iteration_cost, evaluation_pattern, parallelism, initialization_sensitivity, hyperparameter_sensitivity, scaling_sensitivity, noise_robustness, discontinuity_robustness, constraint_violation_handling, warm_start, online_use, strengths, weaknesses, typical_failures, avoid_conditions, first_choice_conditions, second_choice_conditions, switch_signals, beginner_level, tuning_difficulty, implementation_difficulty, explainability, stopping_criteria, diagnostic_metrics, related_method_ids, parent_method_id, child_method_ids, reference_source_ids, confidence, last_verified
) VALUES
(
  'M_DOUGLAS_RACHFORD', 'Douglas–Rachford分割法', 'Douglas-Rachford splitting', 'Douglas-Rachford;DR splitting;DRS', 'MF_COMPOSITE_CONVEX', 'variant', '目的を二つの項の和f+gに分け、各項のprox(または単調作用素のresolvent)を交互に適用して不動点へ進む分割法。smoothnessを要求せず、両項が非滑らかでもよい。', 'convex;composite;nonsmooth;sparse;distributed', 'f,gが閉真凸(または極大単調作用素の和)で、双方のproxが安価に計算できること。解が存在し、和の劣微分が劣微分の和になる等の制約想定が必要。', 'prox_of_each_term', 'continuous;structured', 'simple_sets;separable_constraints;consensus;indicator_functions', 'primary', 'conditional_without_global_guarantee', 'convex_global', 'deterministic', 'local_numerical', '極大単調作用素の和に対し、反復が作用素の不動点へ弱収束し、そのprox像が解を与えることが示されている(Lions and Mercier 1979)。ステップ幅(prox重み)の取り方に制約が少ない点が前向き後ろ向き分割と異なる。非凸問題への大域保証はこの出典では示されていない。', 'fixed_point_residual;primal_dual_gap', 'high_to_very_high', 'low_to_medium', '2つのproxの評価と加減算。proxが閉形式なら安価。', '多反復だが各反復は2つのproxのみ。', 'high_for_separable_or_distributed', 'low_convex', 'medium', 'high', 'low', 'nonsmooth_yes_discontinuous_no', 'projection;prox;indicator_function', 'yes', 'conditional', '両項が非滑らかでもよい;勾配(Lipschitz定数)を必要とせず固定のprox重みで収束理論が成り立つ;ADMMの基礎となる', '収束は一般に遅い(漸近は線形でない場合が多い);prox重みと座標スケーリングで実用速度が大きく変わる;非凸では保証がない', 'prox_weight_mismatch;slow_tail_convergence;infeasible_or_unbounded_problem_without_detection', 'fまたはgのproxが高価;非凸で証明が必須;離散変数', 'f+gの形で両項のproxが安価に得られ、片方がLipschitz勾配を持たない凸問題。', '片方が滑らかなら近接勾配法、線形制約付きの分離なら交互方向乗数法で扱える。', '不動点残差が停滞;prox重みを変えると収束が大きく変わる;片方が滑らかで勾配が使える。', 'medium', 'medium', 'medium', 'high', 'fixed_point_residual;primal_dual_residual;objective_gap;budget', 'fixed_point_residual;prox_weight;primal_residual;prox_time', 'M_ADMM;M_PROX_GRADIENT', 'MF_COMPOSITE_CONVEX', '', 'S129;S128;S066;S061', 'medium', '2026-10-10'
),
(
  'M_FRANK_WOLFE', 'Frank–Wolfe法', 'Frank-Wolfe algorithm', 'Frank-Wolfe;conditional gradient method;projection-free method', 'MF_COMPOSITE_CONVEX', 'variant', '各反復で勾配を使った線形部分問題(線形最小化オラクル)を実行可能集合上で解き、現在点からその解へ向かって凸結合で進む。射影を使わない。', 'convex;constrained;sparse;low_rank', '目的が滑らか(勾配が得られる)。実行可能集合がコンパクトな凸集合で、その上の線形最小化が安価に解けること。', 'gradient;linear_minimization_oracle', 'continuous', 'compact_convex_sets_with_linear_oracle;polytopes;norm_balls', 'primary', 'conditional_without_global_guarantee', 'convex_global', 'deterministic', 'local_numerical', '滑らかな凸目的とコンパクト凸集合に対し、反復k回後の目的gapがO(1/k)で減ることが示されている(Jaggi 2013、曲率定数に依存)。線形部分問題を近似解しても成り立つ。原論文(Frank and Wolfe 1956)は線形制約付き二次計画の方法として導入した。', 'frank_wolfe_gap;primal_dual_gap', 'very_high', 'low', '勾配評価1回と線形最小化オラクル1回。射影・prox不要。', '多反復だが各反復は勾配と線形部分問題のみ。', 'limited', 'low_convex', 'low', 'medium', 'low', 'low', 'feasible_iterates_by_convex_combination', 'yes', 'conditional', '射影が不要で、反復が常に実行可能;更新が少数の頂点の凸結合なのでスパース/低ランクな解が得られやすい;Frank-Wolfe gapが停止判定になる', '収束はO(1/k)で遅い(一般の凸集合);解が頂点でない場合に反復がジグザグする;非滑らかな目的には直接使えない', 'zigzagging_near_boundary;slow_sublinear_rate;expensive_linear_oracle', '線形最小化が高価;目的が非滑らか;高精度解が必須;集合が非有界', '射影は高価だが線形最小化は安価(核ノルム球、確率単体、多面体など)な滑らかな凸問題。', '射影が安価なら射影勾配法、非滑らかなら近接勾配法やサブグラディエント法を比較する。', 'Frank-Wolfe gapの減少が停滞;ジグザグが続く;射影が実は安価。', 'medium', 'low', 'low', 'high', 'frank_wolfe_gap;objective_gap;budget', 'frank_wolfe_gap;step_size;oracle_time;iterate_sparsity', 'M_PROJECTED_GRADIENT;M_PROX_GRADIENT', 'MF_COMPOSITE_CONVEX', '', 'S130;S131;S055', 'medium', '2026-10-10'
),
(
  'M_CCCP', '凹凸手続き(CCCP)', 'Concave-convex procedure (CCCP)', 'CCCP;convex-concave procedure', 'MF_COMPOSITE_CONVEX', 'variant', '目的を凸関数と凹関数の和に分け、各反復で凹部分を現在点で線形化して凸部分問題を解く。目的が単調に減少する。', 'nonconvex;difference_of_convex;smooth', '目的が凸関数と凹関数の和(差凸)に分解でき、勾配が使えること。各反復の凸部分問題を解けること。', 'gradient_of_concave_part;convex_subproblem_solver', 'continuous', 'convex_constraints_in_subproblem', 'not_required', 'primary', 'local', 'deterministic', 'local_numerical', '各反復で目的が単調に減少することが示されている(Yuille and Rangarajan 2003)。大域最適性の保証はない。EMや反復スケーリング等の一部のアルゴリズムはCCCPとして書き直せる。', 'first_order_residual;monotone_decrease', 'medium_to_high', 'low_to_medium', '凸部分問題1回(分解次第で閉形式の更新になる)。', '反復ごとに凹部分の勾配と凸部分問題を評価。', 'by_subproblem', 'medium_to_high_nonconvex', 'low', 'medium', 'low', 'low', 'convex_subproblem_constraints', 'yes', 'no', 'ステップ幅調整が不要;目的が単調減少;凸ソルバーを部品として再利用できる;分解によっては更新が閉形式', '局所解・停留点にしか収束しない;分解の選び方で速度が変わる;凹部分が微分可能であることを前提にする', 'converges_to_poor_stationary_point;slow_convergence;expensive_convex_subproblem', '差凸の分解が自然に得られない;大域最適が必須;離散変数', '凸+凹に自然に分かれ、凹部分が微分可能で、凸部分問題が安価に解ける非凸問題。', '凹部分が非滑らかな凸関数の差になるときはDCアルゴリズム(劣勾配版)を検討する。', '目的の減少が止まる;初期値で解が大きく変わる;凸部分問題が支配的。', 'intermediate', 'low', 'low', 'high', 'objective_change;step_norm;first_order_residual;budget', 'objective_value;step_norm;subproblem_time;iteration_count', 'M_DCA;M_PROX_GRADIENT', 'MF_COMPOSITE_CONVEX', '', 'S132;S133', 'medium', '2026-10-10'
),
(
  'M_DCA', 'DCアルゴリズム(DCA)', 'Difference of convex algorithm (DCA)', 'DCA;DC algorithm;DC programming;difference-of-convex algorithm', 'MF_COMPOSITE_CONVEX', 'variant', '目的を二つの凸関数の差g-hに分け、各反復でhの劣勾配を選び、gから線形項を引いた凸部分問題を解く。双対問題にも同型の反復がある。', 'nonconvex;difference_of_convex;nonsmooth;sparse', '目的が凸関数の差として表せ(gとhは閉真凸)、hの劣勾配が得られること。凸部分問題を解けること。', 'subgradient_of_second_convex_part;convex_subproblem_solver', 'continuous', 'convex_constraints_in_subproblem', 'not_required', 'primary', 'local', 'deterministic', 'local_numerical', 'DC双対性と局所・大域最適性条件の理論があり、DCAは目的を単調に減少させ臨界点に収束することが示されている。多面体DC計画では有限収束する(Pham Dinh and Le Thi 1997)。大域最適性は一般には保証されない。', 'critical_point_residual;monotone_decrease', 'medium_to_high', 'low_to_medium', '劣勾配1つの選択と凸部分問題1回。', '反復ごとに劣勾配と凸部分問題を評価。', 'by_subproblem', 'medium_to_high_nonconvex', 'low', 'medium', 'low', 'nonsmooth_yes_discontinuous_no', 'convex_subproblem_constraints', 'yes', 'no', '非滑らかな差凸目的を扱える;目的が単調減少;DC分解の選択で多くの非凸問題(スパース正則化等)を凸部分問題の列にできる;大規模問題への適用例が多い', '局所解にしか収束しない;DC分解の選択で性能が大きく変わる;凸部分問題の解法が必要', 'bad_dc_decomposition;converges_to_poor_critical_point;expensive_convex_subproblem', 'DC分解が自然に得られない;大域最適が必須;離散変数(混合整数ではDC緩和や分枝限定と組み合わせる)', '目的が凸関数の差に自然に分解でき、凸部分問題が安価に解ける非凸(特に非滑らか)問題。', '全体が滑らかなら一般の局所最適化法、凹部分が微分可能ならCCCPと同一視できる。', '目的の減少が止まる;初期値で解が大きく変わる;DC分解を変えると結果が変わる。', 'intermediate', 'medium', 'medium', 'high', 'objective_change;step_norm;critical_point_residual;budget', 'objective_value;step_norm;subproblem_time;dc_decomposition_choice', 'M_CCCP;M_PROX_GRADIENT', 'MF_COMPOSITE_CONVEX', '', 'S133;S132', 'medium', '2026-10-10'
);

UPDATE methods
SET child_method_ids = 'M_PROX_GRADIENT;M_FISTA;M_COORDINATE_DESCENT;M_ADMM;M_MIRROR_DESCENT;M_SUBGRADIENT;M_BUNDLE;M_DOUGLAS_RACHFORD;M_FRANK_WOLFE;M_CCCP;M_DCA'
WHERE method_id = 'MF_COMPOSITE_CONVEX';

INSERT INTO method_hierarchy (
  hierarchy_id, parent_method_id, child_method_id, relation_type, depth,
  is_primary_parent, rationale, source_ids, confidence, last_verified
) VALUES
('MH_COMPOSITE_CONVEX_DOUGLAS_RACHFORD', 'MF_COMPOSITE_CONVEX', 'M_DOUGLAS_RACHFORD', 'is_a', 1, 'yes', 'Douglas-Rachford splitting is a prox-splitting method classified with ADMM and proximal gradient under Convex composite and proximal optimization.', 'S129;S066', 'medium', '2026-10-10'),
('MH_COMPOSITE_CONVEX_FRANK_WOLFE', 'MF_COMPOSITE_CONVEX', 'M_FRANK_WOLFE', 'is_a', 1, 'yes', 'Frank-Wolfe is an oracle-based convex method (linear minimization oracle instead of prox/projection) with a convex primal-dual-gap guarantee; M_PROJECTED_GRADIENT stays in related_method_ids.', 'S131;S130', 'medium', '2026-10-10'),
('MH_COMPOSITE_CONVEX_CCCP', 'MF_COMPOSITE_CONVEX', 'M_CCCP', 'is_a', 1, 'yes', 'CCCP reduces a difference-of-convex objective to a sequence of convex subproblems; it is classified with DCA under the convex-subproblem family, with local solution scope.', 'S132;S133', 'medium', '2026-10-10'),
('MH_COMPOSITE_CONVEX_DCA', 'MF_COMPOSITE_CONVEX', 'M_DCA', 'is_a', 1, 'yes', 'DCA reduces a difference-of-convex objective to a sequence of convex subproblems using a subgradient of the second convex part; local solution scope.', 'S133;S132', 'medium', '2026-10-10');

INSERT INTO terminology_aliases (
  term_id, target_type, target_id, label_ja, label_en, abbreviations_json,
  synonyms_json, domain_terms_json, misspellings_json, deprecated_terms_json,
  disambiguation_note, locale, rationale, source_ids_json, last_verified
) VALUES
('TERM_DOUGLAS_RACHFORD', 'method', 'M_DOUGLAS_RACHFORD', 'Douglas–Rachford分割法', 'Douglas-Rachford splitting', '["DRS"]',
 '["DR splitting","Douglas-Rachford"]', '["prox分割","極大単調作用素"]', '[]', '[]',
 'ADMMとは別の手法(ADMMはその双対への適用として関係する)。Peaceman-Rachford分割とも別。', 'ja-JP,en',
 '名称・略称をmethodへ解決する。', '["S129","S128"]', '2026-10-10'),
('TERM_FRANK_WOLFE', 'method', 'M_FRANK_WOLFE', 'Frank–Wolfe法', 'Frank-Wolfe algorithm', '["FW"]',
 '["conditional gradient method","projection-free method"]', '["線形最小化オラクル","条件付き勾配法"]', '[]', '[]',
 '射影勾配法とは別の手法。射影の代わりに線形最小化オラクルを使う。', 'ja-JP,en',
 '名称・略称をmethodへ解決する。', '["S130","S131"]', '2026-10-10'),
('TERM_CCCP', 'method', 'M_CCCP', '凹凸手続き', 'Concave-convex procedure', '["CCCP"]',
 '["convex-concave procedure"]', '["差凸最適化"]', '[]', '[]',
 'DCアルゴリズム(DCA)と関係が深いが、CCCPは凹部分が微分可能な形で定式化される。', 'ja-JP,en',
 '名称・略称をmethodへ解決する。', '["S132"]', '2026-10-10'),
('TERM_DCA', 'method', 'M_DCA', 'DCアルゴリズム', 'Difference of convex algorithm', '["DCA"]',
 '["DC algorithm","DC programming","difference-of-convex algorithm"]', '["差凸計画","DC分解"]', '[]', '[]',
 'CCCPと関係が深いが、DCAは劣勾配を使う一般形。直流(DC)とは無関係。', 'ja-JP,en',
 '名称・略称をmethodへ解決する。', '["S133","S132"]', '2026-10-10');

INSERT INTO evidence_links (
  evidence_link_id, source_id, target_table, target_id, supported_field,
  claim_summary, evidence_role, confidence, last_verified
) VALUES
('EL004225', 'S129', 'methods', 'M_DOUGLAS_RACHFORD', 'row', '二つの項のproxを交互に適用して和f+gを最小化する分割法。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004226', 'S128', 'methods', 'M_DOUGLAS_RACHFORD', 'row', '二つの項のproxを交互に適用して和f+gを最小化する分割法。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004227', 'S066', 'methods', 'M_DOUGLAS_RACHFORD', 'row', '二つの項のproxを交互に適用して和f+gを最小化する分割法。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004228', 'S061', 'methods', 'M_DOUGLAS_RACHFORD', 'row', '二つの項のproxを交互に適用して和f+gを最小化する分割法。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004229', 'S130', 'methods', 'M_FRANK_WOLFE', 'row', '線形最小化オラクルの解へ向かう凸結合で、射影なしに制約付き凸問題を解く。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004230', 'S131', 'methods', 'M_FRANK_WOLFE', 'row', '線形最小化オラクルの解へ向かう凸結合で、射影なしに制約付き凸問題を解く。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004231', 'S055', 'methods', 'M_FRANK_WOLFE', 'row', '線形最小化オラクルの解へ向かう凸結合で、射影なしに制約付き凸問題を解く。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004232', 'S132', 'methods', 'M_CCCP', 'row', '凸+凹の目的を、凹部分を線形化した凸部分問題の列で単調に減少させる。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004233', 'S133', 'methods', 'M_CCCP', 'row', '凸+凹の目的を、凹部分を線形化した凸部分問題の列で単調に減少させる。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004234', 'S133', 'methods', 'M_DCA', 'row', '凸関数の差の目的を、劣勾配を選んだ凸部分問題の列で単調に減少させる。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004235', 'S132', 'methods', 'M_DCA', 'row', '凸関数の差の目的を、劣勾配を選んだ凸部分問題の列で単調に減少させる。', 'supporting_or_primary', 'medium', '2026-10-10');
