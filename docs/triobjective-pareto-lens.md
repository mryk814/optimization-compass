# Tri-objective Pareto teaching lens

The Pareto learning slice keeps its analytic bi-objective result as the precision-first view. A linked tri-objective lens adds `f₃=(x−2)²+y²` to the same 9×9 decision grid so learners can practice reading a three-axis trade-off without replacing the canonical problem identity.

## Linked views

- The existing `f₁ × f₂` plot is the 2D precision fallback.
- The orthographic 3D scatter normalizes each axis by the sampled nadir and exposes camera azimuth.
- Parallel coordinates show all three exact axis directions and remain legible when depth is ambiguous or the viewport is narrow.
- The preference slider selects one sampled non-dominated point for all three views. The 3D camera never changes the selected data.

## Evidence boundary

`triobjective_lens.derivation_status` is `sampled_teaching_extension` and its reference status is `sampled_grid`. The generated artifact explicitly says that the 9×9 sample does not establish the continuous problem's true Pareto surface. No exact-front claim is inferred from the scatter.
