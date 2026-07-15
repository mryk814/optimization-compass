# Optimization Method Selection Database staged report

- Version: `0.8.0`
- Release date: `2026-07-15`
- Tables: `58`
- Rows: `8873`
- Data license: `CC-BY-4.0` (`licenses/DATA_LICENSE.txt`)

| Table | Rows |
|---|---:|
| `advanced_view` | 280 |
| `alternative_solution_checks` | 18 |
| `atomic_predicates` | 16 |
| `backlog` | 38 |
| `beginner_view` | 28 |
| `benchmark_contexts` | 6 |
| `case_alternative_map` | 48 |
| `case_feature_map` | 280 |
| `case_implementation_map` | 71 |
| `case_method_map` | 84 |
| `comparison_set_members` | 3 |
| `comparison_sets` | 1 |
| `controlled_vocab` | 129 |
| `decision_questions` | 12 |
| `decision_rule_target_retirements` | 7 |
| `decision_rules` | 78 |
| `demo_scenarios` | 5 |
| `diagnostics` | 42 |
| `evidence_links` | 4193 |
| `example_cases` | 28 |
| `failure_mode_affected_entities` | 93 |
| `failure_mode_diagnostics` | 12 |
| `failure_mode_mitigations` | 12 |
| `failure_mode_profiles` | 12 |
| `failure_mode_scenarios` | 4 |
| `failure_mode_symptoms` | 12 |
| `failure_mode_triggers` | 12 |
| `failure_modes` | 42 |
| `feature_values` | 93 |
| `glossary` | 84 |
| `implementation_claims` | 449 |
| `implementations` | 64 |
| `learning_coverage_expectations` | 8 |
| `learning_edges` | 3 |
| `learning_slice_priorities` | 5 |
| `method_hierarchy` | 82 |
| `method_implementation_map` | 163 |
| `method_visualization_profiles` | 4 |
| `methods` | 98 |
| `model_revisions` | 7 |
| `predicate_coverage` | 15 |
| `predicate_policies` | 15 |
| `problem_alternative_map` | 96 |
| `problem_archetypes` | 56 |
| `problem_definition_archetypes` | 14 |
| `problem_definition_features` | 27 |
| `problem_definitions` | 9 |
| `problem_feature_map` | 842 |
| `problem_features` | 211 |
| `problem_instances` | 10 |
| `problem_method_fit` | 280 |
| `readme` | 24 |
| `release_checks` | 24 |
| `schema_dictionary` | 487 |
| `sheet_catalog` | 33 |
| `sources` | 95 |
| `version_history` | 3 |
| `view_presets` | 6 |

## Free-text-only method conditions

Detected `368` populated condition fields across `92` methods without complete atomic-predicate coverage.

| Method | Unmigrated condition fields |
|---|---|
| `MF_COMPOSITE_CONVEX` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `MF_CONSTRAINED_NLP` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `MF_CONSTRAINT_PROGRAMMING` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `MF_DFO_LOCAL` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `MF_DISCRETE_EXACT` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `MF_EVOLUTIONARY` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `MF_GLOBAL_SEARCH` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `MF_GRAPH_DP` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `MF_LP_QP_CONIC` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `MF_MANIFOLD` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `MF_MULTI_OBJECTIVE` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `MF_OPTIMAL_CONTROL` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `MF_SMOOTH_LOCAL` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `MF_STOCHASTIC_ML` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `MF_SURROGATE_HPO` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `MF_TRUST_REGION` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_ACTIVE_SET` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_ACTIVE_SET_QP` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_ADAM` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_ADAMW` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_ADMM` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_ADMM_QP` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_AUGMENTED_LAGRANGIAN` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_BARRIER_LP_QP` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_BASIN_HOPPING` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_BRANCH_BOUND` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_BRANCH_CUT` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_BUNDLE` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_CDCL_SAT` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_COBYLA` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_COBYQA` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_COORDINATE_DESCENT` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_CP_SAT` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_CP_SEARCH` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_DIFFERENTIAL_EVOLUTION` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_DIJKSTRA_ASTAR` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_DIRECT` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_DIRECT_COLLOCATION` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_DIRECT_SHOOTING` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_DUAL_SIMPLEX` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_DYNAMIC_PROGRAMMING` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_EPSILON_CONSTRAINT` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_FISTA` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_GAUSS_NEWTON` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_GENETIC_ALGORITHM` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_GRADIENT_DESCENT` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_HUNGARIAN` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_HYPERBAND_ASHA` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_ILQR_DDP` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_LBFGS` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_LBFGSB` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_LEVENBERG_MARQUARDT` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_LOCAL_SEARCH_COMBINATORIAL` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_MADS` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_MIRROR_DESCENT` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_MOEA_D` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_MOMENTUM_SGD` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_MULTIPLE_SHOOTING` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_MULTISTART` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_NETWORK_SIMPLEX` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_NEWTON` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_NEWTON_CG` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_NLCG` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_NSGA_II` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_NSGA_III` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_OUTER_APPROX_MINLP` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_PARTICLE_SWARM` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_PATTERN_SEARCH` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_PBT` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_PDLP` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_POWELL` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_PRIMAL_DUAL_CONIC` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_PROJECTED_GRADIENT` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_PROX_GRADIENT` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_RANDOM_SEARCH` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_RIEMANNIAN_GRADIENT` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_RIEMANNIAN_TRUST_REGION` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_SGD` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_SHGO` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_SIMPLEX` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_SIMULATED_ANNEALING` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_SMAC_RF` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_SPATIAL_BRANCH_BOUND` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_SPSA` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_SQP` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_SUBGRADIENT` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_TPE` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_TRUST_EXACT` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_TRUST_KRYLOV` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_TRUST_NCG` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_TURBO_SAASBO` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
| `M_WEIGHTED_SUM` | `required_assumptions`, `avoid_conditions`, `first_choice_conditions`, `second_choice_conditions` |
