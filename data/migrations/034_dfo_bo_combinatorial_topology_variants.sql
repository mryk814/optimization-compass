-- Add BOBYQA, SafeOpt, constrained Bayesian optimization, ParEGO, greedy submodular maximization and level-set topology optimization
-- (editorial scope TOPIC_BOBYQA / TOPIC_SAFEOPT / TOPIC_CONSTRAINED_BO / TOPIC_PAREGO / TOPIC_SUBMODULAR_GREEDY / TOPIC_LEVELSET).
-- Placement (docs/identity-granularity.md: an executable algorithm is a methods row, method_level 'variant', is_a its family):
--   M_BOBYQA              MF_DFO_LOCAL: quadratic-interpolation trust-region DFO for bound constraints, a sibling of M_COBYLA / M_COBYQA.
--   M_SAFEOPT             MF_SURROGATE_HPO: GP surrogate with an acquisition rule; the safe set is part of the acquisition (not a separate family).
--   M_CONSTRAINED_BO      MF_SURROGATE_HPO: GP surrogates for objective and constraints with a feasibility-weighted acquisition. One row for the
--                         approach; Gardner et al. 2014 and Gelbart et al. 2014 are two formulations of it, kept in the text, not as two rows.
--   M_PAREGO              MF_MULTI_OBJECTIVE, not MF_SURROGATE_HPO: what the method returns is a Pareto-set approximation produced by repeated
--                         augmented-Chebyshev scalarization with random weights (a sibling of M_WEIGHTED_SUM). The GP / expected improvement step is
--                         a subroutine inherited from EGO and is recorded in related_method_ids (M_BAYESIAN_OPT_GP).
--   M_SUBMODULAR_GREEDY   MF_GRAPH_DP, following the precedent of M_LOCAL_SEARCH_COMBINATORIAL (a combinatorial heuristic already placed in
--                         MF_GRAPH_DP, which this catalog uses for dedicated discrete-structure algorithms). This is a maintainer lead decision;
--                         the family definition (path / flow / matching / DP structure) is stretched to include set-function structure.
--   M_LEVELSET_TOPOLOGY   MF_TOPOLOGY_OPTIMIZATION: boundary-evolution update with shape derivatives, beside M_SIMP_TOPOLOGY / M_OC_TOPOLOGY / M_MMA.
-- Not added: TOPIC_SOBOL_DESIGN. A Sobol sequence is a low-discrepancy point generator, a component (primitive) used for initial or space-filling
-- designs inside other methods (BO initial design, quasi-random search); it does not choose evaluation points adaptively and has no optimizer
-- stopping rule, solution scope or failure modes of its own. By docs/identity-granularity.md a primitive is a glossary term plus a section of the
-- articles that use it, not a methods row. It is reported for the maintainers (glossary / article section; scope relation primitive_in).
-- Implementation map: only M_BOBYQA -> I_NLOPT (NLOPT_LN_BOBYQA, confirmed against the NLopt algorithms page, already source S018). No BoTorch /
-- Ax mapping is added for constrained BO or ParEGO because the current API could not be confirmed from an official page in this environment.
-- No new implementation rows.
PRAGMA foreign_keys = ON;

INSERT INTO sources (
  source_id, source_type, title, author_or_organization, publication_date,
  accessed_date, url, supported_claim, source_quality, notes, currentness_status
) VALUES
(
  'S145', 'original_paper',
  'The BOBYQA algorithm for bound constrained optimization without derivatives',
  'M. J. D. Powell', '2009-08-01', '2026-10-10',
  'https://www.damtp.cam.ac.uk/user/na/NA_papers/NA2009_06.pdf',
  'Derivative-free minimization under simple lower and upper bounds using a quadratic model by interpolation, trust-region steps, and the RESCUE recovery routine.',
  'primary', 'Department of Applied Mathematics and Theoretical Physics, University of Cambridge, report NA2009/06 (August 2009). Title, author, report number and content confirmed on 2026-10-10 via search (NAG documentation links to the DAMTP PDF; a mirror is on optimization-online.org); the PDF itself could not be opened from this environment, so the URL is the one cited by the NAG documentation.',
  'historical_primary'
),
(
  'S146', 'original_paper',
  'Safe Exploration for Optimization with Gaussian Processes',
  'Yanan Sui; Alkis Gotovos; Joel Burdick; Andreas Krause', '2015-07-01', '2026-10-10',
  'https://proceedings.mlr.press/v37/sui15.html',
  'SafeOpt: Gaussian-process optimization that only evaluates points believed to stay above a safety threshold, with a convergence guarantee to the optimum reachable within the safe set.',
  'primary', 'Proceedings of the 32nd International Conference on Machine Learning (ICML), PMLR 37:997-1005, 2015. Authors, title, venue and pages confirmed on 2026-10-10 against the PMLR record via search.',
  'historical_primary'
),
(
  'S147', 'original_paper',
  'Bayesian Optimization with Inequality Constraints',
  'Jacob R. Gardner; Matt J. Kusner; Zhixiang (Eddie) Xu; Kilian Q. Weinberger; John P. Cunningham', '2014-06-01', '2026-10-10',
  'https://proceedings.mlr.press/v32/gardner14.html',
  'Bayesian optimization with Gaussian-process priors on both the objective and inequality constraint functions, using a constraint-aware acquisition for problems where feasibility is as costly to evaluate as the objective.',
  'primary', 'Proceedings of the 31st International Conference on Machine Learning (ICML), PMLR 32(2):937-945, 2014. Confirmed on 2026-10-10 against the PMLR record via search; the PMLR listing omits the third author surname, which the PDF gives as Xu.',
  'historical_primary'
),
(
  'S148', 'original_paper',
  'Bayesian Optimization with Unknown Constraints',
  'Michael A. Gelbart; Jasper Snoek; Ryan P. Adams', '2014-07-01', '2026-10-10',
  'https://arxiv.org/abs/1403.5607',
  'Constrained Bayesian optimization with unknown, possibly noisy constraints modelled by Gaussian processes, with the objective and constraints evaluable separately (decoupled).',
  'primary', 'Proceedings of the 30th Conference on Uncertainty in Artificial Intelligence (UAI 2014), Quebec City; arXiv:1403.5607. Authors, title, venue and the arXiv number confirmed on 2026-10-10 via search; page ranges differ between the AUAI and PMLR listings, so none is recorded.',
  'historical_primary'
),
(
  'S149', 'original_paper',
  'ParEGO: a hybrid algorithm with on-line landscape approximation for expensive multiobjective optimization problems',
  'Joshua Knowles', '2006-02-01', '2026-10-10',
  'https://doi.org/10.1109/TEVC.2005.851274',
  'ParEGO: extension of efficient global optimization to multiobjective problems by repeatedly scalarizing the objectives with randomly drawn weights and fitting a Gaussian-process model that is updated after each evaluation.',
  'primary', 'IEEE Transactions on Evolutionary Computation 10(1), 50-66, February 2006, DOI 10.1109/TEVC.2005.851274. Volume, issue, pages and DOI confirmed on 2026-10-10 via search (author project page and bibliographic indexes); the full text was not read, so the claim is limited to the title, abstract-level description and the method summary on the author page.',
  'historical_primary'
),
(
  'S150', 'original_paper',
  'An analysis of approximations for maximizing submodular set functions-I',
  'G. L. Nemhauser; L. A. Wolsey; M. L. Fisher', '1978-12-01', '2026-10-10',
  'https://doi.org/10.1007/BF01588971',
  'For a nondecreasing submodular set function with z(empty) = 0 under a cardinality constraint K, the greedy heuristic attains at least 1 - ((K-1)/K)^K of the optimal value; the bound is tight for each K and tends to (e-1)/e.',
  'primary', 'Mathematical Programming 14(1), 265-294 (1978), DOI 10.1007/BF01588971. Volume, pages, DOI and the guarantee confirmed on 2026-10-10 against the Springer record via search. Part II (Fisher, Nemhauser, Wolsey, Mathematical Programming Study 8, 73-87) is a different paper and is not recorded.',
  'historical_primary'
),
(
  'S151', 'original_paper',
  'A level set method for structural topology optimization',
  'Michael Yu Wang; Xiaoming Wang; Dongming Guo', '2003-01-01', '2026-10-10',
  'https://doi.org/10.1016/S0045-7825(02)00559-5',
  'Level-set representation of the structural boundary that is moved by solving a Hamilton-Jacobi equation with a velocity field from shape sensitivity, allowing topology changes during structural optimization.',
  'primary', 'Computer Methods in Applied Mechanics and Engineering 192(1-2), 227-246 (2003), DOI 10.1016/S0045-7825(02)00559-5. Venue, volume, pages and DOI confirmed on 2026-10-10 via a repository record and an institutional publication list; the full text was not read, so the claim is limited to the title and the standard description of the method.',
  'historical_primary'
),
(
  'S152', 'original_paper',
  'Structural optimization using sensitivity analysis and a level-set method',
  'Gregoire Allaire; Francois Jouve; Anca-Maria Toader', '2004-02-01', '2026-10-10',
  'https://doi.org/10.1016/j.jcp.2003.09.032',
  'Combines the classical shape derivative with the level-set method for front propagation to optimize elastic structures in two and three dimensions.',
  'primary', 'Journal of Computational Physics 194(1), 363-393 (2004), DOI 10.1016/j.jcp.2003.09.032. Volume, pages and DOI confirmed on 2026-10-10 via the IP Paris research portal and HAL-based records via search; the full text was not read.',
  'historical_primary'
);

INSERT INTO methods (
  method_id, name_ja, name_en, aliases, method_family_id, method_level,
  summary, problem_classes, required_assumptions, derivative_information, variable_types, constraint_support,
  convex_fit, nonconvex_applicability, solution_scope, determinism, exactness, theoretical_guarantee,
  optimality_certificate, scalability, memory_tendency, per_iteration_cost, evaluation_pattern, parallelism,
  initialization_sensitivity, hyperparameter_sensitivity, scaling_sensitivity, noise_robustness, discontinuity_robustness, constraint_violation_handling,
  warm_start, online_use, strengths, weaknesses, typical_failures, avoid_conditions,
  first_choice_conditions, second_choice_conditions, switch_signals, beginner_level, tuning_difficulty, implementation_difficulty,
  explainability, stopping_criteria, diagnostic_metrics, related_method_ids, parent_method_id, child_method_ids,
  reference_source_ids, confidence, last_verified
) VALUES
(
  'M_BOBYQA', 'BOBYQA', 'Bound optimization by quadratic approximation (BOBYQA)', 'BOBYQA;Powell BOBYQA;Bound Optimization BY Quadratic Approximation', 'MF_DFO_LOCAL', 'variant', '上下限だけを持つ問題に対し、補間で作る二次modelとtrust regionで関数値のみから局所解を探すPowellのDFO。評価点は常に上下限を満たす。', 'continuous;black_box;local;bound_constrained', '評価が有限で、局所探索に十分な予算。上下限は有限であること。目的は局所的に二次modelで近似できる程度に滑らか。', 'function_values_only', 'continuous;bounds', 'bounds', 'viable', 'yes_local_only', 'local', 'deterministic', 'local_numerical', '二次補間modelとtrust regionによる局所的な降下。一般の非滑らかな目的や非線形制約に対する大域・停留性保証は出典(Powell 2009)の範囲外。', 'usually_none', 'low_to_medium_dimensions', 'medium', '補間点の追加・置換とtrust-region部分問題。', '次元に応じた補間点数(典型的には2n+1)の評価を最初に要し、以降は少数の評価で更新する。', 'sequential', 'high', 'medium', 'medium', 'low_to_medium', 'low', 'bounds_only', 'yes', 'rare', '微分不要;少ない評価数で局所解に収束しやすい;評価点が常に上下限内;補間点数を選べる', '非線形制約は扱えない(上下限のみ);非滑らかな目的やnoiseに弱い;高次元では補間点が多く重い;局所解', 'noise_stall;model_degeneracy;local_minimum;poor_scaling', '非線形制約が本質的;評価にnoiseが大きい;目的が不連続;大域探索が必要', '上下限のみ、滑らか、低〜中次元で評価が高価、微分が信用できない連続最適化。', '制約が必要ならCOBYLA / COBYQA、非滑らか寄りならNelder-Mead / Powell法。', '非線形制約が出てきた;noiseで停滞する;次元に対し補間点数が重い。', 'intermediate', 'medium', 'high', 'medium', 'trust_region_radius;objective_change;budget', 'evaluation_count;trust_region_radius;interpolation_points;model_error', 'M_COBYQA;M_COBYLA;M_POWELL;M_NELDER_MEAD', 'MF_DFO_LOCAL', '', 'S145;S018', 'medium', '2026-10-10'
),
(
  'M_SAFEOPT', 'SafeOpt', 'SafeOpt (safe Bayesian optimization with Gaussian processes)', 'SafeOpt;safe Bayesian optimization;safe exploration with Gaussian processes', 'MF_SURROGATE_HPO', 'variant', '未知関数をGaussian processでmodel化し、安全閾値を超えると信頼区間で保証できる領域(safe set)内だけを評価しながら、最適点と安全領域の拡大を両立して探索する手法。', 'expensive_black_box;safe_exploration;adaptive_experimentation;hyperparameter_optimization', '未知関数が既知のkernelのRKHSノルム有界(またはGP事前)で、Lipschitz等の滑らかさがあり、安全閾値と少なくとも1点の既知の安全な初期点がある。', 'function_values', 'continuous_low_dimensional', 'safety_threshold_on_the_function_value', 'not_required', 'primary', 'feasible_only', 'stochastic', 'statistical', 'kernelや事前の仮定の下で、評価点が高確率で安全であること、および到達可能な安全領域内の最適値への収束が示される(Sui et al. 2015)。仮定が成り立たない場合は保証されない。', 'none;confidence_interval_not_certificate', 'low_dimensions_and_observations', 'medium_to_high_with_observations', 'GP更新と安全集合・潜在最適集合・拡張集合の計算。', '安全が確認された点の近傍を逐次評価する。', 'sequential', 'high', 'high', 'medium', 'medium_if_modeled', 'low', 'safe_set_confidence_bound', 'yes', 'yes', '評価中の安全性を高確率で保てる;実機・臨床・推薦など失敗が許されない場面で使える;不確実性に基づく探索', '安全な初期点が必要;kernelや閾値の仮定に敏感;高次元で安全集合の管理が難しい;探索範囲が保守的で遅い', 'misspecified_kernel_unsafe_evaluation;overly_conservative_exploration;no_safe_initial_point;high_dimensional_safe_set', '安全な初期点が無い;失敗しても構わない(通常のBOで足りる);高次元;kernelの仮定が成り立たない', '評価で閾値を下回ると実害が出る、低次元の実機調整・制御パラメータ調整。', '通常の制約付きBO(違反を許容して学習できる場合)。', '安全な点の周りしか探索できない;信頼区間が広すぎて安全集合が広がらない;次元が増えた。', 'advanced', 'high', 'high', 'medium', 'evaluation_budget;safe_set_stall;confidence_gap', 'safe_set_size;best_safe_value;posterior_uncertainty;threshold_margin', 'M_BAYESIAN_OPT_GP;M_CONSTRAINED_BO', 'MF_SURROGATE_HPO', '', 'S146', 'medium', '2026-10-10'
),
(
  'M_CONSTRAINED_BO', '制約付きベイズ最適化', 'Constrained Bayesian optimization', 'constrained BO;constrained Bayesian optimization;Bayesian optimization with unknown constraints;Bayesian optimization with inequality constraints', 'MF_SURROGATE_HPO', 'variant', '目的関数と未知の不等式制約の両方をGaussian processでmodel化し、制約を満たす確率を重みにしたacquisition(期待改善など)で次の評価点を選ぶベイズ最適化。', 'expensive_black_box;black_box_constraints;hyperparameter_optimization;adaptive_experimentation', '評価が高価で、制約も評価して初めて分かるblack-box関数。制約の充足を示す値(または充足確率)を評価ごとに観測できる。目的と制約が確率modelで近似できる程度に滑らか。', 'function_values', 'continuous;integer_by_encoding', 'black_box_inequality_constraints', 'not_required', 'primary', 'global_candidate', 'stochastic', 'statistical', 'acquisitionの定義に基づく経験的な手法。収束保証はmodelやacquisitionの仮定に依存し、実装一般への保証ではない。', 'none;feasibility_probability_not_certificate', 'low_to_medium_dimensions_and_observations', 'medium_to_high_with_observations', 'surrogate fitting(目的と各制約)とacquisition最適化。', '少ない高価評価を逐次に選ぶ。目的と制約を別々に評価できる設計(decoupled)もある。', 'batch_or_asynchronous', 'medium', 'high', 'high', 'medium_if_modeled', 'model_dependent', 'feasibility_probability_weighting;constraint_surrogate', 'yes', 'yes', '制約評価が高価でも評価数を節約できる;実行可能領域に集中して探索できる;制約の不確実性を扱える', '可行点が見つからない序盤に探索が偏る;制約surrogateの誤りが実行可能性の誤判定になる;高次元・不連続な制約に弱い;充足確率は実行可能性の証明ではない', 'infeasible_recommendation;constraint_surrogate_mismatch;no_feasible_point_found;acquisition_failure', '制約が安価に評価できる(解析的に扱える);評価中も制約違反が許されない(SafeOptなど安全性を保つ手法が必要);極端な高次元', '1評価が高価で、制約もblack-boxの低〜中次元問題。', '制約が既知で安価ならpenaltyや制約付きsolver、評価中の違反が許されないならSafeOpt。', '可行点が見つからない;制約surrogateの校正が悪い;次元増加でGPが不安定。', 'advanced', 'high', 'high', 'medium', 'evaluation_budget;time;expected_improvement;feasible_found', 'best_feasible_so_far;feasibility_probability;constraint_violation_rate;surrogate_error;failed_trials', 'M_BAYESIAN_OPT_GP;M_SAFEOPT;M_TURBO_SAASBO', 'MF_SURROGATE_HPO', '', 'S147;S148', 'medium', '2026-10-10'
),
(
  'M_PAREGO', 'ParEGO', 'ParEGO (Pareto efficient global optimization)', 'ParEGO;Pareto efficient global optimization;augmented Chebyshev scalarization BO', 'MF_MULTI_OBJECTIVE', 'variant', '反復ごとに乱数の重みで複数目的を拡張Chebyshevスカラー化し、得られた単目的関数にGaussian process(期待改善)を適用して次の評価点を選ぶことで、少ない評価でPareto集合を近似する多目的最適化。', 'multiobjective;Pareto;expensive_black_box', '評価が高価な少数目的のblack-box問題。目的は各評価で同時に観測でき、目的の尺度を正規化できる。スカラー化後の関数がGPで近似できる程度に滑らか。', 'function_values', 'continuous', 'bounds;constraints_by_variant', 'scalarization_covers_nonconvex_front_by_Chebyshev', 'yes', 'pareto', 'stochastic', 'statistical', 'Pareto集合の近似であり、被覆や最適性の一般的な保証はない。Chebyshevスカラー化は重み付き和と異なり非凸なPareto frontの点も到達可能にする。', 'none;pareto_approximation_not_certificate', 'low_dimensions_few_objectives', 'medium_to_high_with_observations', 'スカラー化関数の再計算、GP fitting、期待改善の最適化。', '少ない高価評価で逐次にPareto集合を広げる。', 'sequential', 'medium', 'medium', 'high', 'medium_if_modeled', 'low', 'backend_or_feasibility_ranking', 'yes', 'rare', '少ない評価でPareto集合を近似できる;重みを乱数にするだけで実装が単純;非凸frontにも到達しうる', '目的数や次元が増えるとGPが不安定;重みのサンプリングによる被覆が不均一;1反復で1点しか得られず並列化が難しい', 'poor_coverage;objective_scaling;surrogate_mismatch;slow_sequential_progress', '評価が安価;目的が多い(4以上);バッチ並列評価が必要', '少数目的で評価が高価なblack-box多目的問題。', '評価が安価ならNSGA-IIなど、並列バッチが必要ならhypervolume系acquisition。', 'Pareto被覆が偏る;目的が増えた;GPの学習が破綻。', 'advanced', 'medium', 'medium', 'medium', 'evaluation_budget;hypervolume_stall;coverage', 'hypervolume;spacing;surrogate_error;feasible_fraction', 'M_WEIGHTED_SUM;M_BAYESIAN_OPT_GP;M_EPSILON_CONSTRAINT;M_NSGA_II', 'MF_MULTI_OBJECTIVE', '', 'S149', 'medium', '2026-10-10'
),
(
  'M_SUBMODULAR_GREEDY', '劣モジュラ関数の貪欲法', 'Greedy maximization of a submodular function', 'submodular greedy;greedy submodular maximization;greedy algorithm for monotone submodular maximization;lazy greedy', 'MF_GRAPH_DP', 'variant', '単調な劣モジュラ集合関数を要素数Kの制約の下で最大化するために、限界利得が最大の要素を一つずつ加えるheuristic。最適値の(1-1/e)倍以上が保証される。', 'combinatorial;set_function;cardinality_constraint;coverage;sensor_placement', '集合関数が単調非減少で劣モジュラ(限界利得が集合の拡大で減る)、f(空集合)=0、要素数の上限があり、関数値のoracleを呼べる。', 'none', 'discrete;set', 'cardinality_constraint;matroid_by_variant', 'not_applicable', 'structure_specific', 'feasible_only', 'deterministic', 'approximation', '単調非減少の劣モジュラ関数の濃度制約付き最大化で、最適値の1-((K-1)/K)^K倍(極限は1-1/e)以上を達成し、この比は一般に改善できない(Nemhauser, Wolsey, Fisher 1978)。単調性か劣モジュラ性が崩れると保証は失われる。', 'approximation_ratio_not_optimality', 'high_with_lazy_evaluation', 'low', 'K回の反復で全要素の限界利得を評価(lazy evaluationで削減可能)。', '関数値oracleをO(nK)回呼ぶ。', 'method_specific', 'not_applicable', 'low', 'low', 'not_applicable', 'native_discrete', 'cardinality_limit', 'conditional', 'yes_by_incremental_update', '単純で高速;(1-1/e)の近似保証;集合被覆・センサー配置・特徴選択などへ広く使える;lazy evaluationで高速化できる', '保証は単調性と劣モジュラ性に依存;非単調や複雑な制約では保証が弱まる;最適解を保証しない', 'non_submodular_objective;non_monotone_objective;marginal_gain_oracle_cost;ties_in_gain', '目的が劣モジュラでない;厳密な最適性証明が必要;複雑な制約(knapsackやmatroidの交差)を無修正で扱う場合', '単調な劣モジュラ関数を要素数制約の下で最大化する被覆・選択問題。', '厳密解が必要ならMILP、複雑な制約や非単調なら別の近似アルゴリズムやlocal search。', '劣モジュラ性の仮定が崩れる;制約が濃度以外になる;最適性ギャップを知りたい。', 'beginner', 'low', 'low', 'high', 'cardinality_reached;marginal_gain_below_tolerance', 'objective_value;marginal_gain;oracle_calls;approximation_ratio_bound', 'M_LOCAL_SEARCH_COMBINATORIAL;M_BRANCH_BOUND', 'MF_GRAPH_DP', '', 'S150', 'medium', '2026-10-10'
),
(
  'M_LEVELSET_TOPOLOGY', 'レベルセット法による形状更新', 'Level-set method for structural topology optimization', 'level set method;level-set topology optimization;level-set shape update;level set shape optimization', 'MF_TOPOLOGY_OPTIMIZATION', 'variant', '構造の境界を暗黙の関数(レベルセット関数)のゼロ等高線で表し、形状微分から得た速度場でHamilton-Jacobi方程式を解いて境界を動かす構造最適化の更新法。境界の分岐・統合による位相変化を扱える。', 'topology_optimization;shape_optimization;pde_constrained;structural_design', '状態方程式(線形弾性など)、形状微分または位相微分、レベルセット関数の初期化と再初期化、体積などの制約を定義する。', 'analytic_gradient;adjoint', 'field;shape', 'integral;state;bounds', 'weak', 'yes_local_only', 'local', 'deterministic', 'local_numerical', '離散化・初期形状・速度場の延長・再初期化に依存する局所的な数値解で、大域最適性や連続問題の保証はない。', 'feasibility;stationarity_diagnostics', 'high_with_sparse_state_solve', 'high', '状態solve、感度計算とレベルセット関数の移流更新。', '各反復で状態equation・adjoint・速度場を評価する。', 'sparse_linear_algebra;distributed', 'high', 'high', 'high', 'low', 'low', 'lagrange_multiplier_or_augmented_lagrangian', 'conditional', 'no', '明確な境界を持つ設計が得られる;位相変化を扱える;グレー領域が生じにくい', '初期形状に依存し新しい穴を作りにくい手法がある;再初期化やCFL条件など数値的な調整が多い;実装が重い', 'initial_design_dependence;no_new_holes;reinitialization_artifact;velocity_extension_error;state_solve_failure', '穴の生成が必須で初期形状に頼れない場合(位相微分などの補助が要る);製造制約を無注釈で保証すると主張する場合', '明確な境界と滑らかな形状が必要で、境界の形状微分が使えるcompliance系構造最適化。', 'グレー領域が許容できるならSIMPなど密度法を比較する。', '初期形状に依存して改善しない;境界が数値的に振動する;新しい穴が必要。', 'advanced', 'high', 'very_high', 'high', 'max_iterations;volume_tolerance;compliance_change;state_residual', 'compliance;volume_fraction;boundary_velocity_norm;reinitialization_count;state_residual', 'M_SIMP_TOPOLOGY;M_ADJOINT_SENSITIVITY;M_MMA', 'MF_TOPOLOGY_OPTIMIZATION', '', 'S151;S152', 'medium', '2026-10-10'
);

UPDATE methods
SET child_method_ids = 'M_NELDER_MEAD;M_POWELL;M_PATTERN_SEARCH;M_MADS;M_COBYLA;M_COBYQA;M_SPSA;M_BOBYQA'
WHERE method_id = 'MF_DFO_LOCAL';
UPDATE methods
SET child_method_ids = 'M_BAYESIAN_OPT_GP;M_TPE;M_SMAC_RF;M_TURBO_SAASBO;M_RANDOM_SEARCH;M_HYPERBAND_ASHA;M_PBT;M_SAFEOPT;M_CONSTRAINED_BO'
WHERE method_id = 'MF_SURROGATE_HPO';
UPDATE methods
SET child_method_ids = 'M_WEIGHTED_SUM;M_EPSILON_CONSTRAINT;M_NSGA_II;M_NSGA_III;M_MOEA_D;M_PAREGO'
WHERE method_id = 'MF_MULTI_OBJECTIVE';
UPDATE methods
SET child_method_ids = 'M_DYNAMIC_PROGRAMMING;M_NETWORK_SIMPLEX;M_HUNGARIAN;M_DIJKSTRA_ASTAR;M_LOCAL_SEARCH_COMBINATORIAL;M_BELLMAN_FORD;M_AUGMENTING_MAXFLOW;M_PUSH_RELABEL;M_SUCCESSIVE_SHORTEST_PATH;M_SUBMODULAR_GREEDY'
WHERE method_id = 'MF_GRAPH_DP';
UPDATE methods
SET child_method_ids = 'M_SIMP_TOPOLOGY;M_DENSITY_FILTER;M_OC_TOPOLOGY;M_MMA;M_ADJOINT_SENSITIVITY;M_LEVELSET_TOPOLOGY'
WHERE method_id = 'MF_TOPOLOGY_OPTIMIZATION';

INSERT INTO method_hierarchy (
  hierarchy_id, parent_method_id, child_method_id, relation_type, depth,
  is_primary_parent, rationale, source_ids, confidence, last_verified
) VALUES
('MH_DFO_LOCAL_BOBYQA', 'MF_DFO_LOCAL', 'M_BOBYQA', 'is_a', 1, 'yes', 'BOBYQA is a quadratic-interpolation trust-region derivative-free method for bound constraints, classified with COBYLA and COBYQA under Local derivative-free optimization.', 'S145;S018', 'medium', '2026-10-10'),
('MH_SURROGATE_HPO_SAFEOPT', 'MF_SURROGATE_HPO', 'M_SAFEOPT', 'is_a', 1, 'yes', 'SafeOpt chooses evaluations from a Gaussian-process surrogate under a safety constraint, classified with Gaussian-process Bayesian optimization.', 'S146', 'medium', '2026-10-10'),
('MH_SURROGATE_HPO_CONSTRAINED_BO', 'MF_SURROGATE_HPO', 'M_CONSTRAINED_BO', 'is_a', 1, 'yes', 'Constrained Bayesian optimization adds constraint surrogates and a feasibility-aware acquisition to Gaussian-process Bayesian optimization.', 'S147;S148', 'medium', '2026-10-10'),
('MH_MULTI_OBJECTIVE_PAREGO', 'MF_MULTI_OBJECTIVE', 'M_PAREGO', 'is_a', 1, 'yes', 'ParEGO returns a Pareto-set approximation by repeated random-weight Chebyshev scalarization, classified with the weighted-sum scalarization; the Gaussian-process step is a subroutine.', 'S149', 'medium', '2026-10-10'),
('MH_GRAPH_DP_SUBMODULAR_GREEDY', 'MF_GRAPH_DP', 'M_SUBMODULAR_GREEDY', 'is_a', 1, 'yes', 'Greedy submodular maximization is a combinatorial heuristic with a dedicated structure, classified with combinatorial local search under Graph algorithms and dynamic programming (maintainer lead decision).', 'S150', 'medium', '2026-10-10'),
('MH_TOPOLOGY_LEVELSET', 'MF_TOPOLOGY_OPTIMIZATION', 'M_LEVELSET_TOPOLOGY', 'is_a', 1, 'yes', 'Level-set boundary evolution is a topology optimization update beside the density-based SIMP method.', 'S151;S152', 'medium', '2026-10-10');

INSERT INTO terminology_aliases (
  term_id, target_type, target_id, label_ja, label_en, abbreviations_json,
  synonyms_json, domain_terms_json, misspellings_json, deprecated_terms_json,
  disambiguation_note, locale, rationale, source_ids_json, last_verified
) VALUES
('TERM_BOBYQA', 'method', 'M_BOBYQA', 'BOBYQA法', 'BOBYQA', '[]',
 '["Bound Optimization BY Quadratic Approximation","Powell BOBYQA"]', '["二次補間model","trust region","bound constraints"]', '[]', '[]',
 '非線形制約を扱えるCOBYLA / COBYQAとは別で、上下限のみを扱う。', 'ja-JP,en',
 '名称をmethodへ解決する。', '["S145"]', '2026-10-10'),
('TERM_SAFEOPT', 'method', 'M_SAFEOPT', 'SafeOpt法', 'SafeOpt', '[]',
 '["safe Bayesian optimization","safe exploration with Gaussian processes","安全ベイズ最適化"]', '["safe set","安全探索"]', '[]', '[]',
 '評価中も安全閾値を守る手法で、違反を許容して学習する制約付きベイズ最適化とは別。', 'ja-JP,en',
 '名称をmethodへ解決する。', '["S146"]', '2026-10-10'),
('TERM_CONSTRAINED_BO', 'method', 'M_CONSTRAINED_BO', '制約付きベイズ最適化', 'Constrained Bayesian optimization', '["constrained BO","CBO"]',
 '["Bayesian optimization with unknown constraints","Bayesian optimization with inequality constraints","制約付きBO"]', '["black-box constraints","feasibility probability","充足確率"]', '[]', '[]',
 '評価中の安全を保つSafeOptとは別。無制約のGP-BOは別のmethod。', 'ja-JP,en',
 '名称と略称をmethodへ解決する。', '["S147","S148"]', '2026-10-10'),
('TERM_PAREGO', 'method', 'M_PAREGO', 'ParEGO法', 'ParEGO', '[]',
 '["Pareto efficient global optimization"]', '["拡張Chebyshevスカラー化","多目的ベイズ最適化"]', '[]', '[]',
 '固定の重みで一回だけスカラー化する重み付き和法とは別。乱数の重みを反復ごとに引く。', 'ja-JP,en',
 '名称をmethodへ解決する。', '["S149"]', '2026-10-10'),
('TERM_SUBMODULAR_GREEDY', 'method', 'M_SUBMODULAR_GREEDY', '劣モジュラ関数の貪欲法', 'Greedy submodular maximization', '[]',
 '["submodular greedy","劣モジュラ貪欲法","lazy greedy"]', '["限界利得","(1-1/e)近似","被覆問題"]', '[]', '[]',
 '単調な劣モジュラ関数に対する近似保証つきの貪欲法で、一般の貪欲heuristicや組合せlocal searchとは別。', 'ja-JP,en',
 '名称をmethodへ解決する。', '["S150"]', '2026-10-10'),
('TERM_LEVELSET_TOPOLOGY', 'method', 'M_LEVELSET_TOPOLOGY', 'レベルセット法による形状更新', 'Level-set method for structural topology optimization', '[]',
 '["level set method","level-set shape update","レベルセット形状更新"]', '["Hamilton-Jacobi","形状微分","暗黙関数"]', '[]', '[]',
 '密度場を設計変数とするSIMPとは別。流体の界面追跡のレベルセット法一般ではなく、構造最適化の更新法を指す。', 'ja-JP,en',
 '名称をmethodへ解決する。', '["S151","S152"]', '2026-10-10');

INSERT INTO method_implementation_map (
  method_implementation_map_id, method_id, implementation_id, support_level, api_name,
  method_selector, implementation_notes, limitations, source_ids, confidence, last_verified
) VALUES
('MIM_BOBYQA_NLOPT', 'M_BOBYQA', 'I_NLOPT', 'native', 'nlopt.opt', 'LN_BOBYQA',
 'NLoptのBOBYQAはPowellのBOBYQAサブルーチンをCへ変換し、NLoptの停止条件に合わせて修正したもの。上下限は設定できる。',
 '上下限のみを扱い、非線形制約はaugmented Lagrangian等の併用が必要。二次近似のため二階微分可能でない目的では性能が落ちうる。機能・optionはversionで確認。実装対応は一般的推奨を意味しない。', 'S018;S145', 'medium', '2026-10-10');

UPDATE implementations SET supported_method_ids = supported_method_ids || ';M_BOBYQA'
WHERE implementation_id = 'I_NLOPT';

INSERT INTO evidence_links (
  evidence_link_id, source_id, target_table, target_id, supported_field,
  claim_summary, evidence_role, confidence, last_verified
) VALUES
('EL004256', 'S145', 'methods', 'M_BOBYQA', 'row', '補間による二次modelとtrust regionで、上下限付きの関数を微分なしで最小化する。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004257', 'S018', 'methods', 'M_BOBYQA', 'row', 'NLoptがBOBYQA(LN_BOBYQA)を上下限付きの微分不要局所最適化として提供する。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004258', 'S146', 'methods', 'M_SAFEOPT', 'row', 'Gaussian processで安全領域を保ちながら探索し、到達可能な最適値への収束を示す。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004259', 'S147', 'methods', 'M_CONSTRAINED_BO', 'row', '目的と不等式制約の両方にGP事前分布を置くベイズ最適化。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004260', 'S148', 'methods', 'M_CONSTRAINED_BO', 'row', '未知の制約をGPでmodel化し、目的と制約を別々に評価できるベイズ最適化。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004261', 'S149', 'methods', 'M_PAREGO', 'row', '乱数の重みによるスカラー化とGPでPareto集合を近似する多目的最適化。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004262', 'S150', 'methods', 'M_SUBMODULAR_GREEDY', 'row', '単調劣モジュラ関数の濃度制約付き最大化で貪欲法が(1-1/e)近似を達成する。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004263', 'S151', 'methods', 'M_LEVELSET_TOPOLOGY', 'row', 'レベルセット関数で境界を表し、速度場で動かして位相変化を許す構造最適化。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004264', 'S152', 'methods', 'M_LEVELSET_TOPOLOGY', 'row', '形状微分とレベルセット法の組合せで弾性構造を最適化する。', 'supporting_or_primary', 'medium', '2026-10-10');
