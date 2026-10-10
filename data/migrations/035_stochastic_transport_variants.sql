-- Add sample average approximation, column-and-constraint generation, progressive hedging, stochastic dual dynamic programming
-- and the Sinkhorn algorithm (editorial scope TOPIC_SAA / TOPIC_CCG / TOPIC_PROGRESSIVE_HEDGING / TOPIC_SDDP / TOPIC_SINKHORN /
-- TOPIC_UNBALANCED_SINKHORN).
-- Placement, consistent with 032 (M_BENDERS in MF_DISCRETE_EXACT because it is a bound-and-gap master-cut scheme; M_DANTZIG_WOLFE in
-- MF_LP_QP_CONIC because it is an LP algorithm):
--   M_CCG       -> MF_DISCRETE_EXACT: a master/subproblem scheme with lower and upper bounds and a gap, the same kind as Benders.
--   M_SAA       -> MF_DISCRETE_EXACT: judgement call. No family is a natural fit (MF_STOCHASTIC_ML is mini-batch gradient methods); the primary
--                  source treats stochastic discrete optimization and the method reports statistical bounds and a gap, so it sits beside
--                  Benders, which already lists the two-stage stochastic LP in its problem classes. Maintainers may re-home it.
--   M_PROGRESSIVE_HEDGING -> MF_LP_QP_CONIC: scenario subproblems are LPs or QPs with a proximal term, coordinated by multiplier updates,
--                  the same pattern as M_ADMM_QP and M_DANTZIG_WOLFE in that family.
--   M_SDDP      -> MF_GRAPH_DP: a stage-wise dynamic-programming recursion (family definition: sequential / staged structure), beside
--                  M_DYNAMIC_PROGRAMMING; its Benders-type cuts are expressed by related_method_ids to M_BENDERS, not by a second parent.
--   M_SINKHORN  -> MF_LP_QP_CONIC: it solves the strictly convex entropy-regularized relaxation of the transport linear program by matrix
--                  scaling. There is no optimal-transport problem archetype (PA028 is Network flow); the transport LP itself is a min-cost
--                  flow, reached through related_method_ids to M_NETWORK_SIMPLEX, not through the family.
-- Unbalanced Sinkhorn (TOPIC_UNBALANCED_SINKHORN) is NOT its own row (docs/identity-granularity.md: a named variant is first an alias of the
-- parent row, and gets its own row only when assumptions, failures and recommendation differ and an article and comparison can show it). It
-- keeps the same scaling iteration with a divergence-relaxed marginal; it is kept as an alias, a terminology synonym, source S167 and text in
-- M_SINKHORN. The scope member maps variant_of -> M_SINKHORN.
-- Sinkhorn 1964 (Annals of Mathematical Statistics) was not confirmed against an official listing, so only Sinkhorn and Knopp 1967 is recorded.
-- No implementation rows: no existing implementation row has a confirmed API for these methods, and this batch adds none.
-- Problem archetypes PA049 (Stochastic programming) and PA050 (Robust optimization) exist; they are mentioned only here and in text, and
-- problem_method_fit is left unset.
PRAGMA foreign_keys = ON;

INSERT INTO sources (
  source_id, source_type, title, author_or_organization, publication_date,
  accessed_date, url, supported_claim, source_quality, notes, currentness_status
) VALUES
(
  'S160', 'original_paper',
  'The sample average approximation method for stochastic discrete optimization',
  'Anton J. Kleywegt; Alexander Shapiro; Tito Homem-de-Mello', '2002-01-01', '2026-10-10',
  'https://doi.org/10.1137/S1052623499363220',
  'Sample average approximation (SAA): the expectation is replaced by a sample average, the sampled problem is solved, and the procedure is repeated to obtain statistical lower and upper bounds, convergence rates and stopping rules; stated for stochastic discrete optimization.',
  'primary', 'SIAM Journal on Optimization 12, 479-502. Journal, volume and pages confirmed on 2026-10-10 by search against reference lists and the 1999 Stochastic Programming E-Print Series version (Humboldt-Universitat zu Berlin); the abstract of that version describes the Monte Carlo approach, convergence rates, stopping rules and a stochastic knapsack example. Year 2002 follows the usual SIAM listing; some reference lists give 2001. Issue number and the SIAM landing page were not confirmed from an official listing, so neither is recorded. DOI 10.1137/S1052623499363220 is the DOI already used in docs/research/uncertainty-method-source-audit.md.',
  'historical_primary'
),
(
  'S161', 'textbook',
  'Lectures on Stochastic Programming: Modeling and Theory',
  'Alexander Shapiro; Darinka Dentcheva; Andrzej Ruszczynski', '2009-01-01', '2026-10-10',
  'https://doi.org/10.1137/1.9780898718751',
  'Textbook treatment of stochastic programming: two-stage and multistage models, sample average approximation, risk-averse models, and decomposition methods including sampling-based dual dynamic programming.',
  'primary', 'SIAM and the Mathematical Programming Society, MPS-SIAM Series on Optimization 9, 2009, 436 pages, DOI 10.1137/1.9780898718751. Authors, series, year and DOI confirmed on 2026-10-10 against library catalog records via search; the first-edition table of contents was not available, so chapter-level claims are not recorded. A 2014 second edition and a 2021 third edition exist; this record is the first edition.',
  'historical_primary'
),
(
  'S162', 'original_paper',
  'Solving two-stage robust optimization problems using a column-and-constraint generation method',
  'Bo Zeng; Long Zhao', '2013-09-01', '2026-10-10',
  'https://doi.org/10.1016/j.orl.2013.05.003',
  'Column-and-constraint generation (C&CG) for two-stage robust optimization: a master problem is enlarged with recourse variables and constraints for scenarios found by a subproblem, giving lower and upper bounds.',
  'primary', 'Operations Research Letters 41(5), 457-461 (September 2013), Elsevier, DOI 10.1016/j.orl.2013.05.003. Journal, volume, issue, pages, year-month and DOI confirmed on 2026-10-10 against the CiNii record and the DOI as reported by search. The full text was not read; the claim is limited to the title and the commonly cited description of the method as the origin of C&CG.',
  'historical_primary'
),
(
  'S163', 'original_paper',
  'Scenarios and policy aggregation in optimization under uncertainty',
  'R. T. Rockafellar; Roger J.-B. Wets', '1991-02-01', '2026-10-10',
  'https://doi.org/10.1287/moor.16.1.119',
  'Progressive hedging (progressive hedging algorithm): scenario subproblems are solved separately and the scenario policies are aggregated so that decisions respect the information available (nonanticipativity).',
  'primary', 'Mathematics of Operations Research 16(1), 119-147 (February 1991), DOI 10.1287/moor.16.1.119. Journal, volume, issue, pages, month and DOI confirmed on 2026-10-10 against the INFORMS record (abstract) and the IAOR record via search; an earlier version is IIASA Working Paper WP-87-119 (December 1987). Only the abstract was available: it describes an algorithm that produces a policy for any weighting of the scenarios, grouped by available information, without reliance on hindsight. Convergence conditions were not read from the paper.',
  'historical_primary'
),
(
  'S164', 'original_paper',
  'Multi-stage stochastic optimization applied to energy planning',
  'M. V. F. Pereira; L. M. V. G. Pinto', '1991-01-01', '2026-10-10',
  'https://doi.org/10.1007/BF01582895',
  'Stochastic dual dynamic programming (SDDP): the expected cost-to-go functions of stochastic dynamic programming are approximated by piecewise linear functions built from stage dual solutions (Benders-type cuts), avoiding state-space discretization; applied to a 39-reservoir hydrothermal system.',
  'primary', 'Mathematical Programming 52(2), 359-375 (1991), Springer. Journal, volume, issue, pages and year confirmed on 2026-10-10 against dblp and the Springer citation listing via search; the abstract content (piecewise-linear cost-to-go from dual solutions acting as Benders cuts, 39 reservoirs) was confirmed against the IAOR record. The DOI 10.1007/BF01582895 is taken from the Springer link returned by search (link.springer.com/doi/10.1007/BF01582895); the page itself was not opened. The authors are listed as Pereira and Pinto; the middle initial of Pinto varies by listing and is not asserted. Month not confirmed, so the date is the year only.',
  'historical_primary'
),
(
  'S165', 'original_paper',
  'Sinkhorn distances: lightspeed computation of optimal transport',
  'Marco Cuturi', '2013-12-01', '2026-10-10',
  'https://papers.nips.cc/paper/2013/hash/af21d0c97db2e27e13572cbf59eb343d-Abstract.html',
  'Entropic regularization of the optimal transport problem makes the optimum computable by Sinkhorn matrix scaling, reported to be several orders of magnitude faster than standard transportation solvers for histograms of a few hundred dimensions or more.',
  'primary', 'Advances in Neural Information Processing Systems 26 (NIPS 2013; the conference is now named NeurIPS), proceedings page at papers.nips.cc confirmed on 2026-10-10 by search. The arXiv preprint 1306.0895 (June 2013) carries a slightly different title (optimal transportation distances). Pages were not confirmed and are not recorded; the proceedings month (December 2013) is the conference month and not an official publication date, so treat it as approximate.',
  'historical_primary'
),
(
  'S166', 'original_paper',
  'Concerning nonnegative matrices and doubly stochastic matrices',
  'Richard Sinkhorn; Paul Knopp', '1967-01-01', '2026-10-10',
  'https://projecteuclid.org/euclid.pjm/1102992505',
  'Matrix scaling: repeated row and column normalization of a nonnegative matrix with total support converges to a doubly stochastic matrix of the form D1 A D2 with positive diagonal D1, D2.',
  'primary', 'Pacific Journal of Mathematics 21(2), 343-348 (1967). Journal, volume, issue, pages and year confirmed on 2026-10-10 against the Project Euclid record via search (which lists the authors in reverse order; AMS and Mathematical Reviews give Sinkhorn first). The convergence statement is taken from reviews quoting the result; the full text was not read. Sinkhorn alone, A relationship between arbitrary positive matrices and doubly stochastic matrices, Annals of Mathematical Statistics 35 (1964), is the earlier origin but was not confirmed against an official listing in this batch, so it is not recorded.',
  'historical_primary'
),
(
  'S167', 'original_paper',
  'Scaling algorithms for unbalanced optimal transport problems',
  'Lenaic Chizat; Gabriel Peyre; Bernhard Schmitzer; Francois-Xavier Vialard', '2018-01-01', '2026-10-10',
  'https://doi.org/10.1090/mcom/3303',
  'Entropic-regularized unbalanced optimal transport, where the marginal constraints are relaxed by divergence penalties, is solved by generalized Sinkhorn scaling algorithms based on pointwise diagonal scaling of the coupling; also covers unbalanced barycenters and gradient flows.',
  'primary', 'Mathematics of Computation 87(314), 2563-2609 (2018). Journal, volume, pages and the four authors confirmed on 2026-10-10 against the AMS listing via search; issue 314 and DOI 10.1090/mcom/3303 come from a university repository record returned by search (the DOI page was not opened). Preprint: arXiv 1607.05816, first titled Scaling algorithms for unbalanced transport problems. Month not confirmed, so the date is the year only.',
  'historical_primary'
);

INSERT INTO methods (
  method_id, name_ja, name_en, aliases, method_family_id, method_level, summary, problem_classes, required_assumptions, derivative_information, variable_types, constraint_support, convex_fit, nonconvex_applicability, solution_scope, determinism, exactness, theoretical_guarantee, optimality_certificate, scalability, memory_tendency, per_iteration_cost, evaluation_pattern, parallelism, initialization_sensitivity, hyperparameter_sensitivity, scaling_sensitivity, noise_robustness, discontinuity_robustness, constraint_violation_handling, warm_start, online_use, strengths, weaknesses, typical_failures, avoid_conditions, first_choice_conditions, second_choice_conditions, switch_signals, beginner_level, tuning_difficulty, implementation_difficulty, explainability, stopping_criteria, diagnostic_metrics, related_method_ids, parent_method_id, child_method_ids, reference_source_ids, confidence, last_verified
) VALUES
(
  'M_SAA', '標本平均近似(SAA)', 'Sample average approximation (SAA)', 'sample average approximation;SAA;sample-average approximation;Monte Carlo sampling approximation', 'MF_DISCRETE_EXACT', 'variant', '期待値を含む確率計画を、N個の標本による標本平均に置き換えた決定的な近似問題として解き、標本を取り直して繰り返すことで解の候補と最適性ギャップの統計的な推定を得る方法。', 'stochastic_programming;two_stage_stochastic;stochastic_discrete_optimization', '目的や制約の期待値を、確率分布からの標本(独立同分布など)で近似できること。標本平均の問題を既存のソルバーで解けること。標本数が有限なので得られる値と解は確率的な近似であり、固定した標本での値をそのまま真の最適値とは読まない。', 'unknown', 'continuous;integer;mixed', 'model_dependent', 'model_dependent', 'model_dependent', 'global_candidate', 'deterministic', 'statistical', '元論文は、標本数を増やしたときの収束の速さ、停止規則、および独立な標本の繰り返しによる最適値の統計的な下界・上界とギャップ推定を扱う(Kleywegt, Shapiro, Homem-de-Mello)。保証は標本の独立性や問題の構造(離散・凸など)に依存し、固定した標本数での解の最適性は保証されない。', 'statistical_gap_estimate_not_certificate', 'sample_size_and_model_dependent', 'grows_with_sample_size', '標本数Nの決定的な近似問題を1回解くコスト(標本を取り直して複数回繰り返す)。', '標本生成 -> 標本平均問題を解く -> 別の標本で解を評価して上下界を推定、の繰り返し。', 'replications_parallel', 'sample_dependent', 'sample_size_dependent', 'model_dependent', 'statistical_estimate', 'model_dependent', 'sampled_constraints_only', 'conditional', 'no', '確率計画を既存の決定的ソルバー(LP・MILPなど)に載せられる;標本数を増やすと近似が改善する;複数回の繰り返しで解の質の統計的な評価ができる', '標本数に対して問題が大きくなる;得られる最適値は標本に依存し、有限標本の解は最適とは限らない;ギャップは統計的な推定で証明ではない', 'too_few_samples;sample_bias;optimistic_in_sample_value;large_scale_sample_problem', '分布の標本が得られない(分布が不明でデータも少ない);標本数が足りず分散が大きい;最悪ケースの保証が必要(ロバスト最適化を検討)', '期待値の最小化として書ける確率計画で、標本が取れ、標本数に見合う決定的な問題をソルバーが解ける。', '標本数が増えて近似問題が解けなくなる(分解法を検討);シナリオ木が小さく明示できる。', '標本を変えると解が大きく変わる;近似問題が大きすぎて解けない;最悪ケースに対する保証が必要。', 'high', 'medium', 'medium', 'high', 'statistical_gap_estimate;sample_size_budget;replication_count', 'sample_average_objective;lower_bound_estimate;upper_bound_estimate;gap_estimate;solution_variability_across_replications', 'M_BENDERS;M_PROGRESSIVE_HEDGING;M_SDDP;M_CCG', 'MF_DISCRETE_EXACT', '', 'S160;S161', 'medium', '2026-10-10'
),
(
  'M_CCG', '列・制約生成法(二段階ロバスト最適化)', 'Column-and-constraint generation (two-stage robust optimization)', 'column-and-constraint generation;C&CG;CCG;column and constraint generation', 'MF_DISCRETE_EXACT', 'variant', '二段階ロバスト最適化を、最悪ケースの不確実性を見つけるsubproblemと、見つかったシナリオごとの再計算変数と制約をmasterへ足していく反復で解く方法。masterの下界とsubproblemの上界で収束を判定する。', 'two_stage_robust_optimization;adjustable_robust;robust_MILP', '不確実性集合が与えられ(多面体など)、第二段階の再計算(recourse)が最悪ケースの探索subproblemとして解けること。第二段階が不確実性の実現値によらず実行可能であること(相対完備)などの条件は、この出典の範囲を超えて一般に付く。', 'model_coefficients', 'continuous;integer;mixed', 'linear;model_dependent', 'model_dependent', 'model_dependent', 'global_certificate', 'deterministic', 'exact_with_tolerance', '元論文は、二段階ロバスト問題に対して列と制約を生成するmaster/subproblemの反復を与え、下界と上界を得る手続きを示す(Zeng and Zhao 2013)。有限回での収束は不確実性集合が有限個の極点で表せるなどの条件に依存する(出典の全文は未確認のため詳細な条件は記録しない)。', 'master下界とsubproblem上界のgap', 'instance_dependent', 'master_grows_with_scenarios', 'masterの求解(MILPになりうる)とsubproblem(最悪ケース探索、双線形・MILPになりうる)の求解。', 'master解 -> subproblemで最悪ケース探索 -> 列と制約をmasterへ追加、の反復。', 'limited', 'low', 'low', 'medium', 'not_applicable_input_data_sensitivity', 'not_applicable', 'worst_case_feasibility', 'yes_for_added_scenarios', 'no', '最悪ケースに対する保証つきの解が得られる;masterに再計算変数と制約を足していく;下界と上界で収束が判断できる', 'subproblemが双線形やMILPで難しくなりうる;反復ごとにmasterが大きくなる;不確実性集合の設定に結果が強く依存する', 'hard_worst_case_subproblem;master_growth;infeasible_recourse;conservative_uncertainty_set', '確率分布が使え期待値で評価したい(確率計画を検討);不確実性集合を設定する根拠がない;二段階でない問題', '不確実性集合が与えられた二段階ロバスト最適化(容量・立地・電力系統運用など)で、最悪ケースの探索を厳密に解ける。', '再計算を簡略化した近似(affine decision rule など)で足りる;期待値評価の確率計画で足りる。', 'subproblemが解けない;masterが急速に大きくなる;解が保守的すぎる。', 'low', 'low', 'high', 'medium', 'lower_upper_bound_gap;no_violating_scenario', 'master_lower_bound;subproblem_upper_bound;gap;generated_scenarios;worst_case_scenario', 'M_BENDERS;M_SAA;M_BRANCH_BOUND', 'MF_DISCRETE_EXACT', '', 'S162', 'medium', '2026-10-10'
),
(
  'M_PROGRESSIVE_HEDGING', 'Progressive hedging法', 'Progressive hedging', 'progressive hedging;progressive hedging algorithm;PHA;scenario decomposition;policy aggregation', 'MF_LP_QP_CONIC', 'variant', '確率計画をシナリオごとの部分問題に分け、各シナリオの解を情報構造(非予測性)に沿って集約・調整する反復で、全シナリオに共通の第一段階決定へ収束させるシナリオ分解法。', 'stochastic_programming;multistage_stochastic;scenario_based', '有限個のシナリオで表された確率計画で、非予測性(同じ情報のシナリオは同じ決定)を等式制約として分離できること。シナリオごとの部分問題を(罰則項つきで)解けること。', 'model_coefficients', 'continuous;integer;mixed', 'linear;convex;nonanticipativity', 'primary', 'heuristic_for_nonconvex_or_integer', 'convex_global', 'deterministic', 'exact_with_tolerance', '元論文は、シナリオごとの方策を情報に沿って集約し、ヘッジした方策を得るアルゴリズムを与える(Rockafellar and Wets 1991。要旨のみ確認)。収束の条件(凸性など)は本文を未確認のため記録しない。整数変数を含む場合の最適性は一般に保証されず、heuristicとして使われる(出典の範囲外の一般的な注意)。', 'non_anticipativity_residual', 'high_by_scenario_decomposition', 'low_to_medium', 'シナリオごとの部分問題(罰則項つき)の求解と、非予測性のための平均化・乗数更新。', 'シナリオ部分問題 -> 平均化(集約) -> 乗数と罰則の更新、の反復。', 'scenario_parallel', 'medium', 'penalty_parameter_sensitive', 'medium', 'not_applicable_input_data_sensitivity', 'not_applicable', 'nonanticipativity_residual', 'yes', 'no', 'シナリオごとに並列に解ける;シナリオ数が多い確率計画を分解して扱える;各反復の部分問題が元の決定的問題と同じ形で既存のソルバーを使える', '罰則パラメータの調整で収束速度が大きく変わる;整数変数を含むと収束や最適性が保証されない;収束が遅くなることがある', 'poor_penalty_parameter;slow_convergence;cycling_with_integer_variables;nonanticipativity_not_met', 'シナリオ数が少なく拡大した決定的等価問題を直接解ける;最悪ケースの保証が必要(ロバスト最適化を検討)', 'シナリオ数が多く、シナリオ別の部分問題が既存ソルバーで解け、並列に実行できる多段階の確率計画。', '決定的等価問題を直接解ける規模(分解不要);段構造を使うBenders型・SDDPが適する。', '非予測性の残差が減らない;罰則パラメータの調整に時間がかかる;整数変数で収束しない。', 'low', 'high', 'medium', 'medium', 'nonanticipativity_residual_tolerance;iteration_limit', 'nonanticipativity_residual;penalty_parameter;scenario_objective_spread;dual_multiplier_change', 'M_ADMM_QP;M_AUGMENTED_LAGRANGIAN;M_BENDERS;M_SAA;M_SDDP', 'MF_LP_QP_CONIC', '', 'S163;S161', 'medium', '2026-10-10'
),
(
  'M_SDDP', '確率的双対動的計画(SDDP)', 'Stochastic dual dynamic programming (SDDP)', 'stochastic dual dynamic programming;SDDP;dual dynamic programming;Pereira-Pinto algorithm', 'MF_GRAPH_DP', 'variant', '多段階確率計画を段ごとのDPとして扱い、将来費用関数を、各段の双対解から作る区分線形の下近似(Benders型のcut)で表し、標本化した前進計算と後退計算の反復で改善する方法。', 'multistage_stochastic_programming;hydrothermal_scheduling;energy_planning', '段ごとの問題が凸(線形計画など)で双対解が取れ、将来費用関数が凸になること。不確実性が段間で独立など、状態が少数の変数に縮約できる構造(出典のエネルギー計画の設定)。状態次元が非常に大きいとcut数が増える。', 'dual_solutions', 'continuous', 'linear;convex', 'primary', 'not_applicable_without_convexity', 'convex_global', 'deterministic', 'approximation', '元論文は、期待将来費用関数を段ごとの双対解から作る区分線形関数で近似し、状態の離散化を避ける方法を示す(Pereira and Pinto 1991)。この出典は39貯水池の水力火力系での適用を示すもので、有限収束の厳密な定理や統計的上界の保証は、この記録の範囲外とする。', 'cut由来の下界と標本由来の統計的上界', 'state_dimension_dependent', 'cuts_accumulate', '前進計算(標本経路)と後退計算(段ごとのLP求解とcut生成)。', '標本経路の前進計算 -> 逆順に段ごとのLPを解いてcutを追加、の反復。', 'scenario_path_parallel', 'low', 'sampling_and_cut_selection_dependent', 'medium', 'statistical_upper_bound', 'not_applicable', 'feasibility_cuts', 'yes_for_added_cuts', 'conditional', '状態を離散化せずに多段階の確率計画を扱える;段ごとのLPに分解して既存のLPソルバーを使える;下界が単調に改善する', '状態次元が大きいとcutが膨大になる;凸性(段問題が線形・凸)が必要;整数変数を含む段問題はそのままでは扱えない', 'cut_explosion;slow_convergence;nonconvex_stage_problem;statistical_upper_bound_noise', '段の問題が非凸・整数で凸近似が使えない;状態次元が非常に大きくcutが増えすぎる;段数が少なく決定的等価問題を直接解ける', '水力発電計画など、段数が多く各段が線形の凸な多段階確率計画。', '段数が少ない(二段階ならBenders型・SAA);シナリオ分解が適する(progressive hedging)。', 'cut数が増え続ける;上界と下界のギャップが縮まらない;段問題が非凸になる。', 'low', 'medium', 'high', 'medium', 'bound_gap_tolerance;statistical_convergence_test;iteration_limit', 'lower_bound;statistical_upper_bound;cuts_per_stage;forward_cost_variance', 'M_DYNAMIC_PROGRAMMING;M_BENDERS;M_SAA;M_PROGRESSIVE_HEDGING', 'MF_GRAPH_DP', '', 'S164;S161', 'medium', '2026-10-10'
),
(
  'M_SINKHORN', 'Sinkhorn法', 'Sinkhorn algorithm (entropic optimal transport)', 'Sinkhorn;Sinkhorn-Knopp;Sinkhorn iterations;Sinkhorn algorithm;matrix scaling;entropic optimal transport;unbalanced Sinkhorn;unbalanced optimal transport scaling', 'MF_LP_QP_CONIC', 'variant', 'エントロピー正則化した最適輸送問題の解が行・列のスケーリング行列で書けることを使い、行方向と列方向の正規化を交互に繰り返して輸送計画を求める行列スケーリング法。周辺分布の制約を発散(KL)で緩めた非均衡版も同じ形のスケーリング反復で解く。', 'optimal_transport;entropic_optimal_transport;unbalanced_optimal_transport;matrix_scaling', 'ソース分布とターゲット分布(ヒストグラム)および費用行列があり、エントロピー正則化の重みε>0を与えること。行列スケーリングの収束には、行列が非負で全支持(total support)などの条件が要る(Sinkhorn and Knopp)。εが小さいと数値的に不安定になり、対数領域の計算などが必要になる(出典の範囲外の一般的な注意)。非均衡版では質量が一致しなくてよいが、周辺の緩和の重みを追加で決める。', 'none', 'continuous', 'marginal_equalities;marginal_divergence_penalty_in_unbalanced', 'primary', 'not_applicable', 'convex_global', 'deterministic', 'approximation', 'Sinkhorn and Knopp(1967)は、全支持を持つ非負行列の行・列正規化の反復が二重確率行列へ収束することを示した(レビュー経由の確認で、本文は未確認)。Cuturi(2013)は、エントロピー正則化した輸送問題をこの行列スケーリングで解く方法を示し、標準の輸送ソルバーより桁違いに高速と報告している。得られる輸送計画は正則化問題の解であり、元の輸送問題(LP)の最適解の近似でありεに依存する。Chizat et al.(2018)は、周辺制約を発散で緩めた非均衡輸送の正則化問題に、点ごとの対角スケーリングに基づく一般化したSinkhornアルゴリズムを与えた。', 'marginal_constraint_residual', 'high_for_dense_cost_matrices_by_matrix_vector_products', 'medium_dense_kernel_matrix', 'カーネル行列と双対スケーリングベクトルの行列ベクトル積(密な場合は次元の2乗程度)。', '行スケーリングの更新と列スケーリングの更新の交互反復。', 'high_by_matrix_vector_products', 'low', 'regularization_weight_sensitive', 'cost_scale_and_epsilon_sensitive', 'not_applicable_input_data_sensitivity', 'not_applicable', 'marginal_residual_tolerance', 'yes_by_dual_scalings', 'conditional', '行列ベクトル積だけで実装でき、GPUや並列化に向く;微分可能で学習の損失(Sinkhorn距離)として使える;正則化により滑らかな問題になる', 'εを小さくすると収束が遅くなり数値的に不安定になる;輸送計画が密になり、元のLPの疎な解とは異なる;正則化のバイアスがある', 'numerical_underflow_small_epsilon;slow_convergence_small_epsilon;dense_plan_instead_of_sparse;marginal_residual_not_reached', '疎で厳密な輸送計画が必要(輸送LP・network simplexを検討);εを小さくしないと精度が出ない大規模問題で対数領域の実装がない', 'ヒストグラム間の輸送距離を大量に計算する、または学習の損失として微分可能な輸送コストが要る問題。', '小〜中規模で厳密な輸送LP解が欲しい(M_NETWORK_SIMPLEXなど);ε依存のバイアスが許されない。', 'εを下げると反復が収束しない;計画が密すぎて使えない;質量が一致しない分布を扱いたい(非均衡版)。', 'medium', 'medium', 'low', 'medium', 'marginal_residual_tolerance;iteration_limit', 'marginal_violation;dual_scaling_change;regularized_cost;epsilon', 'M_NETWORK_SIMPLEX;M_ADMM_QP', 'MF_LP_QP_CONIC', '', 'S165;S166;S167', 'medium', '2026-10-10'
);

UPDATE methods
SET child_method_ids = 'M_BRANCH_BOUND;M_BRANCH_CUT;M_OUTER_APPROX_MINLP;M_SPATIAL_BRANCH_BOUND;M_BENDERS;M_BRANCH_PRICE;M_BRANCH_PRICE_CUT;M_SAA;M_CCG'
WHERE method_id = 'MF_DISCRETE_EXACT';
UPDATE methods
SET child_method_ids = 'M_SIMPLEX;M_DUAL_SIMPLEX;M_BARRIER_LP_QP;M_PDLP;M_ACTIVE_SET_QP;M_ADMM_QP;M_PRIMAL_DUAL_CONIC;M_DANTZIG_WOLFE;M_COLUMN_GENERATION;M_PROGRESSIVE_HEDGING;M_SINKHORN'
WHERE method_id = 'MF_LP_QP_CONIC';
UPDATE methods
SET child_method_ids = 'M_DYNAMIC_PROGRAMMING;M_NETWORK_SIMPLEX;M_HUNGARIAN;M_DIJKSTRA_ASTAR;M_LOCAL_SEARCH_COMBINATORIAL;M_BELLMAN_FORD;M_AUGMENTING_MAXFLOW;M_PUSH_RELABEL;M_SUCCESSIVE_SHORTEST_PATH;M_SDDP'
WHERE method_id = 'MF_GRAPH_DP';

INSERT INTO method_hierarchy (
  hierarchy_id, parent_method_id, child_method_id, relation_type, depth,
  is_primary_parent, rationale, source_ids, confidence, last_verified
) VALUES
('MH_DISCRETE_EXACT_SAA', 'MF_DISCRETE_EXACT', 'M_SAA', 'is_a', 1, 'yes', 'Sample average approximation reduces a stochastic program to sampled problems solved with bound-and-gap style statistical estimates; placed with Benders under Exact discrete and mixed-integer optimization because its primary source is stochastic discrete optimization.', 'S160;S161', 'medium', '2026-10-10'),
('MH_DISCRETE_EXACT_CCG', 'MF_DISCRETE_EXACT', 'M_CCG', 'is_a', 1, 'yes', 'Column-and-constraint generation is a master-subproblem scheme with lower and upper bounds, classified with Benders decomposition under Exact discrete and mixed-integer optimization.', 'S162', 'medium', '2026-10-10'),
('MH_LP_QP_CONIC_PROGRESSIVE_HEDGING', 'MF_LP_QP_CONIC', 'M_PROGRESSIVE_HEDGING', 'is_a', 1, 'yes', 'Progressive hedging splits a stochastic program into scenario subproblems (LP or QP with a proximal term) coordinated by multiplier updates, classified with ADMM and Dantzig-Wolfe decomposition.', 'S163;S161', 'medium', '2026-10-10'),
('MH_GRAPH_DP_SDDP', 'MF_GRAPH_DP', 'M_SDDP', 'is_a', 1, 'yes', 'Stochastic dual dynamic programming is a stage-wise dynamic-programming recursion with cut-approximated cost-to-go functions, classified beside dynamic programming.', 'S164;S161', 'medium', '2026-10-10'),
('MH_LP_QP_CONIC_SINKHORN', 'MF_LP_QP_CONIC', 'M_SINKHORN', 'is_a', 1, 'yes', 'Sinkhorn iterations solve the entropy-regularized (strictly convex) relaxation of the transport linear program by matrix scaling; the unbalanced variant is kept in the same row.', 'S165;S166;S167', 'medium', '2026-10-10');

INSERT INTO terminology_aliases (
  term_id, target_type, target_id, label_ja, label_en, abbreviations_json,
  synonyms_json, domain_terms_json, misspellings_json, deprecated_terms_json,
  disambiguation_note, locale, rationale, source_ids_json, last_verified
) VALUES
('TERM_SAA', 'method', 'M_SAA', '標本平均近似', 'Sample average approximation', '["SAA"]',
 '["sample-average approximation","Monte Carlo sampling approximation"]', '["標本平均問題","統計的ギャップ推定"]', '[]', '[]',
 '確率的勾配法(SGD)や確率近似(stochastic approximation, SPSAなど)とは別。SAAは標本を固定して決定的な問題を解く。機械学習の経験リスク最小化は同じ発想の特別な場合。SAASBO(ベイズ最適化)とは無関係。', 'ja-JP,en',
 '略称と名称をmethodへ解決する。', '["S160", "S161"]', '2026-10-10'),
('TERM_CCG', 'method', 'M_CCG', '列・制約生成法', 'Column-and-constraint generation', '["C&CG","CCG"]',
 '["column and constraint generation"]', '["二段階ロバスト最適化","最悪ケースsubproblem"]', '[]', '[]',
 '列生成(M_COLUMN_GENERATION)やBenders分解とは別。列生成はLPの列を足し、C&CGは再計算変数と制約を足す。略称CCGは共役勾配(CG)と無関係。', 'ja-JP,en',
 '名称と略称をmethodへ解決する。', '["S162"]', '2026-10-10'),
('TERM_PROGRESSIVE_HEDGING', 'method', 'M_PROGRESSIVE_HEDGING', 'Progressive hedging法', 'Progressive hedging', '["PHA"]',
 '["progressive hedging algorithm","scenario decomposition","policy aggregation"]', '["非予測性","シナリオ分解"]', '[]', '[]',
 'Benders型の分解(段で分ける)とは別で、シナリオで分ける分解。ADMMと同じく罰則つきの調整反復を使う。', 'ja-JP,en',
 '名称と別名をmethodへ解決する。', '["S163"]', '2026-10-10'),
('TERM_SDDP', 'method', 'M_SDDP', '確率的双対動的計画', 'Stochastic dual dynamic programming', '["SDDP"]',
 '["dual dynamic programming","Pereira-Pinto algorithm"]', '["多段階確率計画","将来費用関数","水力発電計画"]', '[]', '[]',
 '通常の動的計画法(M_DYNAMIC_PROGRAMMING、状態を離散化する)とは別。SDDPは将来費用関数をcutで近似する。', 'ja-JP,en',
 '名称と略称をmethodへ解決する。', '["S164"]', '2026-10-10'),
('TERM_SINKHORN', 'method', 'M_SINKHORN', 'Sinkhorn法', 'Sinkhorn algorithm', '[]',
 '["Sinkhorn-Knopp","Sinkhorn iterations","matrix scaling","entropic optimal transport","unbalanced Sinkhorn"]', '["エントロピー正則化","行列スケーリング","Sinkhorn距離","非均衡最適輸送"]', '[]', '[]',
 '輸送LPを厳密に解くnetwork simplexなどとは別。Sinkhorn法の解はε依存の正則化解。非均衡Sinkhorn法は同じ行の変種で、周辺制約を発散で緩める(別行にしない)。', 'ja-JP,en',
 '名称と変種名をmethodへ解決する。', '["S165", "S166", "S167"]', '2026-10-10');

INSERT INTO evidence_links (
  evidence_link_id, source_id, target_table, target_id, supported_field,
  claim_summary, evidence_role, confidence, last_verified
) VALUES
('EL004280', 'S160', 'methods', 'M_SAA', 'row', '期待値を標本平均に置き換えた近似問題を解き、繰り返しで統計的なギャップを推定する。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004281', 'S161', 'methods', 'M_SAA', 'row', '期待値を標本平均に置き換えた近似問題を解き、繰り返しで統計的なギャップを推定する。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004282', 'S162', 'methods', 'M_CCG', 'row', '最悪ケースのシナリオに対する列と制約をmasterへ足して二段階ロバスト問題を解く。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004283', 'S163', 'methods', 'M_PROGRESSIVE_HEDGING', 'row', 'シナリオごとの解を情報構造に沿って集約する分解法。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004284', 'S161', 'methods', 'M_PROGRESSIVE_HEDGING', 'row', 'シナリオごとの解を情報構造に沿って集約する分解法。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004285', 'S164', 'methods', 'M_SDDP', 'row', '双対解から作る区分線形のcutで将来費用関数を近似する多段階確率計画の手法。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004286', 'S161', 'methods', 'M_SDDP', 'row', '双対解から作る区分線形のcutで将来費用関数を近似する多段階確率計画の手法。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004287', 'S165', 'methods', 'M_SINKHORN', 'row', 'エントロピー正則化した最適輸送を行列スケーリングで解く。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004288', 'S166', 'methods', 'M_SINKHORN', 'row', 'エントロピー正則化した最適輸送を行列スケーリングで解く。', 'supporting_or_primary', 'medium', '2026-10-10'),
('EL004289', 'S167', 'methods', 'M_SINKHORN', 'row', '周辺制約を緩めた非均衡輸送も一般化したスケーリング反復で解く。', 'supporting_or_primary', 'medium', '2026-10-10');
