# Knowledge change checklist

Use this checklist for pull requests that add or correct structured knowledge, content, cases, comparisons, problem instances, or visual learning assets.

Not every item applies to every PR. Mark non-applicable items explicitly rather than deleting them from the PR description.

## Scope

- [ ] I classified the change as prose/content, Gallery, comparison, problem instance, canonical knowledge, visualization, recommendation, or release work.
- [ ] The PR has one primary review concern and does not include unrelated cleanup.
- [ ] I identified the editable authority instead of patching generated output.
- [ ] I listed every changed stable ID.
- [ ] I checked for an existing entity or alias before creating a new ID.

## Authority and generated files

- [ ] I did not manually edit `knowledge.sqlite`, `DATASET_VERSION`, `site/public/data/**`, released distributions, or generated Trace/media files.
- [ ] Any committed generated files were produced by the documented deterministic workflow.
- [ ] Unexpected unrelated generated diffs are absent or explained.
- [ ] Method, implementation, problem, case, scenario, comparison, and content identities are not conflated.

## Sources and licensing

- [ ] Every material factual addition has a source/evidence trail.
- [ ] Sources are official documentation, official repositories, original papers, standards, or equivalent authoritative material.
- [ ] Qiita and Zenn are not used as sources.
- [ ] `last_verified` / `last_reviewed` reflects a real review date.
- [ ] Third-party text, diagrams, screenshots, logos, or code examples have been checked under `docs/licensing.md` and `NOTICE`.

## Semantics

- [ ] `unknown`, `not_applicable`, and `unsupported` are used deliberately.
- [ ] Library defaults are not presented as universal recommendations.
- [ ] Local, global, feasible, approximate, statistical, and certified outcomes are distinguished.
- [ ] Discretized-model claims are not presented as continuous-model guarantees without qualification.
- [ ] Candidate, conditional, and excluded method sets do not overlap.
- [ ] Failure, caveat, limitation, and switch conditions are stated where relevant.

## Existing-entity content

- [ ] The canonical draft was created with `author content method` or its identity was checked equivalently.
- [ ] `status: published` is used only after placeholders, sources, relations, review date, limitations, and failure/switch signals are complete.
- [ ] `ready content <content-id>` regenerated the public indexes and proved content, search, retrieval, entity-link, and route presence.
- [ ] The PR is for Atlas/Pages publication; it does not bump or publish a dataset version.

## Gallery case

- [ ] Problem, feature, question-answer, method, implementation, source, visualization, and comparison IDs exist.
- [ ] Conditional and excluded methods each have a concrete reason.
- [ ] `map_node_id` is backed by the question answers.
- [ ] The Python example is nonblank, minimal, and syntactically valid.
- [ ] The case distinguishes the real problem from a fixed educational instance or run.

## Comparison

- [ ] The comparison question is explicit.
- [ ] Fixed and changed factors are explicit.
- [ ] Initial condition, seed, budget, stopping, tuning, and synchronization are explicit.
- [ ] Metrics and status interpretation are explicit.
- [ ] Fairness note and caveat are present.
- [ ] Ranking eligibility is justified; failure/sensitivity contrasts are not treated as rankings.

## Problem, scenario, and visualization

- [ ] Problem-suite and executable registry keys match exactly.
- [ ] Available oracles and constraint behavior are explicit.
- [ ] Known-reference status and optimizer-visible information are distinct.
- [ ] Scenario identity is canonical, derived, or generated-only as appropriate.
- [ ] Budget, seed, tuning, stopping, and implementation mapping are explicit.
- [ ] Success and failure signals are observable.
- [ ] A static summary and text alternative carry the educational meaning.
- [ ] An existing renderer/artifact contract is reused unless a new contract was deliberately designed.

## Canonical method / implementation / source

- [ ] The entity boundary and family placement are documented.
- [ ] Source, method/implementation row, hierarchy, mapping, evidence, and related relations are complete.
- [ ] Recommendation behavior changes have focused regression cases.
- [ ] The migration is registered in the deterministic build sequence.
- [ ] Release identity is changed only as part of an intentional dataset release.
- [ ] Human-readable content accompanies the structured addition or the missing content is explicitly tracked.

## Validation

Record the exact owning task and results in the PR. Run only the checks selected for the change surface;
the list below is a reference, not a requirement to run every command for every PR. Published
existing-entity content should normally use `ready content <content-id>` and `content-ready`.

- [ ] `uv run ruff check .`
- [ ] `uv run ruff format --check .`
- [ ] `uv run mypy src`
- [ ] focused or full `uv run pytest`
- [ ] `uv run optimization-compass verify-data`
- [ ] `uv run python scripts/verify_content.py`
- [ ] `uv run python scripts/verify_licensing.py`
- [ ] `uv run python scripts/rebuild_dataset.py --stage`
- [ ] `npm --prefix site run typecheck`
- [ ] `npm --prefix site run parity`
- [ ] `npm --prefix site test -- --run`
- [ ] `npm --prefix site run build`
- [ ] `npm --prefix site run test:e2e` when routes, journeys, playback, rendering, or accessibility change

## PR summary template

```markdown
## Change category

<!-- prose / content / Gallery / comparison / problem / canonical data / visualization / recommendation / release -->

## Changed IDs

- `...`

## Source and evidence

- `S...`: ...

## Behavior and product impact

- recommendation:
- View / Map:
- Case / Theater / Compare:
- Coverage / search / retrieval:
- release identity:

## Generated artifacts

- generated by:
- expected generated files:

## Validation

- `command`: result

## Limitations and follow-up

- ...
```
