# Bayesian Optimization Theater

Issue #26 adds an executable, fixed-seed 1D expensive black-box experiment at
`/theater/bayesian-optimization`.

## Learning contract

- The optimizer receives only evaluated observations. The dashed true-objective curve is an
  explicitly labelled educational reference and is never used to choose a point.
- The renderer overlays GP surrogate mean, 95% uncertainty, observations, Expected Improvement,
  and the selected next point. Every frame is a complete snapshot after 3–10 evaluations.
- `exploit` uses `xi=0`; `explore` uses `xi=0.18`. Both can be replayed with either noiseless or
  small-noise (`sigma=0.08`) observations.
- Random search uses the same objective, domain, seed, and ten-evaluation budget. It is a baseline
  for this generated run, not an assertion that one method universally dominates.

## Generated artifacts

`optimization-compass export-site-data` writes four renderer payloads below `data/visualizations/`
and registers their path, byte length, and SHA-256 in the shared
`data/visualization-scenarios.json` authority. There is no second scenario index. The common
`VisualizationScenario 1.0.0` envelope owns title, method/run identity, budget, sources, and
limitations; the `surrogate_uncertainty 1.0.0` payload contains plot geometry and frame
explanations only.

The Python generator is deterministic at seed `2604`. Contract tests verify reproducibility,
surrogate updates, equal budgets, presets, and payload hashes. The TypeScript parser rejects unknown
envelope fields and unsupported renderer families.

## Accessibility and fallback

Playback controls are native buttons and a range input. Focus the player and use Left/Right to step
or Space to play/pause. The SVG has a title and description; a keyboard-accessible text alternative
lists every observation, the acquisition rationale, and the equal-budget result. The comparison
table is the static fallback when the animated chart is not useful.

## Limits

The plotted uncertainty is conditional on a stationary RBF GP with fixed hyperparameters. Kernel,
noise, and stationarity misspecification can make both uncertainty and acquisition misleading.
High-dimensional BO needs more observations and usually structured kernels, low-effective-
dimension methods, or trust-region variants. A finite-budget incumbent is not a global certificate.
