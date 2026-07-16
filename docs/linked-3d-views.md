# Linked 3D views

Issue #80 introduces 3D only where height adds a concrete reading task. It does not replace the established 2D views.

## Gradient and Nelder–Mead

- The linked surface consumes the same `AlgorithmTrace`, objective metadata, and playback frame as the 2D renderer.
- A Gradient frame selects its `iterate`. A Nelder–Mead frame selects the simplex vertex with the smallest objective value.
- Selecting a trajectory point seeks the shared playback controller; there is no independent 3D timeline.
- The camera control changes azimuth only. It never changes the data or the selected frame.

## Projection disclosure

The renderer uses an orthographic projection. `x` and `y` are normalized from `objective.display_range`; `f(x, y)` is clipped to the declared z range and displayed with `log1p` height normalization. The projection and normalization are stated in the figure caption and accessible description.

The existing 2D contour or frame snapshot remains the precision-first fallback, especially on mobile. The 3D view is an additional shape-and-trajectory cue, not a source of exact coordinate readings.

## Accessibility and mobile

- Every trajectory point is keyboard selectable and announces its frame target.
- The SVG has a title and description containing the current coordinates and objective value.
- At narrow widths the camera control stacks above the surface, and the view must not create horizontal overflow.
