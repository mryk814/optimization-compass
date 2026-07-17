# Historical release packaging

Issue #155 separates two jobs that must not be conflated:

1. stop future full release bundles from accumulating in the ordinary Git working tree;
2. migrate already committed historical bundles to durable release/archive storage.

The first job is covered by the compact-release retention contract. This document covers an offline,
non-destructive preparation step for the second job.

## Safety properties

`scripts/package_historical_release.py`:

- reads an existing release manifest and the files it names;
- verifies SHA-256 and, when present, byte size before packaging;
- rejects absolute paths and parent-directory traversal;
- creates a deterministic ZIP with sorted entries, fixed timestamps, and fixed file modes;
- emits bundle hash, size, source-manifest hash, and file count;
- can write a machine-readable local catalog;
- performs no network access, Git deletion, release publication, or credential use.

A successful package is an upload candidate, not proof that an external archive has accepted or retained
it. Publication and removal from `main` remain separate reviewed operations.

## Verify a committed release without writing output

```bash
uv run python scripts/package_historical_release.py \
  --manifest data/optimization_method_selection_database_v0.11.0_manifest.json \
  --check-only
```

The command fails before producing output if a named file is absent or its hash/size has drifted.

## Create a deterministic bundle outside the repository

```bash
mkdir -p /tmp/optimization-compass-release-bundles
uv run python scripts/package_historical_release.py \
  --manifest data/optimization_method_selection_database_v0.11.0_manifest.json \
  --output-dir /tmp/optimization-compass-release-bundles \
  --catalog /tmp/optimization-compass-release-bundles/catalog.json
```

The output is named `optimization-compass-dataset-v<version>.zip`. Re-running into another empty
directory from identical inputs produces the same ZIP hash. Existing output is not replaced unless
`--overwrite` is explicit.

Multiple `--manifest` arguments may be supplied to generate one local catalog:

```bash
uv run python scripts/package_historical_release.py \
  --manifest data/optimization_method_selection_database_v0.10.0_manifest.json \
  --manifest data/optimization_method_selection_database_v0.11.0_manifest.json \
  --output-dir /tmp/optimization-compass-release-bundles \
  --catalog /tmp/optimization-compass-release-bundles/catalog.json
```

## Review before any upload

For each release:

- compare the emitted source-manifest hash with the committed manifest;
- independently hash the ZIP;
- inspect the ZIP member list and included licenses/attribution;
- confirm that no authoring input, secret, cache, or unrelated historical file was added;
- record intended external destination, object/version ID, retention policy, and public download URL;
- upload idempotently and verify the remote bytes against the local ZIP hash;
- test download and disaster-recovery instructions;
- update a generated release catalog only after remote verification succeeds.

## Review before any Git cleanup

Do not delete a committed historical bundle merely because a ZIP was created or uploaded. Cleanup needs
a separate PR proving:

- at least one durable remote copy exists and is hash-verifiable;
- license and attribution travel with the bundle;
- normal clone, test, stage, and current-runtime workflows do not read the files being removed;
- existing URLs have redirects or a documented deprecation path;
- rollback and missing-asset behavior are tested;
- Git history is not rewritten unless separately approved.

## Suggested migration sequence

```text
manifest verification
→ deterministic local bundle
→ independent bundle inspection
→ external upload
→ remote hash/download verification
→ generated release-catalog update
→ consumer and rollback tests
→ separate source-tree cleanup PR
```

This sequence intentionally keeps external publication failure from redefining or partially deleting the
canonical release.
