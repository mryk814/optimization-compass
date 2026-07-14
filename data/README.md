# Knowledge-base artifact

The runtime copy is stored at `src/optimization_compass/resources/knowledge.sqlite` so it is included in the Python wheel.

- Dataset version: `0.2.0`
- SHA-256: `4c916f293ec7ce5ce452297238f455bb23e971ae2ef38a92eaeafc3c79f02d13`
- Runtime mode: SQLite read-only
- Data license: CC BY 4.0 (`../DATA_LICENSE`)

Use `scripts/rebuild_dataset.py --stage` to rebuild all distributions twice and validate exact
cross-format equivalence without changing this published release. Publishing is a separate
atomic operation and must use a new version only after the staged manifest, runtime hash, and
`DATASET_VERSION` agree.

New staged releases bundle the code/data/content notices in the release tree,
declare them in the release manifest, and include the data notice, CC BY 4.0
reference, and project notice in the deterministic CSV ZIP. The tracked v0.2.0
artifact predates that packaging change and remains immutable.

The atlas migration and seed under `data/migrations/` and `data/seeds/` are staged build inputs.
They intentionally do not change the published v0.2.0 artifacts in Task 11A.
