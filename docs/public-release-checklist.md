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
- [ ] Site typecheck, unit tests, production build, browser journeys, and
      accessibility checks pass against the artifact being deployed.

## Publication

- [ ] The release commit passed the complete CI pipeline; no artifact from a
      different commit is reused.
- [ ] GitHub release assets include the manifest and licensed dataset bundle.
- [ ] GitHub Pages was deployed from the validated artifact.
- [ ] Post-deploy smoke checks confirm routes, data fetches, manifest identity,
      and license links.
