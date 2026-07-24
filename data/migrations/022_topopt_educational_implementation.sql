PRAGMA foreign_keys = ON;

-- Register the DTU-maintained top88 MATLAB teaching code as a bounded
-- implementation of the density-based compliance loop it actually exposes.
-- The source is linked, not copied, and the catalog does not infer a license
-- or production FEM capability that the official page does not state.
INSERT INTO implementations (
  implementation_id, library_name, solver_name, api_name, method_selector,
  language, license, commercial_model, free_use_conditions, open_source,
  os_support, problem_formats, variable_support, constraint_support,
  analytic_derivatives, autodiff, numerical_diff, sparse_support, parallelism,
  gpu_support, warm_start, callback, termination_controls, initialization,
  constraint_violation_reporting, optimality_info, dual_variables,
  optimality_gap, sensitivity_info, status_codes, major_options,
  default_safety, documentation_quality, beginner_usability,
  maintenance_status, last_release, last_verified, official_docs_url,
  official_repo_url, usage_example, notes, supported_method_ids,
  implementation_differences, source_ids, confidence
) VALUES (
  'I_TOPOPT_88_MATLAB',
  'DTU TopOpt',
  'top88 educational MATLAB code',
  'top88(nelx,nely,volfrac,penal,rmin,ft)',
  'top88',
  'MATLAB',
  'source-specific terms; not stated on the official download page',
  'unknown',
  'The official page offers the code for engineering education; verify redistribution terms separately.',
  'unknown',
  'MATLAB-compatible environment; platform matrix not published',
  'minimum-compliance topology optimization teaching grids',
  'continuous element-density field',
  'volume fraction; density bounds; fixed linear-elastic FEM state equation',
  'yes; analytic compliance sensitivity',
  'no',
  'no',
  'yes; vectorized finite-element assembly',
  'no',
  'no',
  'yes; initial density field',
  'no structured callback API',
  'design-change tolerance and source-level iteration loop',
  'uniform density at the requested volume fraction',
  'volume fraction and design-change history',
  'stationarity diagnostic only; no global certificate',
  'OC volume multiplier is internal to the update',
  'no',
  'yes; compliance sensitivity and density filtering',
  'no structured status API',
  'nelx;nely;volfrac;penal;rmin;filter_type',
  'educational code; independent verification required',
  'high',
  'high',
  'active_docs_verified',
  'official page updated 2026-04-20',
  '2026-07-24',
  'https://www.topopt.mek.dtu.dk/apps-and-software/efficient-topology-optimization-in-matlab',
  '',
  'top88(120,40,0.5,3.0,3.5,1)',
  'Bounded to the official 88-line teaching implementation. It does not represent a production FEM package, general MMA implementation, stress or buckling constraints, or manufacturing validation.',
  'M_SIMP_TOPOLOGY;M_DENSITY_FILTER;M_OC_TOPOLOGY',
  'The downloadable variants differ in density/PDE/projection filtering; record the exact file and parameters.',
  'S097;S098;S099',
  'high'
);

INSERT INTO method_implementation_map (
  method_implementation_map_id, method_id, implementation_id, support_level,
  api_name, method_selector, implementation_notes, limitations, source_ids,
  confidence, last_verified
) VALUES
(
  'MIM_TOPOPT_88_SIMP', 'M_SIMP_TOPOLOGY', 'I_TOPOPT_88_MATLAB', 'native',
  'top88(nelx,nely,volfrac,penal,rmin,ft)', 'top88',
  'The density field, SIMP penalization, compliance objective, volume fraction, and finite-element state solve are explicit in the teaching code.',
  'Educational rectangular-grid compliance example; it does not establish mesh independence, strength, buckling, manufacturing feasibility, or production solver performance.',
  'S097;S098;S099', 'high', '2026-07-24'
),
(
  'MIM_TOPOPT_88_FILTER', 'M_DENSITY_FILTER', 'I_TOPOPT_88_MATLAB', 'native',
  'top88(nelx,nely,volfrac,penal,rmin,ft)', 'ft',
  'The official top88 page documents density filtering and links PDE and projection-filter variants separately.',
  'Filter choice and radius are modeling decisions; lower checkerboard score does not prove mesh-independent physics.',
  'S099', 'high', '2026-07-24'
),
(
  'MIM_TOPOPT_88_OC', 'M_OC_TOPOLOGY', 'I_TOPOPT_88_MATLAB', 'native',
  'top88(nelx,nely,volfrac,penal,rmin,ft)', 'OC update loop',
  'The teaching code performs an Optimality Criteria density update for the single volume-constrained compliance problem.',
  'This mapping does not extend OC to arbitrary nonlinear or multiple constraints and does not imply support for MMA.',
  'S097;S098;S099', 'high', '2026-07-24'
);
