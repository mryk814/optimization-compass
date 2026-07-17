# Public release checklist

Complete every applicable item before publishing a dataset, GitHub release, or
GitHub Pages artifact.

## License and rights

- [ ] Root `LICENSE`, `DATA_LICENSE`, `CONTENT_LICENSE`, `CC-BY-4.0`, and
      `NOTICE` are present and linked from README.
- [ ] Code, data, and educational content are classified under the intended
      scope; mixed artifacts do not obscure the applicable license.
- [ ] Dataset manifest declares `MIT`, `CC-BY-4.0`, bundled notice paths, and
      the project attribution.
- [ ] Dataset release directory and deterministic CSV ZIP contain the required
      license and notice files.
- [ ] Site manifest license paths resolve in the production Pages artifact and
      the footer exposes them.
- [ ] `THIRD_PARTY_SOURCE_AUDIT.md` reflects the current source types and any
      redistributed third-party material.
- [ ] Every third-party quotation, figure, logo, screenshot, or substantial
      excerpt has a local exception notice and required attribution.
- [ ] Product and organization names are not presented as endorsement, and no
      unlicensed official logo is used.
- [ ] Release notes state the code/data/content license map and identify any
      exceptions.

## Artifact integrity

- [ ] `uv run python scripts/verify_licensing.py` passes.
- [ ] `uv run python scripts/rebuild_dataset.py --stage` completes twice with
      an identical tree hash.
- [ ] `verify_release_tree` validates manifest schema, bundled notices, ZIP
      entries, hashes, all format round-trips, and live database checks.
- [ ] Runtime database, dataset files, site data, manifest, and release tag use
      the same version identity.
- [ ] `uv run python scripts/verify_content.py` passes.
- [ ] `coverage.json` and `coverage.md` come from the same snapshot; broken references are
      separated from unbuilt expectations.
- [ ] Release notes use `coverage-diff` with explicit before/after snapshots, or state that no
      baseline was supplied.
- [ ] Site typecheck, unit tests, production build, browser journeys, and
      accessibility checks pass against the artifact being deployed.

## Publication

- [ ] The release commit passed the complete CI pipeline; no artifact from a
      different commit is reused.
- [ ] `scripts/repository_size.py --check` rejects a new complete distribution in the Git tree.
- [ ] The complete dataset ZIP was prepared outside the repository with an explicit source commit and
      matching `v<dataset version>` tag, then independently verified with `release_bundles.py verify`.
- [ ] The release catalog entry matches the database, canonical manifest, and complete ZIP hashes and
      byte size. Reusing a version with different metadata is rejected.
- [ ] External upload remains a draft until every asset digest and byte size has been checked. A failed
      upload does not authorize tracked catalog or retention changes.
- [ ] Historical migration follows the reviewed plan and
      [`historical-release-backfill.md`](historical-release-backfill.md): prepare twice from Git blobs,
      create new annotated tags without force at reviewed source commits, target drafts explicitly,
      verify authenticated downloads against candidate outer bytes and inner identity, preserve
      existing public loose assets, publish new releases, prove all remote tag targets, verify all
      complete bundles anonymously, then commit catalog/Data UI and cleanup.
- [ ] GitHub release assets include the manifest and licensed dataset bundle.
- [ ] GitHub Pages was deployed from the validated artifact.
- [ ] Post-deploy smoke checks confirm routes, data fetches, manifest identity,
      and license links.
- [ ] Public `deployment.json` matches the validated workflow commit SHA and dataset version.
- [ ] Pages failure and rollback follow [pages-deployment.md](pages-deployment.md); no artifact
      from another commit or hand-built fallback is uploaded.
