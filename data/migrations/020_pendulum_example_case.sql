-- Give the pendulum flagship its own canonical example ID.
-- EC027 already belongs to the simulation-failure case and must not be repurposed.

INSERT INTO example_cases (
  case_id, title_ja, problem_id, problem_features_summary, alternative_solution_ids,
  first_choice_method_id, second_choice_method_id, avoid_method_id, decision_reason,
  additional_information_needed, representative_implementation_ids, expected_failures,
  switch_decision, validation_result, model_revision_notes, source_ids, confidence,
  last_verified
) VALUES (
  'EC029', '制約付きpendulum swing-up', 'PA042',
  '非線形pendulum dynamics、固定horizon、terminal target、path／bound制約を持つ軌道最適化。',
  'ALT_SPECIALIZED;ALT_DECOMPOSITION',
  'M_DIRECT_COLLOCATION', 'M_MULTIPLE_SHOOTING', 'M_BFGS',
  'stateとcontrolを同時に置き、dynamics defectとpath制約を疎なNLPとして観測できる。',
  'mesh、初期trajectory、nodeと区間再構成のviolation、model mismatch。',
  'I_CASADI;I_ACADOS;I_DRAKE',
  'mesh artifact;reconstructed path violation;terminal error under model mismatch',
  'mesh refinementと独立validation rolloutで離散化誤差とmodel誤差を分ける。',
  'pass',
  'EC020の一般軌道教材を変更せず、固定pendulum instanceを独立Caseとして追加する。',
  'S042;S050;S102', 'high', '2026-07-19'
);

INSERT INTO case_feature_map (
  case_feature_map_id, case_id, feature_id, feature_value_id, value_text,
  truth_status, notes, source_ids, confidence, last_verified
)
SELECT
  printf('CFM%05d', 280 + ROW_NUMBER() OVER (ORDER BY feature_id)),
  'EC029', feature_id, feature_value_id, value_text, truth_status,
  'Inherited from PA042; the fixed pendulum instance and reconstruction checks take precedence.',
  'S042;S050;S102', 'high', '2026-07-19'
FROM case_feature_map
WHERE case_id = 'EC020';

INSERT INTO case_method_map (
  case_method_map_id, case_id, method_id, role, fit_id, rationale,
  source_ids, confidence, last_verified
) VALUES
('CMM0085', 'EC029', 'M_DIRECT_COLLOCATION', 'first_choice', NULL,
 'Expose state, control, defects, and path constraints in one sparse transcription.',
 'S042;S050;S102', 'high', '2026-07-19'),
('CMM0086', 'EC029', 'M_MULTIPLE_SHOOTING', 'second_choice', NULL,
 'Retain interval integration while separating long-horizon sensitivity by segment.',
 'S042;S050;S102', 'high', '2026-07-19'),
('CMM0087', 'EC029', 'M_BFGS', 'avoid', NULL,
 'A flat unconstrained objective hides dynamics defects and path feasibility.',
 'S042;S050;S102', 'high', '2026-07-19');

INSERT INTO case_implementation_map (
  case_implementation_map_id, case_id, implementation_id, role, sequence,
  notes, source_ids, confidence, last_verified
) VALUES
('CIM0072', 'EC029', 'I_CASADI', 'representative', 1,
 'Representative transcription implementation; exact options remain instance-specific.',
 'S042', 'high', '2026-07-19'),
('CIM0073', 'EC029', 'I_ACADOS', 'representative', 2,
 'Representative optimal-control implementation; exact options remain instance-specific.',
 'S042;S102', 'medium', '2026-07-19'),
('CIM0074', 'EC029', 'I_DRAKE', 'representative', 3,
 'Representative trajectory-optimization implementation; exact options remain instance-specific.',
 'S050', 'high', '2026-07-19');

INSERT INTO case_alternative_map (
  case_alternative_map_id, case_id, alternative_id, sequence, rationale,
  source_ids, confidence, last_verified
) VALUES
('CAM0049', 'EC029', 'ALT_SPECIALIZED', 1,
 'Compare specialized trajectory-optimization tooling and its diagnostics.',
 'S042;S050;S102', 'high', '2026-07-19'),
('CAM0050', 'EC029', 'ALT_DECOMPOSITION', 2,
 'Compare shooting or decomposition when rollout and memory structure dominate.',
 'S042;S050;S102', 'high', '2026-07-19');
