PRAGMA foreign_keys = OFF;

INSERT INTO sources (
  source_id, source_type, title, author_or_organization, publication_date,
  accessed_date, url, supported_claim, source_quality, notes, currentness_status
) VALUES (
  'S096',
  'original_paper',
  'A Subspace, Interior, and Conjugate Gradient Method for Large-Scale Bound-Constrained Minimization Problems',
  'M. A. Branch, T. F. Coleman, and Y. Li',
  '1999-01-01',
  '2026-07-16',
  'https://doi.org/10.1137/S1064827595289108',
  'Subspace, interior, reflected-direction trust-region method for large-scale bound-constrained problems',
  'primary',
  'Primary reference cited by the SciPy least_squares Trust Region Reflective notes.',
  'historical_primary'
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
) VALUES (
  'M_TRUST_REGION_REFLECTIVE',
  'Trust Region Reflective法',
  'Trust Region Reflective',
  'TRF;trust-region reflective;trust region reflective;subspace trust region interior reflective',
  'MF_TRUST_REGION',
  'variant',
  'bounds付き非線形最小二乗で、境界までの距離に応じてtrust regionを変形し、反射方向も使って局所解を探すGauss–Newton系手法。',
  'nonlinear_least_squares;bound_constrained;large_sparse',
  '残差vectorと局所的に有用なJacobianが得られ、上下限が数値的・物理的に妥当。',
  'residual;jacobian;optional_sparse_jacobian',
  'continuous',
  'bounds',
  'strong_for_linear_or_convex_least_squares',
  'yes_local_only',
  'local',
  'deterministic',
  'local_numerical',
  '標準的な滑らかさとmodel精度の仮定下で一階停留点へのtrust-region収束。非凸非線形最小二乗では局所解。',
  'scaled_first_order_optimality;model_agreement;active_bounds',
  'high_with_sparse_jacobian',
  'medium_dense_to_low_sparse',
  '残差・Jacobian評価とtrust-region部分問題。denseではSVD系、large sparseではLSMRと低次元部分空間。',
  '通常はtrial pointごとに残差を評価し、Jacobianは解析・数値差分・sparse operatorで供給。',
  'numerical_differentiation_workers;linear_algebra_by_backend',
  'medium_nonconvex',
  'medium',
  'very_high',
  'low_to_medium_with_robust_loss',
  'low',
  'strictly_feasible_iterates;distance_to_bounds_scaling;reflected_directions',
  'yes',
  'conditional',
  'boundsを直接扱う;large sparse Jacobian;robust loss;default実装として広く利用される',
  '局所解;一般非線形制約は扱わない;Jacobianとscaleに敏感;rank deficiencyで停滞し得る',
  'rank_deficiency;poor_scaling;trust_radius_collapse;active_bound_stagnation;bad_jacobian',
  '離散変数;不連続残差;一般非線形制約;大域最適性certificateが必要;残差分解が不自然',
  'bounds付き非線形最小二乗、特に大規模または疎なJacobianで、局所解と一階診断が必要。',
  'LMがboundsに対応できない、またはdense小規模法ではmemory・計算量が重い。',
  'optimality停滞;active_maskが不安定;rank deficiency;Jacobian評価が支配的;一般制約が必要。',
  'medium',
  'medium',
  'high',
  'high',
  'ftol;xtol;gtol;max_nfev;callback_stop',
  'cost;residual_vector;optimality;active_mask;nfev;njev;status;trust_region_model_agreement;singular_values',
  'M_GAUSS_NEWTON;M_LEVENBERG_MARQUARDT;M_TRUST_KRYLOV;M_LBFGSB;M_SLSQP',
  'MF_TRUST_REGION',
  NULL,
  'S003;S096',
  'high',
  '2026-07-16'
);

UPDATE methods
SET child_method_ids = CASE
  WHEN child_method_ids IS NULL OR trim(child_method_ids) = '' THEN 'M_TRUST_REGION_REFLECTIVE'
  ELSE child_method_ids || ';M_TRUST_REGION_REFLECTIVE'
END,
last_verified = '2026-07-16'
WHERE method_id = 'MF_TRUST_REGION';

UPDATE methods
SET related_method_ids = CASE
  WHEN related_method_ids IS NULL OR trim(related_method_ids) = '' THEN 'M_TRUST_REGION_REFLECTIVE'
  ELSE related_method_ids || ';M_TRUST_REGION_REFLECTIVE'
END,
last_verified = '2026-07-16'
WHERE method_id IN ('M_GAUSS_NEWTON', 'M_LEVENBERG_MARQUARDT', 'M_TRUST_KRYLOV');

INSERT INTO method_hierarchy (
  hierarchy_id, parent_method_id, child_method_id, relation_type, depth,
  is_primary_parent, rationale, source_ids, confidence, last_verified
) VALUES (
  'MH_TRUST_REGION_REFLECTIVE',
  'MF_TRUST_REGION',
  'M_TRUST_REGION_REFLECTIVE',
  'variant_of',
  1,
  'yes',
  'Bound-constrained nonlinear least-squares trust-region variant with interior scaling and reflected directions.',
  'S003;S096',
  'high',
  '2026-07-16'
);

UPDATE implementations
SET
  api_name = 'scipy.optimize.least_squares / scipy.optimize.curve_fit',
  method_selector = 'trf; curve_fit selects trf when bounds are supplied',
  problem_formats = 'nonlinear least squares; bounded curve fitting',
  constraint_support = 'bounds',
  sparse_support = 'yes; jac_sparsity or sparse Jacobian selects LSMR path',
  callback = 'yes for least_squares trf',
  major_options = 'least_squares: method=trf is the default; curve_fit: trf is selected when bounds are supplied and lm otherwise; tr_solver; jac_sparsity; x_scale; loss; ftol; xtol; gtol; max_nfev',
  default_safety = 'default_is_api_specific_not_a_global_ranking',
  usage_example = 'scipy.optimize.least_squares(..., method="trf", bounds=(lower, upper))',
  notes = 'least_squares defaults to trf. curve_fit delegates bounded problems to least_squares and defaults to trf when bounds are supplied.',
  supported_method_ids = 'M_TRUST_REGION_REFLECTIVE',
  implementation_differences = 'Dense Jacobians use an exact SVD-like trust-region solve; large sparse Jacobians use LSMR and a two-dimensional subspace. Iterates remain strictly feasible and active_mask is tolerance-based.',
  source_ids = 'S003;S082;S096',
  last_verified = '2026-07-16'
WHERE implementation_id = 'I_SCIPY_LEAST_SQUARES_TRF';

UPDATE evidence_links
SET
  source_id = 'S003',
  target_id = 'MIM_SCIPY_TRF',
  supported_field = 'support_level;method_selector;implementation_notes',
  claim_summary = 'SciPy exposes native Trust Region Reflective nonlinear least squares and selects trf by default for least_squares.',
  evidence_role = 'direct',
  confidence = 'high',
  last_verified = '2026-07-16'
WHERE target_table = 'method_implementation_map'
  AND target_id IN ('MIM00011', 'MIM00012');

DELETE FROM method_implementation_map
WHERE implementation_id = 'I_SCIPY_LEAST_SQUARES_TRF';

INSERT INTO method_implementation_map (
  method_implementation_map_id, method_id, implementation_id, support_level,
  api_name, method_selector, implementation_notes, limitations,
  source_ids, confidence, last_verified
) VALUES (
  'MIM_SCIPY_TRF',
  'M_TRUST_REGION_REFLECTIVE',
  'I_SCIPY_LEAST_SQUARES_TRF',
  'native',
  'scipy.optimize.least_squares',
  'trf (default)',
  'Residual vector and Jacobian structure are used directly. Bounds, robust loss, sparse Jacobians, and callback stopping are supported by the API.',
  'Local nonlinear least-squares method; bounds only, not general nonlinear constraints. Default selection is not a universal performance ranking.',
  'S003;S096',
  'high',
  '2026-07-16'
);

PRAGMA foreign_keys = ON;
