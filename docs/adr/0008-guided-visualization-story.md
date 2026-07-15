# ADR 0008: Guided stories are scenario data, not renderer copy

- Status: accepted
- Date: 2026-07-16
- Issue: #80

## Context

The Atlas has four useful visualization modes, but their responsibilities were implicit. Existing
narration milestones named what to inspect without controlling the relevant frame, focus, layers,
view, speed, or pause. Renderer-specific walkthrough code would make the same lesson drift across
interactive views and derived media.

## Decision

`VisualizationScenario 1.2.0` replaces 1.1.0 and may own a `GuidedStory 1.0.0`. A guided step binds
one canonical lesson milestone to an exact frame, authored annotation, observable focus, visible
observable layers, viewport/camera preset, playback speed, and auto-pause. These values are parsed
strictly in Python and TypeScript. The UI may present them differently but does not invent them.

The four modes have distinct jobs:

- Guided: one authored interpretation path with cues and automatic pauses.
- Explore: free controls for changing frame, parameters, layers, and view.
- Compare: synchronized evidence under an explicit fairness contract; it does not rank contrast-only runs.
- Cinema: distraction-free playback and derived media from the same scenario, renderer, and story identity.

The first pilot is the canonical two-dimensional Nelder–Mead quadratic scenario. `guided_story` is
null for scenarios not yet authored; null means the capability is unavailable, not a legacy UI
fallback. Subsequent #80 slices add stories across renderer families.

## Accessibility and motion

Every cue is a native button and remains usable by keyboard. Cue activation pauses before seeking.
OS reduced-motion preferences continue to disable automatic playback; focus and layer changes are
instantaneous when reduced motion is requested. Story annotations are live status text, while the
renderer retains a complete text alternative.

## Compatibility

This is a synchronized contract replacement. There is no 1.1 parser. Existing scenario IDs,
artifact paths, trace contracts, and deep links remain stable.
