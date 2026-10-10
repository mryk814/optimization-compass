# Dependency maintenance

The repository no longer contains Dependabot configuration. The PR-only validation workflow checks
locked dependency installation and immutable action pins. Dependency updates and vulnerability
audits must still be run explicitly; there is no grouped weekly update schedule or automatic
vulnerability audit in this checkout.

Review upstream release notes and both lockfile changes. Changes to generated data, recommendations,
browser behavior, or license terms need the matching validation task before merging.

## Local checks

```bash
uv lock --check
uv sync --frozen --all-extras --all-groups
uv run --frozen pip-audit --skip-editable
npm --prefix site ci
npm --prefix site audit --audit-level=high --json > /tmp/compass-npm-audit.json
uv run --frozen python scripts/verify_npm_audit.py --report /tmp/compass-npm-audit.json
uv run --frozen python scripts/dependency_report.py \
  --node-lock site/package-lock.json \
  --output dependency-reports/dependency-licenses.json
```

Use a suitable temporary path on your platform. `npm audit` returns nonzero for findings; retain and
inspect its report rather than masking the failure. The verifier rejects every high or critical
finding without an advisory allowlist. `pip-audit --skip-editable` checks installed dependencies,
not this project's source.

The dependency report is an inventory of Python and npm packages, versions, and declared licenses,
not a legal conclusion. `UNKNOWN` metadata or changed terms require review under
[`licensing.md`](licensing.md). The workflow-pin validator checks `.github/workflows` by default and
also accepts an explicit workflow directory.
