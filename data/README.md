# Knowledge-base artifact

The runtime copy is stored at `src/optimization_compass/resources/knowledge.sqlite` so it is included in the Python wheel.

- Dataset version: `0.12.0`
- SHA-256: `fe0a7e67c764747390034b3c44b7f801e539cbd16db8abddbd08ee012d5b5b35`
- Runtime mode: SQLite read-only
- Data license: CC BY 4.0 (`../DATA_LICENSE`)

`src/optimization_compass/resources/release-authority.json` is the only editable authority for the target dataset version,
release date, and pinned base identity. Use `scripts/rebuild_dataset.py --stage` to rebuild all
distributions and site JSON twice and validate exact cross-format equivalence without changing
the published release. Publishing prepares the complete ZIP outside the repository and atomically
replaces the runtime database, `DATASET_VERSION`, compact release metadata/catalog, README facts, and
`site/public/data` from the same validated staged tree.

Complete historical version trees are distributed from GitHub Releases and indexed by
`releases/catalog.json`; they are not retained in an ordinary Git checkout. The v0.2.0 SQLite artifact
remains the immutable pinned build base and is the only retained historical distribution file. See
`docs/adr/0014-release-retention-and-external-bundles.md`.
New staged releases bundle the code/data/content notices in the release tree,
declare them in the release manifest, and include the data notice, CC BY 4.0
reference, and project notice in the deterministic CSV ZIP. The tracked v0.2.0
artifact predates that packaging change and remains immutable.

The migrations and seeds under `data/migrations/` and `data/seeds/` are staged build inputs. They are
applied in registered order to the pinned v0.2.0 base; historical distribution files are never build
inputs.
