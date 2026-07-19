# Validated GitHub Pages deployment

GitHub Pages is published only by `.github/workflows/ci.yml`. The former independent Pages
workflow was removed so validation and publication cannot select different commits or rebuild the
site along separate paths.

## One artifact pipeline

`validate_pages_artifact` checks out the workflow commit once and performs the complete gate:

1. install the locked Python and Node.js dependencies;
2. use `select-validation-task` to classify pull-request paths as `docs`, `tier-a`, `content-ready`, `pr-fast`, or `tier-b`; pushes, scheduled runs, and manual runs select `tier-b`;
3. for `content-ready` and Tier B, delete and regenerate `site/public/data`, then require zero tracked drift;
4. run the selected registry task; unknown paths fail safe to Tier B rather than silently receiving a fast gate;
5. verify README facts and repository size for every task, and source health plus zero generated
   drift for Tier B;
6. retain `site/dist` for non-documentation pull-request and nightly browser jobs;
7. on `main`, stamp `site/dist/deployment.json` and verify the exact directory locally; and
8. on `main`, upload that directory once as the `github-pages` artifact.

The full Python regression suite is required for backend, canonical data, schema, generator,
release, backend-test, and unknown-path pull requests, and for every main/scheduled/manual Tier B
run. Draft/prose content uses Tier A; published content and deterministic indexes use
`content-ready`; site, workflow, validation-contract, and documentation-only pull requests use the
smaller authoritative task that owns their surface. The browser job runs tagged critical journeys on non-doc pull
requests. On `main`, the same critical journeys plus the axe route matrix block publication. A
scheduled/manual nightly job runs the full
desktop/mobile Playwright suite against the validated artifact and stays visibly red until every
quarantined legacy expectation has been repaired.

The deployment identity records the workflow commit SHA, dataset version, release date, database
SHA-256, and Pages base path. Its commit SHA is `${{ github.sha }}` for the checked-out workflow
commit; its dataset fields come from the built `data/release.json`. A mismatch in any generated
JSON asset, built HTML reference, or license path rejects the artifact before upload.

Pull requests run the same validation/build pipeline and retain `site/dist` as
`validated-site-<commit SHA>`, but the Pages-format artifact and deploy job remain main-only.
The browser job downloads that artifact without rebuilding it. On `main`, it instead downloads the
Pages-format `github-pages` artifact, extracts `artifact.tar`, and tests the exact publishable tree:

```bash
python scripts/pages_artifact.py verify-local \
  --root extracted-artifact \
  --expected-commit-sha <40-character-sha> \
  --expected-dataset-version <x.y.z>
```

The browser E2E job `needs: validate_pages_artifact` and never rebuilds the site. The deploy job
requires this browser job in addition to validation, so a failed journey, console assertion,
responsive check, or axe scan blocks publication. Workflow structure tests keep both artifact
paths and the single Pages upload contract explicit.
Failure evidence is retained as `playwright-failure-<commit SHA>` with screenshots, traces, console
logs, JUnit output, and the HTML report.

The full suite runs daily at 02:30 JST and on `workflow_dispatch`. Known failures are never silently
skipped: the nightly job fails, retains `playwright-nightly-failure-<commit SHA>`, and each failure
family must have an owner, cause classification, target date, and explicit exit condition in GitHub
Issues. Removing a spec from the suite is not a quarantine mechanism.

## Deployment and post-deploy smoke

Only a push to `main` may enter `deploy`. It requires the validated artifact job and the Browser E2E
job. `actions/deploy-pages` consumes the `github-pages` artifact from the same workflow run; it never
checks out and rebuilds another directory. Deployment and smoke share the `github-pages` concurrency
lock, so a later deployment cannot replace the site during smoke.

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

- Validation, regeneration, parity, build, or local artifact failure: `deploy` is
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
