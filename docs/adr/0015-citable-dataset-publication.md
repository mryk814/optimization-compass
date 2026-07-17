# ADR 0015: Citable dataset releases use a verified Zenodo archive

- Status: accepted
- Date: 2026-07-17
- Issue: #154
- Related: #149, #152, #155

## Context

Optimization Compass publishes a versioned CC BY 4.0 dataset whose SQLite, JSON, JSONL, CSV, Excel,
schema, report, site-data, manifest, and licenses share one deterministic release identity. GitHub
Releases provides complete immutable bundles and `data/releases/catalog.json` fixes their source commit,
tag, hashes, and byte size. A GitHub URL alone is not a complete scholarly citation contract, however,
and neither the README nor the browser UI should maintain version or citation strings independently.

The external service remains a distribution and citation surface. It must not become an authoring input,
runtime dependency, or replacement for the deterministic Git release tree.

Current official guidance was reviewed on 2026-07-17:

- [Zenodo records](https://help.zenodo.org/docs/deposit/about-records/) receive a DataCite DOI when
  published, and files normally move through draft to an immutable published record;
- [Zenodo versions](https://help.zenodo.org/docs/deposit/manage-versions/) create distinct records and
  persistent identifiers linked into one version series;
- [Zenodo creators](https://help.zenodo.org/docs/deposit/describe-records/creators/) and
  [licenses](https://help.zenodo.org/docs/deposit/describe-records/licenses/) are explicit citation and
  reuse metadata;
- the [Zenodo REST API](https://developers.zenodo.org/) documents deposit, file, publish, and new-version
  operations, but its legacy license endpoint differs from the current production vocabulary endpoint;
- [Hugging Face dataset repositories](https://huggingface.co/docs/hub/datasets-overview),
  [dataset cards](https://huggingface.co/docs/hub/datasets-cards), and
  [DOIs](https://huggingface.co/docs/hub/doi) offer useful discovery and exploration, but add a second
  mutable Git-backed publication surface and a separate DOI lifecycle;
- Citation File Format [schema 1.2.0](https://github.com/citation-file-format/citation-file-format/blob/main/schema-guide.md)
  supports datasets, exact versions, release dates, commits, artifact repositories, and DOIs.

An unrelated Zenodo record already uses the short title “Optimization Compass”. The dataset therefore
needs a distinctive publication title rather than assuming the project name is globally unique.

## Decision

Zenodo is the primary citable archive. Hugging Face is deferred as an optional discovery or viewer mirror;
it is not required to complete the archival contract. The public record title is
“Optimization Compass Optimization Atlas Dataset”. Dataset releases remain authored and validated in this
repository.

The first archive candidate is dataset 0.15.1. Later formally published dataset versions use Zenodo's
new-version flow so each version can be cited and verified independently. Historical GitHub Release
backfill from #155 does not imply that every historical version must also be deposited in Zenodo.

### Editable and generated authority

`data/releases/publication-authority.json` owns stable publication prose and metadata:

- title and Japanese/English abstracts;
- creator names already asserted by project metadata and license notices;
- keywords, language position, coverage limits, non-guarantees, license, and attribution;
- repository and Atlas URLs.

It does not own a dataset version, release date, commit, tag, hash, bundle URL, or DOI. Those values come
from the validated release catalog. `CITATION.cff`, `docs/dataset-card.md`, and external preparation files
are deterministic products of the two authorities. ORCID, affiliation, or split personal-name fields are
not inferred from an unsplit public name.

### Deposited artifact

Each Zenodo record receives exactly one canonical complete release bundle. The bundle already contains
all released formats, license/notice files, `bundle-index.json`, and the canonical release manifest. It is
verified locally against the catalog before any external operation. Uploading expanded duplicates would
create a second partial-file transaction and is therefore rejected.

The record metadata links the exact source commit, version tag, project site, release bundle, license, and
source audit. The audit remains linked at the immutable source commit instead of being copied as an
unmanifested release file.

### Offline preparation boundary

The first implementation is intentionally network-free:

1. strictly load publication authority and release catalog;
2. verify a caller-supplied bundle with the existing release verifier;
3. compare version, date, source commit, tag, database hash, manifest hash, bundle hash, byte count, and
   asset filename against the catalog;
4. write `CITATION.cff`, `DATASET_CARD.md`, and `publication-metadata.json` only to an explicit directory
   outside the repository;
5. treat an identical existing output as an idempotent replay and reject any difference or extra file.

Normal tests, staging, and metadata checks never use the network or external credentials.

### Future remote publication boundary

Remote write automation is a separate reviewed change. It must use Zenodo Sandbox before production,
because current production vocabulary endpoints and the legacy developer examples are not identical. It
must also:

- accept an explicit existing draft/record identity instead of blindly creating records on retry;
- reserve the version DOI before preparing DOI-bearing metadata;
- explicitly select CC BY 4.0 rather than relying on a platform default;
- upload only the verified bundle and re-download it for SHA-256 verification;
- require an explicit publish approval and leave failures as drafts;
- honor rate-limit and `Retry-After` responses;
- treat an exact published replay as success and any remote identity or hash difference as a stop;
- attach the verified version DOI to the local catalog only after anonymous post-publication verification.

Catalog attachment remains one-way: `archival: null` may become one exact descriptor; an identical replay
is allowed, while changing or removing a registered identifier is forbidden. Implementing that transition
must not weaken the existing release-entry immutability rule.

## Dataset card contract

The generated card states:

- included release formats and exact provenance;
- scope and evidence model;
- Japanese-first, English-term-aware language position from ADR 0013;
- catalog and recommendation coverage limits;
- CC BY 4.0 attribution and third-party rights boundary;
- that the Atlas does not guarantee optimality, feasibility, robustness, safety, universal ranking, or
  real-world performance.

README and future Data UI citation links must consume generated catalog/publication metadata. They may not
introduce hand-maintained current versions or DOI strings.

## Failure and correction policy

Missing creators, a non-CC-BY-4.0 dataset license, malformed URLs, unknown fields, bundle/catalog drift,
repository-local output, an unsupported archival identifier, or non-identical replay stops preparation
without a partial result. A published remote mismatch is never overwritten. It is corrected with a new
dataset version and DOI.

Actual publication stops until creator citation spelling and any optional ORCID or affiliation are
confirmed, Sandbox proves the API and license contract, the remote bundle hash matches, and #155 catalog
or Data UI changes have been reconciled.

## Consequences

The repository gains useful citation metadata before external credentials or a DOI exist. Current GitHub
release users can cite an exact version, while a future DOI can be added without manually rewriting version
facts. External failure cannot redefine a release, and ordinary contributor or staging workflows remain
offline. The remaining #154 acceptance criteria—one public durable record, verified remote bytes, one-way
catalog attachment, and public Data UI links—remain explicitly external follow-up work.
