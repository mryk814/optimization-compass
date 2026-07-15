# ADR 0006: Educational metadata belongs to VisualizationScenario

- Status: accepted
- Date: 2026-07-15
- Issue: #63

## Context

The renderer payloads already describe executable geometry, but the teaching intent was split
between page copy, captions, and renderer code. That made a new scenario or renderer require UI
copy changes and allowed static summaries to disagree with the interactive view.

## Decision

`VisualizationScenario 1.1.0` is the versioned authority for short, reusable educational metadata.
Every scenario owns:

- a bilingual learning objective and optional misconception;
- primary and secondary observables, success signals, and contrast/failure signals;
- the canonical renderer-independent narration milestones `start`, `first_change`,
  `pattern_visible`, and `termination`;
- comparison role, prerequisites, and recommended next scenarios;
- known-reference display policy;
- short static summary, text alternative, derived-media caption, and limitations.

Failure-contrast and sensitivity scenarios must provide both a misconception and at least one
failure/contrast signal. Every signal and narration step may reference only observables declared by
the lesson, and every lesson observable must be supplied by the artifact envelope.

The UI consumes one shared `ScenarioLessonPanel`; renderer pages do not own scenario-specific
teaching copy. Goal-cue reference visibility also comes from the scenario policy. The same envelope
is mandatory for future renderer families added by #50.

## Authority boundary

- `VisualizationScenario`: stable short teaching metadata and canonical relations.
- Markdown content: long-form explanation, derivation, and exercises.
- Trace or renderer payload: run values, frames, and geometry.
- UI components: generic presentation and runtime frame summaries only.

The generated scenario catalog is deterministic and versioned. SQLite does not duplicate this
short scenario catalog, and Markdown does not repeat its structured fields.

## Compatibility

This is a deliberate replacement of `VisualizationScenario 1.0.0`; there is no legacy parser or
parallel v2 catalog. Existing scenario IDs, artifact paths, trace contracts, and deep links remain
stable and are covered by regression tests. Consumers fail closed on any unsupported contract
version or unknown field.

## Consequences

Static summaries, text alternatives, captions, and interactive reading cues now share one authored
source. Adding a renderer family requires geometry-specific parsing but no new educational metadata
shape. A schema change requires a contract-version bump and synchronized Python/TypeScript parsers.
