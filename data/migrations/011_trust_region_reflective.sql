PRAGMA foreign_keys = ON;

INSERT INTO sources (
  source_id, source_type, title, author_or_organization, publication_date,
  accessed_date, url, supported_claim, source_quality, notes, currentness_status
) VALUES (
  'S096',
  'original_paper',
  'A Subspace, Interior, and Conjugate Gradient Method for Large-Scale Bound-Constrained Minimization Problems',
  'Branch, Coleman, and Li',
  '1999',
  '2026-07-16',
  'https://epubs.siam.org/doi/10.1137/S1064827595289108',
  'Trust Region Reflective and large-scale bound-constrained subspace method',
  'primary',
  'Primary reference cited by the SciPy least_squares documentation for method=trf.',
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
  'TRF;trust-region reflective;reflective least squares',
  'M_TRUST_REGION',
  'variant',
  '残差とJacobianから作るGauss–Newton型modelを、boundsまでの距離と反射方向を考慮したtrust region内で改善する非線形最小二乗法。',
  'nonlinear_least_squares;bound_constrained;large_sparse',
  '残差vectorとJacobianまたはその安定した近似が利用でき、変数boundsが意味を持つ。局所modelを評価できる程度に残差が滑らか。',
  'residual;jacobian;finite_difference_or_sparse_jacobian',
  'continuous',
  'bounds',
  'strong_for_convex_or_well_conditioned_least_squares',
  'yes_local_only',
  'local',
  'deterministic',
  'local_numerical',
  '標準的な滑らかさ・正則性・bounded level set等の仮定下で一階停留点への大域的収束理論を持つ。非凸最小二乗では大域最適性を保証しない。',
  'scaled_first_order_optimality;active_bounds_not_global_certificate',
  'high_with_sparse_jacobian',
  'medium_to_high',
  'residual/Jacobian評価、Gauss–Newton model、dense SVDまたはsparse LSMR部分問題。',
  '通常は一候補stepごとに残差を評価し、model agreementに応じてtrust regionを更新。数値Jacobianでは追加評価。',
  'finite_difference_workers;linear_algebra_backend',
  'medium_nonconvex',
  'medium',
  'very_high',
  'low_to_medium',
  'low',
  'strictly_feasible_iterates;distance_to_bounds_scaling;reflected_directions',
  'yes_by_initial_guess',
  'conditional',
  'boundsを直接扱う;large sparse Jacobianへ対応;rank-deficient問題のregularization option;robust lossと併用可能',
  '変数scale・Jacobian品質に敏感;局所解;strict feasibilityによりactive_maskはtolerance依存;一般非線形制約は扱わない',
  'trust_radius_collapse;poor_scaling;rank_deficient_jacobian;wrong_jacobian_sparsity;boundary_stagnation',
  '離散変数;一般等式・不等式制約;強い不連続;残差vectorを定義できないblack-box;大域最適性証明が必要',
  'bounds付き非線形最小二乗、特にlarge sparse JacobianまたはSciPy least_squaresの標準的な開始点。',
  'LMがboundsを扱えない、またはdense small-problem前提が合わない。dogboxでrank deficiencyや停滞が見られる。',
  'optimalityが下がらない;active_maskが想定と異なる;trust radiusが縮小し続ける;数値Jacobian評価が支配的;境界付近でcostが停滞。',
  'medium',
  'medium',
  'high',
  'high',
  'ftol;xtol;gtol;max_nfev;callback_stop',
  'cost;optimality;active_mask;nfev;njev;status;message;residual_pattern;jacobian_rank;trust_solver',
  'M_GAUSS_NEWTON;M_LEVENBERG_MARQUARDT;M_TRUST_KRYLOV',
  'M_TRUST_REGION',
  '',
  'S003;S096',
  'high',
  '2026-07-16'
);

UPDATE methods
SET child_method_ids = CASE
  WHEN child_method_ids IS NULL OR trim(child_method_ids) = ''
    THEN 'M_TRUST_REGION_REFLECTIVE'
  WHEN instr(';' || child_method_ids || ';', ';M_TRUST_REGION_REFLECTIVE;') = 0
    THEN child_method_ids || ';M_TRUST_REGION_REFLECTIVE'
  ELSE child_method_ids
END,
last_verified = '2026-07-16'
WHERE method_id = 'M_TRUST_REGION';

INSERT INTO method_hierarchy (
  hierarchy_id, parent_method_id, child_method_id, relation_type, depth,
  is_primary_parent, rationale, source_ids, confidence, last_verified
) VALUES (
  'H_TRUST_REGION_REFLECTIVE',
  'M_TRUST_REGION',
  'M_TRUST_REGION_REFLECTIVE',
  'variant_of',
  1,
  'yes',
  'TRF is a trust-region variant specialized for bound-constrained nonlinear least squares.',
  'S003;S096',
  'high',
  '2026-07-16'
);

DELETE FROM method_implementation_map
WHERE implementation_id = 'I_SCIPY_LEAST_SQUARES_TRF';

INSERT INTO method_implementation_map (
  method_implementation_map_id, method_id, implementation_id, support_level,
  api_name, method_selector, implementation_notes, limitations, source_ids,
  confidence, last_verified
) VALUES (
  'MIM_TRF_SCIPY',
  'M_TRUST_REGION_REFLECTIVE',
  'I_SCIPY_LEAST_SQUARES_TRF',
  'native',
  'scipy.optimize.least_squares',
  'trf',
  'SciPyのleast_squaresでdefault。residual vector、Jacobian sparsity、robust loss、dense exactまたはsparse LSMR trust solverを利用できる。',
  'bounds以外の一般制約は扱わない。局所法であり、default選択は一般性能rankingではない。',
  'S003;S096',
  'high',
  '2026-07-16'
);

UPDATE implementations
SET supported_method_ids = 'M_TRUST_REGION_REFLECTIVE',
    implementation_differences = 'least_squaresのmethod=trf。bounds距離によるscale、反射方向、strictly feasible iteratesを使う。dense Jacobianはexact系、large sparse JacobianはLSMR/2-D subspace系。',
    notes = 'scipy.optimize.least_squaresではmethodを省略するとtrf。curve_fitではbounds指定時にtrfがdefault。defaultは万能順位ではなくAPI条件付きの選択。',
    source_ids = 'S003;S096;S082',
    last_verified = '2026-07-16'
WHERE implementation_id = 'I_SCIPY_LEAST_SQUARES_TRF';

INSERT INTO terminology_aliases (
  term_id, target_type, target_id, label_ja, label_en, abbreviations_json,
  synonyms_json, domain_terms_json, misspellings_json, deprecated_terms_json,
  disambiguation_note, locale, rationale, source_ids_json, last_verified
) VALUES (
  'TERM_TRUST_REGION_REFLECTIVE',
  'method',
  'M_TRUST_REGION_REFLECTIVE',
  'Trust Region Reflective法',
  'Trust Region Reflective',
  '["TRF"]',
  '["trust-region reflective","reflective least squares","SciPy trf"]',
  '["bounded nonlinear least squares","疎Jacobian最小二乗"]',
  '["trust region reflection","trust reflective"]',
  '[]',
  'SciPy least_squaresのtrfと、一般scalar目的のtrust-region Newton法を区別する。',
  'ja-en',
  'API selector、略称、和英表記からcanonical methodへ解決する。',
  '["S003","S096"]',
  '2026-07-16'
);

INSERT INTO learning_edges (
  edge_id, source_type, source_id, target_type, target_id, relation, rationale,
  difficulty, audience, display_order, source_ids_json, last_verified, status
) VALUES
  (
    'LE_TRF_SPECIAL_GN', 'method', 'M_TRUST_REGION_REFLECTIVE', 'method',
    'M_GAUSS_NEWTON', 'special_case_of',
    'TRF uses a Gauss–Newton least-squares model and adds bound-aware trust-region globalization.',
    'intermediate', 'all', 1, '["S003","S096"]', '2026-07-16', 'current'
  ),
  (
    'LE_TRF_CONTRAST_LM', 'method', 'M_TRUST_REGION_REFLECTIVE', 'method',
    'M_LEVENBERG_MARQUARDT', 'contrast_with',
    'LM is usually efficient for small unconstrained least squares; TRF handles bounds and sparse Jacobians.',
    'beginner', 'all', 2, '["S003"]', '2026-07-16', 'current'
  ),
  (
    'LE_TRF_IMPLEMENTED_SCIPY', 'method', 'M_TRUST_REGION_REFLECTIVE', 'implementation',
    'I_SCIPY_LEAST_SQUARES_TRF', 'implemented_by',
    'SciPy exposes TRF through scipy.optimize.least_squares(method="trf").',
    'beginner', 'practitioner', 3, '["S003"]', '2026-07-16', 'current'
  );
