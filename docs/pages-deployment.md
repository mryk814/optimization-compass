# Pages artifact verification

The repository no longer contains a GitHub Actions or Pages deployment workflow. A push or PR
therefore does not validate, upload, or deploy a site. Existing public Pages content may still be
served, but it is not evidence that the current source commit has been published.

The artifact and checkpoint scripts remain available for explicit validation and publication work.
They do not establish a deployment pipeline or change repository settings.

## Verify one built artifact

Run the applicable validation task, then build the site once. `npm --prefix site run build` includes
TypeScript checks. Browser checks can reuse that build with `npm --prefix site run test:e2e:artifact`;
`test:e2e` also builds, so do not run both paths for the same artifact.

For an artifact deliberately prepared for publication, stamp and verify its actual source identity:

```bash
uv run python scripts/pages_artifact.py stamp \
  --root site/dist --commit-sha <40-character-source-sha>
uv run python scripts/pages_artifact.py verify-local \
  --root site/dist --expected-commit-sha <40-character-source-sha> \
  --expected-dataset-version <x.y.z>
```

The identity includes the source commit, dataset version, release date, database SHA-256, and base
path. Verification rejects inconsistent data identity, asset references, or license paths. Use the
same verified directory for browser checks and any separately authorized publication.

## Verify a published site

After an authorized deployment, `scripts/pages_artifact.py smoke-remote` checks public deployment
identity, data assets, license paths, and application-shell availability. HTTP requests do not send
URL fragments, so this check does not prove client-side route rendering or accessibility; those
belong to the browser suite against the built artifact.

`scripts/pages_checkpoint.py` compares the local/remote commit, recorded workflow runs, and public
identity. Its workflow lookup describes the former `Validated CI and Pages` workflow. With no current
workflow, a missing run or stale public identity remains a blocker, not a reason to assume publication
succeeded or to rerun historical deployment jobs.

Do not upload a different tree after validation, stamp an unrelated SHA, or bypass an identity
failure. Publication and recovery require an explicit current process; this guide does not authorize
a deploy, a workflow restoration, or a repository-settings change.
