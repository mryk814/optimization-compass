# ADR 0009: Derived media is a deterministic projection of scenario artifacts

- Status: accepted
- Date: 2026-07-16
- Issue: #80

## Decision

Static thumbnails, PNG, and SVG are generated during the canonical site export. The renderer reads
the validated `VisualizationScenario`, its source artifact, and the authored guided terminal cue.
It writes files plus `DerivedMediaManifest 1.0.0`; page components consume that manifest instead of
inventing filenames or duplicating captions.

`SiteManifest 1.1.0` replaces 1.0.0 and exposes the derived-media manifest. There is no compatibility
parser for the old top-level shape.

The raster pilot uses a dependency-free RGB PNG encoder. This keeps bytes stable across local and CI
exports and avoids browser screenshot timing, font, device-scale, and animation variance. SVG owns
human-readable title/description text; both formats own the same geometry and provenance.

## Consequences

- Reusable media can be verified by SHA-256 and traced back to the exact source artifact.
- Alt text, caption, limitations, source IDs, licensing, and attribution travel with the file.
- Animated outputs will append files to the same entry/manifest contract.
- A visual redesign intentionally changes hashes and must be reviewed as an artifact change.

## Amendment (2026-07-17): video output does not scale beyond the pilot

The canonical lesson surface is the interactive Theater playback plus each scenario's static
summary and text alternative. Video files (GIF/WebM) are optional external-sharing derivatives,
not required learning artifacts, and the project does not plan to produce them for every scenario.

Consequences of this amendment:

- The `SCENARIO_NM_QUADRATIC` animation remains the only packaged video. New scenarios ship with
  interactive playback, a static summary, captions metadata where applicable, and a text
  alternative — without GIF/WebM outputs.
- The pilot's packaged-bytes-plus-input-hash mechanism (`derived_media.py` canonical constants) is
  frozen as-is. If a renderer change breaks the pilot's animation fingerprint, the decision point is
  to re-encode once or retire the animation — not to generalize the mechanism.
- Scaling video would require a separate design (manifest-driven identity, media bytes generated
  outside Git with a pinned encoder, hashes recorded in the manifest — in the spirit of
  ADR 0014's external bundles). Do not extend the per-scenario constants in code instead.
- The external video publishing playbook (`docs/external-video-publishing.md`) applies only to
  deliberately chosen representative scenarios, decided case by case.
