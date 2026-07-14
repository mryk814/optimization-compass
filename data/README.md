# Knowledge-base artifact

The runtime copy is stored at `src/optimization_compass/resources/knowledge.sqlite` so it is included in the Python wheel.

- Dataset version: `0.3.1`
- SHA-256: `2fe6578731db3688697def28bacb9c3f4753c6549c718792a83ba2a54061c602`
- Runtime mode: SQLite read-only
- Data license: CC BY 4.0 (`../DATA_LICENSE`)

`src/optimization_compass/resources/release-authority.json` is the only editable authority for the target dataset version,
release date, and pinned base identity. Use `scripts/rebuild_dataset.py --stage` to rebuild all
distributions and site JSON twice and validate exact cross-format equivalence without changing
the published release. Publishing atomically replaces the distribution tree, runtime database,
`DATASET_VERSION`, and `site/public/data` from the same validated staged tree.

The v0.2.0 artifacts remain the immutable pinned base. Published v0.3.0 artifacts also remain
immutable. Versioned v0.3.1 artifacts add the coverage migration, metadata, release identity,
and exact site-data tree.
New staged releases bundle the code/data/content notices in the release tree,
declare them in the release manifest, and include the data notice, CC BY 4.0
reference, and project notice in the deterministic CSV ZIP. The tracked v0.2.0
artifact predates that packaging change and remains immutable.

The atlas migration and seed under `data/migrations/` and `data/seeds/` are staged build inputs.
They are applied in order to v0.3.1 while the pinned v0.2.0 and published v0.3.0 artifacts remain
immutable.
