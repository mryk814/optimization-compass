# Metadata responsibilities

This decision record defines the single owner for every Optimization Atlas metadata class.
The purpose is to keep rebuild inputs auditable without creating a second runtime authority.

## Authority boundaries

- The canonical released SQLite database owns IDs, relations, controlled vocabulary, view
  presets, support scope, learning edges, and objective/scenario metadata.
- SQL migrations and JSON seeds are auditable build inputs. They are applied to a pinned
  release and validated, but are not a second runtime authority.
- Markdown frontmatter owns article and case metadata plus canonical references. Markdown
  bodies own prose, mathematics, code, and citations.
- The Python registry owns executable objective and algorithm implementations. Expressions
  in SQLite are display-only and must never be evaluated as code.
- Trace JSON owns generated frames. Frames are regenerated and are never stored in SQLite.
- Site indexes and ViewSpec files are generated artifacts, not hand-edited authorities.

## Explicit states

`unknown`, `not_applicable`, and `unsupported` have different meanings and must be stored
explicitly. A blank string or `NULL` must never be used to infer one of these states.

- `unknown`: the answer has not been established.
- `not_applicable`: the field does not apply to this entity by design.
- `unsupported`: the feature is understood but deliberately outside the supported scope.

Optional foreign keys use SQL `NULL` only when their explicit status permits absence. For
example, an educational trace generator records `implementation_status=not_applicable` and
keeps `implementation_id` as SQL `NULL`.

## Release discipline

`scripts/rebuild_dataset.py --stage` copies the pinned release to temporary storage, applies
the migration and seed, recomputes release checks from live rows, exports every distribution,
round-trips every format, and rebuilds a second time to prove deterministic hashes. Stage mode
never changes published files, the runtime database, or `DATASET_VERSION`.

Publishing is a separate atomic gate. The staged manifest schema, version, and release date are
validated before artifact paths are resolved, then cross-checked with JSON/JSONL headers, SQLite
version history, the report, filenames, hashes, current runtime hash, and code version. Release-tree
verification explicitly requires the Atlas contract even when every Atlas table is absent. The data
directory, runtime database, and version file are all prepared and backed up before the first
replacement; any replacement failure restores all three targets.
