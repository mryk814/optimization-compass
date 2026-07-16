# Derived visualization media

`optimization-compass export-site-data` generates reusable media under `data/media/`. The index is
`data/media/manifest.json` (`DerivedMediaManifest 1.0.0`) and is discoverable from
`SiteManifest 1.1.0` as `derived_media`.

The first pilot is `SCENARIO_NM_QUADRATIC`:

- `thumbnail.png` (600×338) for cards and sharing previews;
- `static.png` (1200×675) for raster reuse;
- `static.svg` (1200×675) for accessible scalable reuse.

The PNG files use a small standard-library renderer and encoder. They do not depend on a browser,
OS font rasterization, wall-clock time, or random state. Re-exporting the same dataset produces the
same bytes. The SVG contains title/description text and the same canonical trajectory and terminal
simplex.

Every manifest entry records scenario and dataset identity, artifact and renderer versions, source
artifact path/hash, frame, viewport/camera, guided narration version, sources, limitations, bilingual
alt/caption text, license, attribution, byte length, and SHA-256 for each output. Consumers should
verify file byte length and hash before publishing or caching it.

Animated GIF/WebM outputs extend the same manifest in a later #80 slice; they do not introduce a
parallel media index.
