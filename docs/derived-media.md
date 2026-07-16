# Derived visualization media

`optimization-compass export-site-data` generates reusable media under `data/media/`. The index is
`data/media/manifest.json` (`DerivedMediaManifest 1.1.0`) and is discoverable from
`SiteManifest 1.1.0` as `derived_media`.

The first pilot is `SCENARIO_NM_QUADRATIC`:

- `thumbnail.png` (600×338) for cards and sharing previews;
- `static.png` (1200×675) for raster reuse;
- `static.svg` (1200×675) for accessible scalable reuse.
- `animation.gif` (640×360) for portable looping previews;
- `animation.webm` (640×360) for efficient browser playback;
- `captions.vtt` and `transcript.txt` for bilingual captions and non-video reading.

The PNG files use a small standard-library renderer and encoder. They do not depend on a browser,
OS font rasterization, wall-clock time, or random state. Re-exporting the same dataset produces the
same bytes. The SVG contains title/description text and the same canonical trajectory and terminal
simplex.

The animation combines authored story frames with ten evenly sampled trace frames at a fixed 0.6
seconds per frame. GIF and WebM are canonical packaged projections of those rendered PNG frames.
The exporter hashes the complete ordered frame input before copying the packaged bytes, so a trace
or renderer change fails loudly until the media is regenerated and reviewed. This keeps site-data
exports byte-identical across operating systems and ffmpeg builds while preserving the exact source
artifact and frame provenance.
The WebM player uses the static thumbnail as its poster and attaches the WebVTT file as a caption
track. The plain-text transcript remains usable without video playback.

Every manifest entry records scenario and dataset identity, artifact and renderer versions, source
artifact path/hash, frame, viewport/camera, guided narration version, sources, limitations, bilingual
alt/caption text, animation frame indices and duration, caption/transcript assets, license,
attribution, byte length, and SHA-256 for each output. Consumers should
verify file byte length and hash before publishing or caching it.

All formats share one manifest; there is no parallel animation index or independent timeline.
