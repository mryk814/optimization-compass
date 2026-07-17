# Historical release backfill runbook

This runbook covers migration preparation for dataset 0.2.0 through 0.12.0. It does not upload an
asset, create or move a tag, modify the tracked release catalog, delete a distribution, change the
repository-size baseline, or enable immutable releases.

## Authority and provenance

[`data/releases/historical-backfill.json`](../data/releases/historical-backfill.json) is the reviewed
migration plan. Every entry fixes the version, date, reconstruction commit, reviewed artifact-set
origin, future tag name, historical verification profile, byte hashes, and line-ending
materialization profile. Only full lowercase commit SHAs are accepted. A branch, tag, `HEAD`, working
tree path, or symbolic ref is never an extraction input.

The packer reads release bytes with `git cat-file --batch`. It does not copy versioned artifacts from
the checkout. Some schema-2 manifests recorded CRLF bytes that were produced from LF-normalized Git
blobs. Such releases explicitly select `manifest-crlf-v1`; that profile permits CRLF materialization
only for the five license files, top-level JSON/JSONL/report/schema files, and generated Coverage
JSON/Markdown. The input must contain LF with no CR bytes, and the transformed bytes and SHA-256 must
exactly match the historical manifest. Every other path uses the Git blob unchanged. Dataset 0.11.0
and legacy 0.2.0 explicitly select `git-blob-v1`.

Dataset 0.2.0 predates the schema-2 manifest and bundled-license contract. Its artifact set comes from
`1bb71675c418dd6b561c02ba2bbe0fe6a2fdd418`; the reviewed reconstruction commit
`1963561360b08eae4baecf1bd93a903e97658c99` adds the five license files. Preparation verifies that
all 42 versioned 0.2.0 paths have identical Git blob bytes in both commits. The legacy profile checks
the eight manifest-listed artifacts, all 33 CSV directory members, the manifest database hash, and
the five plan-pinned supplemental license hashes. It does not pretend that the current site contract
existed in 0.2.0.

`source_commit` is the commit recorded in bundle/catalog identity and is the required target whenever
the corresponding tag exists. `reconstruction_commit` is the full commit read by the packer. When
they differ, every versioned manifest and artifact blob must be identical at both commits; only the
plan-pinned supplemental licenses may come solely from the reconstruction commit. Neither field
claims to be the first commit anywhere in Git history that contained each individual blob.

## Local prepare

Choose a new output directory outside the repository. The command fails if it already exists.

```powershell
uv run python scripts/release_bundles.py historical-prepare `
  --plan data/releases/historical-backfill.json `
  --catalog data/releases/catalog.json `
  --output-directory C:\tmp\optimization-compass-historical-backfill
```

Preparation is a batch transaction. It produces nothing at the requested path until all 14 release
trees, deterministic bundle indexes, ZIP inventories, hashes, and the catalog overlay pass. The final
directory contains:

- 14 `optimization_method_selection_database_v<version>_bundle.zip` files;
- `catalog.candidate.json`, which preserves the tracked catalog's current version;
- `backfill-report.json`, including every ZIP digest and every declared CRLF path.

The command never writes `data/releases/catalog.json`. Run it twice into two new directories and
compare the ZIP, candidate catalog, and report hashes before an upload is authorized.

Verify one local bundle independently:

```powershell
uv run python scripts/release_bundles.py historical-verify `
  --plan data/releases/historical-backfill.json `
  --bundle C:\tmp\optimization-compass-historical-backfill\optimization_method_selection_database_v0.12.0_bundle.zip
```

## Upload and remote verification

Asset upload belongs to the later publication phase, with two explicit paths.

- Releases 0.3.0 and 0.3.1 are already public and contain older loose assets. Do not draft, replace,
  or delete those releases or assets. First confirm that the new `_bundle.zip` name is absent. Add only
  that bundle, then verify it anonymously. If the same name already exists, accept it only when size,
  SHA-256, and inner identity are identical; otherwise stop.
- The other 12 releases are new. Upload the exact asset name from `catalog.candidate.json` to a draft,
  but first create the annotated `v<version>` tag without force at the plan's exact `source_commit`.
  Create the draft with an explicit target equal to that same commit. Download it through an
  authenticated command such as `gh release download`, and run `historical-verify` with the candidate
  catalog on the downloaded bytes. That gate checks the outer name, byte count, and SHA-256 before the
  ZIP inventory and inner release tree. Publish only after it passes, then run the anonymous verifier.

The new bundles reconstruct the internally consistent tracked manifest contract. They are not claimed
to be byte-for-byte aggregates of the older loose GitHub assets: the public 0.3.0 and 0.3.1 manifest
and release-identity files have historical line-ending/hash inconsistencies. Those loose assets remain
unchanged and non-authoritative; the catalog points to the verified complete bundle.

Do not publish the tracked catalog or delete a historical file merely because an authenticated upload
or download command succeeded. Verify each authenticated download before publication:

```powershell
uv run python scripts/release_bundles.py historical-verify `
  --plan data/releases/historical-backfill.json `
  --catalog C:\tmp\optimization-compass-historical-backfill\catalog.candidate.json `
  --bundle C:\tmp\authenticated-download\optimization_method_selection_database_v0.12.0_bundle.zip
```

After every bundle is publicly available, verify all 14 anonymously:

```powershell
uv run python scripts/release_bundles.py historical-verify-remote `
  --plan data/releases/historical-backfill.json `
  --catalog C:\tmp\optimization-compass-historical-backfill\catalog.candidate.json `
  --repo-root . `
  --remote origin
```

The verifier first confirms that the selected Git remote resolves to the `owner/repository` in the
reviewed plan. One strict `git ls-remote --tags` inventory must contain every planned lightweight or
peeled annotated tag at its exact `source_commit`; a missing, moved, duplicate, or malformed tag fails
before any asset download. It then streams into temporary storage, enforces catalog size before
accepting the download, checks SHA-256, permits only GitHub or GitHubusercontent redirect hosts, and
reruns the bundle inventory and version-specific release-tree checks. A 404, excess byte, digest
mismatch, unapproved redirect, or inner identity mismatch fails the entire operation. Normal tests and
staged builds never call either remote network path, and both Git and HTTP remote operations use a
finite timeout.

## Publication boundary and recovery

The later publication PR must follow this order:

1. prepare the deterministic batch twice;
2. for public 0.3.0 and 0.3.1, preserve existing loose assets and add only an absent or identical
   bundle;
3. for the other 12 versions, create annotated tags without force at each reviewed `source_commit`,
   then create drafts with that exact explicit target;
4. upload the new bundles and verify authenticated downloads against both the candidate catalog's
   outer bytes and the reviewed inner tree;
5. publish the new releases, then run the remote tag gate and anonymous verification for all 14
   bundles;
6. review and commit the catalog overlay and Data UI together;
7. remove only remotely verified historical distributions while retaining the pinned 0.2.0 base;
8. lower the repository-size baseline and prove offline stage/test/package behavior;
9. enable immutable releases only after the migrated public surface is complete.

If any asset or remote verification fails, leave the tracked catalog, historical files, and size
baseline unchanged. Keep a new failed upload in draft; do not alter an existing public release to mimic
that rollback. If a same-name remote asset already exists with different bytes, stop and never overwrite
it. Published immutable mistakes require a new dataset version and tag.
