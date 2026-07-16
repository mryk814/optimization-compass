PRAGMA foreign_keys = OFF;

DROP INDEX implementation_claim_active_unique;
DROP TABLE implementation_claims;

CREATE TABLE implementation_claims (
  claim_id TEXT NOT NULL PRIMARY KEY CHECK (trim(claim_id) <> ''),
  subject_id TEXT NOT NULL,
  predicate TEXT NOT NULL CHECK (predicate IN (
    'current_release', 'maintenance_status', 'license_spdx', 'platform_architecture',
    'gpu_distributed_support', 'supported_problem_classes', 'important_option_defaults',
    'default_method_selection', 'conditional_default_method'
  )),
  value_json TEXT NOT NULL CHECK (json_valid(value_json)),
  value_status TEXT NOT NULL CHECK (value_status IN ('verified', 'explicit_unknown')),
  valid_from DATE NOT NULL,
  valid_to DATE,
  replaced_by TEXT,
  source_id TEXT NOT NULL,
  source_date DATE NOT NULL,
  last_verified DATE NOT NULL,
  confidence TEXT NOT NULL CHECK (confidence IN ('high', 'medium', 'low', 'unverified')),
  verification_status TEXT NOT NULL CHECK (
    verification_status IN ('verified', 'source_pending', 'superseded')
  ),
  product_version TEXT,
  commit_sha TEXT,
  release_tag TEXT,
  FOREIGN KEY (subject_id) REFERENCES implementations(implementation_id),
  FOREIGN KEY (source_id) REFERENCES sources(source_id),
  FOREIGN KEY (replaced_by) REFERENCES implementation_claims(claim_id),
  CHECK (valid_to IS NULL OR valid_to >= valid_from),
  CHECK ((value_status = 'explicit_unknown') = (verification_status = 'source_pending'))
);

CREATE UNIQUE INDEX implementation_claim_active_unique
  ON implementation_claims(subject_id, predicate)
  WHERE valid_to IS NULL;

INSERT INTO sources (
  source_id, source_type, title, author_or_organization, publication_date,
  accessed_date, url, supported_claim, source_quality, notes, currentness_status
) VALUES
(
  'S096', 'original_paper',
  'A Subspace, Interior, and Conjugate Gradient Method for Large-Scale Bound-Constrained Minimization Problems',
  'Branch, Coleman, and Li', '1999-01-01', '2026-07-16',
  'https://doi.org/10.1137/S1064827595289108',
  'Trust Region Reflective / STIR bound-constrained trust-region method',
  'primary', NULL, 'historical_primary'
),
(
  'S097', 'official_documentation', 'scipy.optimize.curve_fit', 'SciPy', NULL,
  '2026-07-16',
  'https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.curve_fit.html',
  'curve_fit method selection and bounds-dependent defaults',
  'primary', NULL, 'verified_current'
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
  'トラストリージョン・リフレクティブ法',
  'Trust Region Reflective',
  'TRF;trust-region reflective;scipy least_squares trf',
  'MF_TRUST_REGION',
  'variant',
  'bounds付き非線形最小二乗で、境界までの距離と反射方向を使いながらGauss–Newton型の局所modelを安全に改善するtrust-region法。',
  'nonlinear_least_squares;bound_constrained;large_sparse',
  'residual vectorと十分に滑らかなJacobianを評価でき、boundsと変数scaleが意味を持つ。',
  'residual;jacobian;finite_difference_or_callable',
  'continuous',
  'bounds',
  'strong_for_least_squares',
  'yes_local_only',
  'local',
  'deterministic',
  'local_numerical',
  '標準的な滑らかさと正則性の下で、boundsを考慮した一階停留条件への収束を持つ変種。',
  'bound_scaled_first_order_optimality',
  'high_with_sparse_jacobian',
  'medium',
  '残差・Jacobian評価とtrust-region部分問題。denseではSVD相当、large sparseではLSMR系。',
  '候補stepの評価、拒否時の追加評価、必要なら数値Jacobian評価。',
  'jacobian_columns;linear_algebra_by_backend',
  'medium',
  'medium',
  'very_high',
  'low_to_medium',
  'low',
  'strictly_feasible_bound_iterates;reflected_directions',
  'yes',
  'conditional',
  'boundsを直接扱う;疎Jacobianを利用できる;default実装が広く使われる;robust lossと併用可能',
  '局所解;scaleとJacobian品質に敏感;一般非線形制約は扱わない;rank deficiencyで停滞し得る',
  'trust_radius_collapse;poor_scaling;rank_deficient_jacobian;active_bound_stagnation;bad_jacobian',
  '離散変数;一般等式・不等式制約;強い不連続;大域最適性証明が必要',
  'bounds付き非線形最小二乗、またはlarge sparse Jacobianを持つleast_squaresで堅実な第一候補。',
  '無制約小規模でLMが使えない、またはLMがrank・bounds条件に合わない。',
  'optimalityが停滞;active_maskが固定したままcostが改善しない;評価上限;Jacobian condition悪化。',
  'medium',
  'medium',
  'high',
  'high',
  'ftol;xtol;gtol;evaluation_budget',
  'cost;optimality;active_mask;nfev;njev;status;message;jacobian_rank;trust_solver',
  'M_GAUSS_NEWTON;M_LEVENBERG_MARQUARDT;M_TRUST_KRYLOV;M_LBFGSB;M_SLSQP',
  'MF_TRUST_REGION',
  NULL,
  'S003;S096;S097',
  'high',
  '2026-07-16'
);

INSERT INTO method_hierarchy (
  hierarchy_id, parent_method_id, child_method_id, relation_type, depth,
  is_primary_parent, rationale, source_ids, confidence, last_verified
) VALUES (
  'MH_TRF', 'MF_TRUST_REGION', 'M_TRUST_REGION_REFLECTIVE', 'is_a', 1, 'yes',
  'Trust Region Reflective is a bound-aware nonlinear least-squares member of the trust-region family.',
  'S003;S096', 'high', '2026-07-16'
);

UPDATE evidence_links
SET target_id = 'MIM_TRF_SCIPY',
    claim_summary = 'SciPy least_squares provides the native Trust Region Reflective implementation.',
    last_verified = '2026-07-16'
WHERE target_table = 'method_implementation_map'
  AND target_id IN ('MIM00011', 'MIM00012');

DELETE FROM method_implementation_map
WHERE implementation_id = 'I_SCIPY_LEAST_SQUARES_TRF';

INSERT INTO method_implementation_map (
  method_implementation_map_id, method_id, implementation_id, support_level,
  api_name, method_selector, implementation_notes, limitations, source_ids,
  confidence, last_verified
) VALUES (
  'MIM_TRF_SCIPY', 'M_TRUST_REGION_REFLECTIVE', 'I_SCIPY_LEAST_SQUARES_TRF',
  'native', 'scipy.optimize.least_squares', 'trf',
  'SciPy least_squaresのdefault。dense Jacobianではexact系、large sparseではLSMR系を選択できる。',
  '非線形最小二乗とboundsが対象。default選択は一般性能rankingを意味しない。',
  'S003;S096;S097', 'high', '2026-07-16'
);

UPDATE implementations
SET supported_method_ids = 'M_TRUST_REGION_REFLECTIVE',
    notes = 'residual vectorとJacobian sparsityを直接渡す。least_squaresのdefaultはtrf。curve_fitはbounds指定時にtrfを選ぶ。robust lossも選択可能。',
    source_ids = 'S003;S096;S097;S082',
    last_verified = '2026-07-16'
WHERE implementation_id = 'I_SCIPY_LEAST_SQUARES_TRF';

PRAGMA foreign_keys = ON;
