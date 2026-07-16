# Visualization task-based evaluation

Date: 2026-07-16  
Dataset: `0.10.0`  
Scope: issue #80 selective 3D pilots and derived media  
Method: scripted task completion plus responsive/accessibility inspection; this is not a human comprehension study.

## Comparison

The control is the existing 2D precision view. The treatment adds a linked orthographic 3D view while keeping the same 2D view, frame/preference state, exact-value panels, and text alternative.

| Task | 2D control | Linked 3D + fallback | Evidence |
|---|---|---|---|
| Identify the optimization goal on first load | Complete | Complete | lesson heading and direction cues remain visible |
| Move to a known frame and recover the same selection | Complete | Complete | playback URL and `data-current-frame` update from a 3D trajectory point |
| Read exact current coordinates/objectives | Complete | Complete | 2D caption/value panels remain the precision source |
| Explain the third objective in the Pareto pilot | Not available | Complete | three formulas, 3D axes, exact values, and parallel coordinates |
| Change preference without desynchronizing views | Complete for f₁/f₂ | Complete for all three views | one weight slider drives 2D, 3D, and parallel selection |
| Use the primary task at 375 px without horizontal overflow | Complete | Complete | `scrollWidth <= clientWidth`; linked views stack |
| Operate frame/preference/camera controls by keyboard | Complete | Complete | native range controls and focusable trajectory points |
| Recover meaning without motion or color alone | Complete | Complete | persistent 2D fallback, shape/text cues, SVG title/description, transcript/captions |

Result: the linked treatment adds the third-axis and surface-shape tasks without removing a task completed by the 2D control. It does not demonstrate that learners understand faster or remember more. Therefore 3D remains selective and additive; 2D linked views remain the default authority.

## Automated task evidence

`site/e2e/visualization-task-evaluation.spec.ts` verifies three end-to-end tasks:

1. Nelder–Mead 3D trajectory selection seeks the shared playback frame while the 2D contour remains present.
2. The sampled three-objective view exposes 3D, parallel coordinates, exact values, a visible evidence limitation, keyboard preference/camera controls, and no 375 px overflow.
3. The WebM loads with a poster and WebVTT caption track, while GIF and transcript remain independently discoverable.

Unit/contract checks cover projection rotation, shared selection, deterministic media hashes, manifest provenance, and sampled-front dominance. The browser inspection also confirmed WebM decode with no media error and one text track.

## Adoption decision

- Keep the Gradient/Nelder–Mead surface and sampled three-objective lens as pilots.
- Do not introduce a site-wide 3D engine from this result.
- Prefer the 2D precision view on first load when occlusion, power use, or screen width harms the task.
- A future human test should ask participants to explain goal/current/best/terminal reason and the third-objective trade-off, then compare accuracy and time between 2D-only and linked conditions.
