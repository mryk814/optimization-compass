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
| Pinned 0.2.0 base SQLite | retained temporarily | retained | Required by the current staged build |
| Current runtime SQLite and `DATASET_VERSION` | retained | retained | Python runtime authority |
| Current generated Pages data | retained | retained | Current site only |
| Current manifest, release identity, report, schema | retained | retained | Compact verification and documentation |
| Full JSON/JSONL/CSV/Excel and versioned site-data | not added after 0.12.0 | retained | Download distribution |
| Historical compact catalog | retained | bundled at publication time | Generated public discovery input |
| Licenses and attribution | retained at project root | included in every bundle | Never fetched separately for verification |
| Small focused fixtures | retained | not required | Tests must not become historical bundles |

## Publication and failure boundaries

This ADR separates deterministic local preparation from external publication. A later migration step
will upload and verify historical bundles, populate the catalog, remove historical working-tree copies,
and enable immutable GitHub Releases. This first step does not delete a historical file, create or move a
tag, publish an asset, or enable a repository setting.

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
across line-ending settings and is the CI gate. PR A grandfathers the exact 0.2.0–0.12.0 distribution
set and rejects a new tracked version or growth beyond that baseline. The migration PR will lower the
allowlist and byte ceiling after remote assets have been independently verified.

## Consequences

The ordinary checkout remains self-contained for development, packaging, Pages generation, tests, and
staged release rebuilds, while complete historical downloads move to the surface designed to distribute
them. Future releases require an explicit source commit and tag instead of inferring provenance. Release
coordination becomes a documented two-surface transaction, but partial publication cannot silently
redefine the current runtime dataset.
