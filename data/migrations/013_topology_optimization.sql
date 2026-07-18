PRAGMA foreign_keys = ON;

INSERT INTO sources (
  source_id, source_type, title, author_or_organization, publication_date,
  accessed_date, url, supported_claim, source_quality, notes, currentness_status
) VALUES
(
  'S097', 'original_paper',
  'A 99 line topology optimization code written in MATLAB',
  'Ole Sigmund', '2001-04-01', '2026-07-18',
  'https://doi.org/10.1007/s001580050176',
  'Educational density-based compliance topology optimization with finite elements, sensitivity filtering, and an Optimality Criteria update.',
  'primary', 'Original paper for the compact educational compliance topology-optimization loop.',
  'historical_primary'
),
(
  'S098', 'official_documentation',
  'A 99 line topology optimization code written in MATLAB',
  'Technical University of Denmark TopOpt', NULL, '2026-07-18',
  'https://www.topopt.mek.dtu.dk/apps-and-software/a-99-line-topology-optimization-code-written-in-matlab',
  'Maintainer-hosted educational implementation and scope of the 99-line compliance example.',
  'primary', 'Official TopOpt educational page; the downloadable code is not copied into this repository.',
  'verified_current'
),
(
  'S099', 'official_documentation',
  'Efficient topology optimization in MATLAB',
  'Technical University of Denmark TopOpt', NULL, '2026-07-18',
  'https://www.topopt.mek.dtu.dk/apps-and-software/efficient-topology-optimization-in-matlab',
  'Density filtering, projection filtering, and the educational top88/top110 family.',
  'primary', 'Official TopOpt page describing the 88-line code and filtering extensions.',
  'verified_current'
),
(
  'S100', 'original_paper',
  'The method of moving asymptotes—a new method for structural optimization',
  'Krister Svanberg', '1987-02-01', '2026-07-18',
  'https://doi.org/10.1002/nme.1620240207',
  'MMA uses strictly convex approximating subproblems controlled by moving asymptotes.',
  'primary', 'Original MMA paper.',
  'historical_primary'
),
(
  'S101', 'official_documentation',
  'Mathematical background: adjoints and their applications',
  'dolfin-adjoint project', NULL, '2026-07-18',
  'https://www.dolfin-adjoint.org/en/latest/documentation/maths/',
  'Adjoint equations and reduced sensitivities for PDE-constrained optimization.',
  'primary', 'Official project documentation used for the state/adjoint explanation.',
  'verified_current'
);

INSERT INTO methods (
  method_id, name_ja, name_en, aliases, method_family_id, method_level, summary,
  problem_classes, required_assumptions, derivative_information, variable_types,
  constraint_support, convex_fit, nonconvex_applicability, solution_scope,
  determinism, exactness, theoretical_guarantee, optimality_certificate,
  scalability, memory_tendency, per_iteration_cost, evaluation_pattern,
  parallelism, initialization_sensitivity, hyperparameter_sensitivity,
  scaling_sensitivity, noise_robustness, discontinuity_robustness,
  constraint_violation_handling, warm_start, online_use, strengths, weaknesses,
  typical_failures, avoid_conditions, first_choice_conditions,
  second_choice_conditions, switch_signals, beginner_level, tuning_difficulty,
  implementation_difficulty, explainability, stopping_criteria,
  diagnostic_metrics, related_method_ids, parent_method_id, child_method_ids,
  reference_source_ids, confidence, last_verified
) VALUES
(
  'MF_TOPOLOGY_OPTIMIZATION', '構造トポロジー最適化', 'Structural topology optimization',
  'topology optimization;structural optimization;TO', 'MF_TOPOLOGY_OPTIMIZATION', 'family',
  '材料の分布や形状を設計変数にし、状態方程式を解きながら性能と体積などの制約を調整する手法群。',
  'topology_optimization;pde_constrained;structural_design',
  '設計領域、物理model、境界条件、材料model、制約、離散化を明示する。',
  'analytic_gradient;adjoint;automatic_differentiation;finite_difference', 'field;shape',
  'integral;state;bounds', 'weak', 'yes_local_only', 'local', 'deterministic',
  'local_numerical', '離散化・緩和・更新則に依存する局所的な数値解であり、連続問題の大域解を保証しない。',
  'feasibility;stationarity;mesh_independence_diagnostics', 'high_with_sparse_state_solve',
  'high', '状態solveと感度計算が支配的。', '各updateでstate equation、objective、sensitivityを評価する。',
  'sparse_linear_algebra;distributed', 'medium', 'high', 'very_high', 'low', 'low',
  'filter;projection;penalty;conservative_approximation', 'conditional', 'no',
  'field-valued designとphysicsを一つのloopで表せる。', 'mesh・model・constraint・updateの組合せに敏感。',
  'checkerboard;gray_density;mesh_dependence;singular_state_system',
  'continuous guaranteeやmanufacturing feasibilityを無注釈で主張する場合。',
  'state solve、感度、制約、discretizationを同時に検査できる小さなreference case。',
  '高価なstate solveや非滑らかな製造制約が支配する場合は専用のformulationを比較する。',
  'volume/compliance停滞;checkerboard;gray_fraction増大;state solve failure', 'medium', 'high',
  'high', 'high', 'max_iterations;volume_tolerance;stationarity;state_residual',
  'compliance;volume_fraction;gray_fraction;checkerboard_score;sensitivity_norm;state_residual',
  '', NULL, 'M_SIMP_TOPOLOGY;M_DENSITY_FILTER;M_OC_TOPOLOGY;M_MMA;M_ADJOINT_SENSITIVITY',
  'S097;S099;S100;S101', 'high', '2026-07-18'
),
(
  'M_SIMP_TOPOLOGY', 'SIMP密度法', 'SIMP density method',
  'SIMP;solid isotropic material with penalization;density-based topology optimization',
  'MF_TOPOLOGY_OPTIMIZATION', 'variant',
  '各有限要素の密度を連続変数として扱い、剛性を密度のべき乗で補間するdensity-based topology optimization。',
  'topology_optimization;linear_elasticity;pde_constrained',
  '線形弾性state solve、材料補間、設計密度の上下限、volume constraintを定義する。',
  'analytic_gradient;adjoint', 'field', 'integral;bounds;state', 'weak', 'yes_local_only', 'local',
  'deterministic', 'local_numerical', 'SIMPは0/1 topologyそのものではなく、連続緩和とpenalizationである。',
  'volume_feasibility;stationarity', 'high_with_sparse_fem', 'high', 'FEM state solveと感度計算。',
  'iterationごとにFEM、compliance、element sensitivityを評価する。', 'sparse_linear_algebra',
  'medium', 'high', 'very_high', 'low', 'low', 'density_filter;projection;volume_correction',
  'conditional', 'no', 'field variableを既存の有限要素loopに接続しやすい。',
  '中間密度、mesh dependence、local solution、gray regionが残る。',
  'checkerboard;gray_density;singular_stiffness', 'stress・buckling・manufacturing制約だけをcompliance modelで代表する場合。',
  'compliance minimizationの最初のeducational formulation。', 'filterやprojectionの挙動を別々に検証する。',
  'volumeが合わない;gray_fractionが下がらない;meshを変えるとtopologyが変わる。', 'beginner', 'high',
  'medium', 'high', 'max_iterations;volume_tolerance;state_residual',
  'compliance;volume_fraction;gray_fraction;checkerboard_score', 'M_DENSITY_FILTER;M_OC_TOPOLOGY',
  'MF_TOPOLOGY_OPTIMIZATION', '', 'S097;S098;S099', 'high', '2026-07-18'
),
(
  'M_DENSITY_FILTER', '密度・感度filter', 'Density and sensitivity filtering',
  'density filter;sensitivity filter;mesh-independency filter', 'MF_TOPOLOGY_OPTIMIZATION', 'variant',
  '近傍要素の密度または感度を平滑化し、checkerboardと過度に細かい構造を抑える正則化手法。',
  'topology_optimization;regularization', 'mesh上の近傍、filter radius、weight、volumeの定義が必要。',
  'analytic_gradient', 'field', 'integral;bounds', 'weak', 'yes_local_only', 'local', 'deterministic',
  'local_numerical', 'filterは物理的なmanufacturing constraintやmesh independenceを単独で保証しない。',
  'filter_radius_sensitivity;minimum_length_diagnostic', 'very_high', 'low', '近傍重みの集計。',
  'update前のdensityまたはsensitivityを変換する。', 'parallel_array_operations', 'low', 'medium',
  'medium', 'low', 'low', 'explicit_filter;projection', 'conditional', 'no',
  'checkerboardを見えるfailure signalに変えられる。', 'radiusと境界処理に依存し、細部を消しすぎる場合がある。',
  'checkerboard;over_smoothed_design;boundary_artifact', '最小feature sizeを別の工程で保証できると誤認する場合。',
  'mesh sensitivityの診断とともに使う。', 'PDE filterやrobust formulationを比較する。',
  'checkerboard_scoreが下がらない;gray regionが増える;complianceが悪化しすぎる。', 'beginner', 'medium',
  'medium', 'high', 'filter_radius;mesh_refinement;gray_fraction',
  'checkerboard_score;gray_fraction;minimum_feature_diagnostic', 'M_SIMP_TOPOLOGY',
  'MF_TOPOLOGY_OPTIMIZATION', '', 'S097;S099', 'high', '2026-07-18'
),
(
  'M_OC_TOPOLOGY', 'Optimality Criteria更新', 'Optimality Criteria update',
  'OC;optimality criteria;optimality criteria method', 'MF_TOPOLOGY_OPTIMIZATION', 'variant',
  'complianceの感度とvolume制約のKKT条件を使い、move limitと二分法で密度を更新する構造最適化向けの更新則。',
  'topology_optimization;structural_design', '密度の上下限、volume constraint、感度の符号とstate solveが必要。',
  'analytic_gradient;adjoint', 'field', 'integral;bounds', 'weak', 'yes_local_only', 'local', 'deterministic',
  'local_numerical', 'KKT条件への近づき方は離散化・filter・move limitに依存し、大域最適性は保証しない。',
  'volume_feasibility;stationarity', 'very_high', 'low', '感度集計と密度field全体のbounded update。',
  '毎反復でstate・sensitivityを1回ずつ評価する。', 'parallel_array_operations', 'medium', 'high',
  'very_high', 'low', 'low', 'move_limit;volume_bisection', 'yes', 'no',
  'compliance topology optimizationの教材で動きを説明しやすい。', '局所解、move limit依存、非標準制約への拡張が必要。',
  'volume_oscillation;gray_density;checkerboard', '非線形・stress・buckling制約をvolumeだけで置き換える場合。',
  'SIMP complianceとvolume constraintが主役の小規模case。', 'MMAや専用制約法を比較する。',
  'volumeが振動;compliance停滞;move limitが常にactive。', 'beginner', 'medium', 'medium', 'high',
  'max_iterations;volume_tolerance;stationarity', 'compliance;volume_fraction;gray_fraction;move_limit_active',
  'M_SIMP_TOPOLOGY;M_MMA', 'MF_TOPOLOGY_OPTIMIZATION', '', 'S097;S098', 'high', '2026-07-18'
),
(
  'M_MMA', '移動漸近線法', 'Method of Moving Asymptotes',
  'MMA;method of moving asymptotes', 'MF_TOPOLOGY_OPTIMIZATION', 'variant',
  '各反復で漸近線を動かしながらstrictly convexな近似部分問題を解く更新法。',
  'topology_optimization;nonlinear_programming;structural_design',
  '目的・制約の感度、変数の上下限、近似部分問題、asymptote更新を定義する。',
  'analytic_gradient;adjoint', 'field', 'integral;bounds;state', 'weak', 'yes_local_only', 'local',
  'deterministic', 'local_numerical', '凸近似部分問題の性質は説明できるが、元の非凸topology問題の大域解を保証しない。',
  'KKT_residual;volume_feasibility', 'high_with_sparse_state_solve', 'high', '近似部分問題とstate solve。',
  '各反復でstate、感度、近似部分問題を評価する。', 'parallel_array_operations;sparse_linear_algebra',
  'medium', 'high', 'very_high', 'low', 'low', 'conservative_convex_approximation', 'yes', 'no',
  '複数の制約や非線形性を扱う枠組みを持つ。', 'asymptoteとscaleの調整が難しく、実装差も大きい。',
  'stalled_subproblem;constraint_drift;poor_scaling', 'OCで十分な単純volume制約を無批判に順位付けする場合。',
  '複数制約やOCのmove limitがボトルネックになる場合。', 'OC、SCP、SQPと条件をそろえて比較する。',
  'KKT残差停滞;subproblemが小さすぎる;constraint violation。', 'intermediate', 'high', 'high', 'medium',
  'max_iterations;KKT_residual;volume_tolerance', 'compliance;volume_fraction;KKT_residual;asymptote_width',
  'M_OC_TOPOLOGY;M_SIMP_TOPOLOGY', 'MF_TOPOLOGY_OPTIMIZATION', '', 'S100', 'high', '2026-07-18'
),
(
  'M_ADJOINT_SENSITIVITY', 'adjoint感度解析', 'Adjoint sensitivity analysis',
  'adjoint method;adjoint sensitivity;reverse sensitivity', 'MF_TOPOLOGY_OPTIMIZATION', 'variant',
  '状態方程式のadjointを解き、設計変数ごとの目的感度を少ない追加state solveで計算する方法。',
  'pde_constrained;topology_optimization;sensitivity_analysis',
  'state equation、目的functional、微分可能な材料・境界modelを定義する。',
  'adjoint;analytic_gradient;automatic_differentiation', 'field;function', 'state;integral;bounds', 'weak',
  'yes_local_only', 'local', 'deterministic', 'local_numerical',
  'adjointは感度の計算法であり、更新則や大域最適性の保証そのものではない。',
  'gradient_consistency;state_residual;adjoint_residual', 'very_high_with_sparse_solve', 'high',
  'forward stateとadjoint stateのsolve。', '目的ごとにadjointを解き、設計変数数に依存しにくい勾配を得る。',
  'sparse_linear_algebra;distributed', 'low', 'medium', 'very_high', 'low', 'low', 'state_solve;adjoint_solve',
  'conditional', 'no', 'field-valued設計変数でも勾配を作れる。', 'stateとadjointの整合性、checkpoint、境界条件に敏感。',
  'inconsistent_adjoint;state_nonconvergence;gradient_mismatch', '非微分なcontactやdiscrete topologyをそのまま扱う場合。',
  'state solveが安定し、目的functionalが微分可能なPDE制約問題。', 'direct sensitivityやfinite differenceとgradient checkを行う。',
  'gradient check failure;adjoint residual;state residual', 'intermediate', 'high', 'high', 'high',
  'state_residual;adjoint_residual;gradient_check', 'gradient_check;state_residual;adjoint_residual', 'M_SIMP_TOPOLOGY',
  'MF_TOPOLOGY_OPTIMIZATION', '', 'S101', 'high', '2026-07-18'
);

INSERT INTO method_hierarchy (
  hierarchy_id, parent_method_id, child_method_id, relation_type, depth,
  is_primary_parent, rationale, source_ids, confidence, last_verified
) VALUES
('MH_TOPOLOGY_SIMP', 'MF_TOPOLOGY_OPTIMIZATION', 'M_SIMP_TOPOLOGY', 'variant_of', 1, 'yes', 'Density-based topology optimization variant.', 'S097;S098', 'high', '2026-07-18'),
('MH_TOPOLOGY_FILTER', 'MF_TOPOLOGY_OPTIMIZATION', 'M_DENSITY_FILTER', 'variant_of', 1, 'yes', 'Filtering regularizes a field-based topology loop.', 'S099', 'high', '2026-07-18'),
('MH_TOPOLOGY_OC', 'MF_TOPOLOGY_OPTIMIZATION', 'M_OC_TOPOLOGY', 'variant_of', 1, 'yes', 'Structural optimization update rule.', 'S097', 'high', '2026-07-18'),
('MH_TOPOLOGY_MMA', 'MF_TOPOLOGY_OPTIMIZATION', 'M_MMA', 'variant_of', 1, 'yes', 'Moving-asymptote update for structural optimization.', 'S100', 'high', '2026-07-18'),
('MH_TOPOLOGY_ADJOINT', 'MF_TOPOLOGY_OPTIMIZATION', 'M_ADJOINT_SENSITIVITY', 'variant_of', 1, 'yes', 'Adjoint sensitivity method for PDE-constrained objectives.', 'S101', 'high', '2026-07-18');

PRAGMA foreign_keys = OFF;

INSERT INTO benchmark_contexts (
  context_id, context_version, category, problem_instance_id, problem_variant, dimension,
  sparsity_json, hardware_json, runtime_json, oracle_budget_json, evaluation_budget,
  time_budget_seconds, tolerance_json, stopping_json, initialization_json, seed_status,
  seed_value, tuning_policy, implementation_versions_json, outcome_metrics_json,
  status_mapping_json, source_ids_json, last_verified
) VALUES (
  'BENCH_TOPOLOGY_EDUCATIONAL_12', '1.0.0', 'NLP', 'INSTANCE_TOPOLOGY_CANTILEVER_2D',
  'deterministic_density_field_teaching_trace', 32,
  '{"field_grid":"8x4","state_solve":"sparse_reference"}',
  '{"os":"platform-neutral","precision":"float64","hardware":"educational"}',
  '{"comparison_scope":"exact","generator_id":"educational.topology_optimization.v1","generator_version":"1.0.0","implementation_mapping_status":"not_applicable"}',
  '{"limit":12,"unit":"oracle_evaluations"}', 12, NULL,
  '{"volume_fraction":0.5,"state_residual":"teaching_reference"}',
  '{"policy":"fixed_oracle_budget","value":12}',
  '{"policy":"fixed_density_field","points":[0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5]}', 'not_applicable', NULL,
  'fixed educational presets; no post-run tuning',
  '{"generator_id":"educational.topology_optimization.v1","generator_version":"1.0.0","implementation_mapping_status":"not_applicable"}',
  '["compliance","volume_fraction","gray_fraction","checkerboard_score"]',
  '{"feasibility":"discretized_volume_only","terminal_status":"teaching_trace"}',
  '["S097","S098","S099","S100","S101"]', '2026-07-18'
);

PRAGMA foreign_keys = ON;
