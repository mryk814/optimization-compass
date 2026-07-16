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
