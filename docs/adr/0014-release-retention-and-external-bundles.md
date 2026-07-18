# ADR 0014: Complete release bundles live outside the Git working tree

- Status: accepted
- Date: 2026-07-17
- Issue: #155
- Related: #143, #145, #154

## Context

Optimization Compass builds one immutable dataset identity into SQLite, JSON, JSONL, CSV, Excel,
schema, report, site-data, manifest, and license distributions. Through dataset 0.12.0, every complete
version tree was also retained under `data/`. The tracked `data/` tree reached 294.47 MiB at 0.11.0
and 319.20 MiB of Git blob content at 0.12.0. Each recent version adds about 28 MiB even though
ordinary authoring, tests, and staged rebuilds do not read historical distributions.

The deterministic build currently does need the pinned 0.2.0 SQLite base. The Python package needs the
current runtime SQLite database, and Pages validation uses the current generated `site/public/data`
tree. Those are runtime/build inputs, not historical download retention.

Git history rewriting would make existing commit and citation references harder to reason about. Git
LFS would still store every changed generated object, adds quota and contributor-client behavior, and
cannot serve the Pages site. Complete versioned distributions are release assets, not source inputs.

## Decision

Stop adding complete dataset distributions to the Git working tree after 0.12.0. A future release is
prepared in a validated staged directory, packaged into one deterministic complete ZIP outside the
repository, and described by a compact release catalog entry. Atomic source publication promotes only:

- `src/optimization_compass/resources/knowledge.sqlite`;
- `src/optimization_compass/resources/DATASET_VERSION`;
- the current generated `site/public/data` tree;
- the generated README release facts;
- the current versioned manifest, release identity, report, and schema;
- `data/releases/catalog.json`.

The complete ZIP contains `bundle-index.json` and one versioned release-tree directory. The index fixes
the version, release date, source commit, version tag, canonical manifest hash, and the byte count and
SHA-256 of every included file. ZIP members are sorted and use the release date, fixed permissions, and
fixed compression settings. Preparing the same staged tree twice must produce identical bytes.

The catalog is compact and offline-verifiable. Every entry has an exact source commit, matching
`v<version>` tag, database hash, canonical manifest hash, complete-bundle URL/hash/size, and an explicit
nullable archival record. A version is immutable within the catalog. New entries are ordered by semantic
version and the last entry is current.

Normal tests and `scripts/rebuild_dataset.py --stage` never download a historical release. The complete
bundle output must resolve outside the repository. A publish command without an explicit 40-character
source commit, matching tag, and external output directory fails before changing tracked targets.

### Retention matrix

| Artifact class | Git working tree | Complete release asset | Notes |
|---|---|---|---|
| Authoring inputs, migrations, seeds, content, registries | retained | optional source archive | Canonical editable inputs |
| Pinned 0.2.0 base SQLite | retained | retained | Required by the current staged build |
| Current runtime SQLite and `DATASET_VERSION` | retained | retained | Python runtime authority |
| Current generated Pages data | retained | retained | Current site only |
| Current manifest, release identity, report, schema | retained | retained | Compact verification and documentation |
| Historical full JSON/JSONL/CSV/Excel, SQLite, and versioned site-data | removed after remote verification | retained | Complete downloads are GitHub Release assets |
| Historical compact catalog | retained | bundled at publication time | Generated public discovery input |
| Licenses and attribution | retained at project root | included in every bundle | Never fetched separately for verification |
| Small focused fixtures | retained | not required | Tests must not become historical bundles |

## Publication and failure boundaries

This ADR separates deterministic local preparation from external publication. The migration step uploads
and verifies historical bundles before removing their tracked working-tree copies. Immutable GitHub
Releases remain a separate final setting change after the public surface is verified.

Bundle preparation happens before atomic source promotion. If staging, packing, catalog validation, or
target preparation fails, tracked targets remain unchanged. If replacement fails, data, runtime,
version, site data, and README are restored and the unpublished bundle is removed. Upload failures leave
the remote release in draft and do not authorize catalog publication. A same-version catalog entry may
be replayed only when every field is byte-for-byte identical; a different hash requires a new version.

Once release immutability is enabled, a bad published bundle is corrected with a new dataset version and
tag. It is never overwritten. Pages failure leaves the previous validated deployment active. Git history
is not rewritten by this policy; reverting the later cleanup can restore working-tree copies while the
external publication is investigated.

## Repository growth gate

`scripts/repository_size.py` reports both checkout bytes and Git-index blob bytes. The latter is stable
across line-ending settings and is the CI gate. After the 14 historical assets were independently
verified, the migration retains only the pinned 0.2.0 SQLite build input and lowers the allowlist and
byte ceiling to that exact Git blob size.

## Consequences

The ordinary checkout remains self-contained for development, packaging, Pages generation, tests, and
staged release rebuilds, while complete historical downloads move to the surface designed to distribute
them. Future releases require an explicit source commit and tag instead of inferring provenance. Release
coordination becomes a documented two-surface transaction, but partial publication cannot silently
redefine the current runtime dataset.

## Historical migration preparation

The accepted policy is implemented in phases. Phase A adds only the reviewed migration plan, exact Git
blob reconstruction, version-specific local verification, a current-preserving catalog candidate, and
anonymous remote verification. Its commands and failure boundaries are documented in
[`../historical-release-backfill.md`](../historical-release-backfill.md).

Historical extraction never reads checkout artifact bytes. Schema-2 releases whose manifests recorded
Windows CRLF bytes declare a closed materialization profile in the reviewed plan; only its strict path
classes may expand an LF-normalized Git blob, and the result must match the manifest byte count and
SHA-256. Undeclared mismatches fail. Dataset 0.2.0 uses a separate legacy profile and supplements its
unchanged artifact set with plan-pinned license blobs from a later reconstruction commit.

Phase A did not upload, mutate the tracked catalog, remove a historical distribution, lower the size
baseline, change Pages, create or move a tag, or change repository release settings. The later migration
performed those operations only after remote verification. New releases use draft upload, authenticated
download verification against candidate outer bytes and inner identity, publication, and then
anonymous verification. Their annotated tags are created without force at the reviewed source commit,
and draft creation names that commit as its explicit target. Existing public 0.3.0 and 0.3.1
keep their loose assets unchanged and receive only a missing or byte-identical complete bundle before
anonymous verification. Their tracked, internally consistent bundle reconstruction is the catalog
authority; it is not represented as a byte-for-byte aggregate of historically inconsistent loose
manifest/release-identity assets. Before download, the selected remote must identify the repository in
the reviewed plan and a single strict remote tag inventory must prove all 14 tags still target their
reviewed source commits. Catalog publication and cleanup wait until all 14 bundles pass anonymous
verification. Normal tests and staged builds do not contact the remote.
