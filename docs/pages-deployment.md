# Validated GitHub Pages deployment

GitHub Pages is published only by `.github/workflows/ci.yml`. The former independent Pages
workflow was removed so validation and publication cannot select different commits or rebuild the
site along separate paths.

## One artifact pipeline

`validate_pages_artifact` checks out the workflow commit once and performs the complete gate:

1. install the locked Python and Node.js dependencies;
2. run Python lint, formatting, mypy, and the full test suite;
3. delete and regenerate `site/public/data`, then require zero tracked drift;
4. run database, content, licensing, deterministic two-stage rebuild, and generated-data checks;
5. run Python/TypeScript recommendation parity;
6. run site typecheck and unit tests, then build `site/dist`;
7. stamp `site/dist/deployment.json` and verify the exact directory locally; and
8. upload that directory once as the `github-pages` artifact.

The deployment identity records the workflow commit SHA, dataset version, release date, database
SHA-256, and Pages base path. Its commit SHA is `${{ github.sha }}` for the checked-out workflow
commit; its dataset fields come from the built `data/release.json`. A mismatch in any generated
JSON asset, built HTML reference, or license path rejects the artifact before upload.

Pull requests run the same artifact pipeline and retain the Pages-format `github-pages` artifact,
but the deploy job is skipped. Downloading that artifact yields `artifact.tar`; extract it and run
the same generic seam used by CI:

```bash
python scripts/pages_artifact.py verify-local \
  --root extracted-artifact \
  --expected-commit-sha <40-character-sha> \
  --expected-dataset-version <x.y.z>
```

The browser E2E job `needs: validate_pages_artifact`, downloads the `github-pages` artifact from
the same workflow run, extracts its single `artifact.tar`, and verifies that exact directory instead
of rebuilding it. The deploy job requires this browser job in addition to validation and Python
compatibility, so a failed journey, console assertion, responsive check, or axe scan blocks
publication. Workflow structure tests keep the artifact name and single-upload contract explicit.
Failure evidence is retained as `playwright-failure-<commit SHA>` with screenshots, traces, console
logs, JUnit output, and the HTML report.

## Deployment and post-deploy smoke

Only a push to `main` may enter `deploy`. It requires both the validated artifact job and the
Python 3.13 compatibility job. `actions/deploy-pages` consumes the `github-pages` artifact from the
same workflow run; it never checks out and rebuilds another directory. Deployment and smoke share
the `github-pages` concurrency lock, so a later deployment cannot replace the site during smoke.

After deployment, `scripts/pages_artifact.py smoke-remote` retries propagation and requires the
public `deployment.json` to match the validated commit SHA and dataset version. It checks these
public hash-route URLs:

- `/`
- `/#/map`
- `/#/diagnose`
- `/#/theater/nelder-mead`
- `/#/gallery`

It also parses and version-checks:

- `data/release.json`
- `data/manifest.json`
- `data/views/problem-structure.json`
- `data/content.json`
- `data/gallery.json`
- `data/comparisons.json`
- `data/traces/index.json`

Every license path declared by the deployed site manifest must return a non-empty file.

URL fragments are not transmitted in HTTP requests. The post-deploy hash-route loop therefore
proves that each public URL resolves to the validated application shell, assets use the configured
base path, and deployment/data identity is current; it does not claim to exercise client-side
route rendering. #18 owns browser-level route semantics and accessibility against the extracted
`artifact.tar` from this same workflow run.

## Failure and rollback

- Validation, regeneration, parity, compatibility, build, or local artifact failure: `deploy` is
  skipped. The last successful Pages deployment remains active.
- Artifact upload or Pages deployment failure: no unvalidated fallback is uploaded. Inspect the
  failed run, fix the source, and let the complete pipeline create a new artifact.
- Post-deploy smoke failure: treat the new deployment as bad even if the deploy step succeeded.
  Prefer reverting the bad commit on `main` through a reviewed PR; the revert commit must pass the
  complete workflow and will publish a fresh, traceable artifact.
- Emergency restoration: identify the last known-good `Validated CI and Pages` run with
  `gh run list`, verify its commit SHA, and use `gh run rerun <run-id>` to rebuild and redeploy that
  historical commit through its original complete gate. Follow immediately with a source revert
  so `main`, the public deployment, and the next workflow run converge again.

Never upload a hand-built directory, reuse an artifact from a different commit, or bypass a failed
gate. The public `deployment.json` and workflow run must always identify the same source commit.
