# External video publishing playbook

External video is a derived distribution format, never the authority for an Optimization Atlas lesson. The canonical `VisualizationScenario`, artifact, guided story, sources, limitations, and media manifest remain the inputs and the route back into Atlas.

## Choose the format

| Format | Length | One viewer task | Required structure |
|---|---:|---|---|
| Visual Short | 30–60 seconds | Recognize one important transition | goal → before/after → interpretation → canonical URL |
| Concept video | 2–4 minutes | Explain the mechanism and its main limitation | problem → observables → transition → result → limitation |
| Deep dive | 6–12 minutes | Connect equations, parameters, failure, and implementation | formulation → trace → contrast → guarantee boundary → sources |

Do not stretch one scenario to fit every format. A Short uses one authored milestone; a Concept video may use the complete guided story; a Deep dive may link multiple canonical scenarios while preserving each identity.

## Required publishing bundle

Before upload, retain these fields beside the rendered file:

- Atlas canonical URL and scenario ID;
- dataset version, artifact contract/version, and renderer contract/version;
- narration/story version and the exact frame indices/duration;
- source IDs and links back to the Atlas source pages;
- limitations and projection disclosure;
- transcript, WebVTT captions, alt/thumbnail text;
- license, attribution, file SHA-256, and the media-manifest path.

The bundle is valid only when its media files match the byte lengths and hashes in `data/media/manifest.json`.

## Description template

```text
[One-sentence phenomenon and viewer task]

Open the canonical interactive lesson:
{ATLAS_CANONICAL_URL}

Scenario: {SCENARIO_ID}
Dataset: {DATASET_VERSION}
Artifact: {ARTIFACT_CONTRACT} {ARTIFACT_VERSION}
Renderer: {RENDERER_FAMILY} {RENDERER_VERSION}
Story: {NARRATION_VERSION}

What this rendering does not establish:
{LIMITATIONS}

Sources: {SOURCE_IDS_AND_ATLAS_SOURCE_URLS}
Transcript: {TRANSCRIPT_URL}
Captions: {CAPTIONS_URL}
License / attribution: {LICENSE_AND_ATTRIBUTION}
Media SHA-256: {HASH}
```

The first two description lines must make sense without expanding the description. Put the canonical URL before promotional copy.

## Captions, transcript, and storyboard

- Start from authored narration milestones; do not add a video-only explanation that cannot return to Atlas.
- Captions must describe the operation and decision, not merely repeat labels visible on screen.
- Keep a plain-text transcript in the Atlas media bundle so search and learning pages can index it.
- Add spoken descriptions for changes otherwise conveyed only by color, depth, or motion.
- Respect reduced-motion intent when deriving a loop: cuts or held keyframes are preferable to rapid camera movement.

## Versioning and corrections

The published identity is `(scenario ID, dataset version, artifact version, renderer version, narration version, media hash)`. If any member changes, render and publish a new external asset. Do not silently relabel an old upload as current.

For a correction that changes meaning or evidence:

1. mark the old description as superseded;
2. link the replacement and its canonical Atlas URL;
3. retain the old version/hash in the release record;
4. update transcript and captions together;
5. never delete the limitation solely to fit a shorter format.

Platform metrics such as views and watch time do not change the canonical ranking or claims in Atlas.

## Pre-publish checklist

- [ ] The video answers one declared viewer task.
- [ ] Canonical URL, scenario, dataset, versions, sources, and limitation are present.
- [ ] Transcript and captions match the uploaded cut.
- [ ] Thumbnail/alt text describes the phenomenon without overclaiming.
- [ ] Projection, normalization, and sampled-vs-exact status are visible where applicable.
- [ ] Hash, license, and attribution match the media manifest.
- [ ] Mobile legibility and a captions-on playback pass were checked.
- [ ] The Atlas lesson remains complete if the external video disappears.
