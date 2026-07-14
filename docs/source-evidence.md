# Source evidence and freshness

`sources` and `evidence_links` in the released SQLite database are the authority for public
evidence metadata. `site/public/data/sources.json` is a generated, versioned index; it must not be
edited by hand. The site exposes it at `/sources` and `/sources/:sourceId`. Diagnose, Method,
Learn, Gallery, Map, and Trace render source links to those detail pages. Each detail page links
back to resolvable method, implementation, rule, or related targets.

## Export and CI checks

Run the normal exporter after changing authority data:

```powershell
uv run optimization-compass export-site-data --output site/public/data
git diff --exit-code -- site/public/data
```

The export fails when a source URL is not an absolute HTTP(S) URL, when an evidence target cannot
be resolved, or when the source/evidence contract is inconsistent. CI also runs the local-only
health report, which checks URL format, source references, freshness dates, and implementation
version/maintenance/license candidates without accessing the network:

```powershell
uv run python scripts/source_health.py --output source-health-report
```

## Freshness policy

`src/optimization_compass/evidence.py` is the policy authority and the generated source index
includes the same values.

| Source type | Maximum age |
| --- | ---: |
| official documentation, issue, repository, vendor manual | 90 days |
| standard | 365 days |
| original paper, textbook, university material | 730 days |

Implementation release, maintenance, and license metadata has a 90-day review window. Explicit
`unknown` values are reported as candidates rather than guessed. This is why the existing CHK010
advisory remains honest: 25 implementation releases have no source-backed value yet.

## Scheduled link report

The weekly `Source and metadata health` workflow runs:

```powershell
uv run python scripts/source_health.py --check-network --output source-health-report
```

It uploads JSON and Markdown artifacts. It never commits, opens an issue, changes the database, or
rewrites generated data. Classification is deliberately conservative:

- 404 and 410 are confirmed broken links.
- TLS certificate failures are reported separately.
- Redirects are advisories, including possible official-domain changes.
- 429, 408, 425, and common 5xx responses are retried with backoff and remain rate-limit or
  transient advisories, not broken links.
- 403 is `access_restricted`, not broken.
- A rejected HEAD request is retried with a one-byte GET request.
- DNS, timeout, and connection failures need three failed attempts and remain transient.

## Manual verification

1. Download the latest workflow artifact and review `report.md` first.
2. Open redirected, broken/TLS, and stale candidates in a normal browser.
3. Confirm the official owner/domain and the exact version, maintenance status, license, or access
   terms. Do not infer a license from a repository host or a package manager.
4. Update only the canonical SQLite/migration/seed authority, including `accessed_date` or
   `last_verified` after a human check.
5. Rebuild the complete release, inspect `/sources/:sourceId` and at least one backlink, then run
   all CI-equivalent checks before publication.
