# Dependency and supply-chain maintenance

Optimization Compass has one validated CI and Pages workflow. Dependency updates do not bypass it:
focused Python 3.12 smoke tests, site tests, recommendation parity, the production build, dataset
checks, and the Pages artifact gate all run on Dependabot pull requests.

## Automated updates

`.github/dependabot.yml` opens grouped weekly updates on Monday in `Asia/Tokyo`:

| Ecosystem | Directory | Group | Time |
|---|---|---|---|
| uv / Python | `/` | `python-dependencies` | 09:00 |
| npm | `/site` | `site-dependencies` | 09:15 |
| GitHub Actions | `/` | `github-actions` | 09:30 |

Review and merge security updates promptly after the validated workflow passes. Merge routine grouped
updates at least monthly. Do not auto-merge a major update or an update that changes generated data,
recommendations, browser behavior, or license terms. Read the upstream release notes and inspect both
lockfile changes before approval.

## CI gates

The `Validate and build Pages artifact` job enforces the following supply-chain contract:

1. `uv lock --check` rejects drift between `pyproject.toml` and `uv.lock`.
2. `npm install --package-lock-only --ignore-scripts` followed by a clean diff rejects drift between
   `site/package.json` and `site/package-lock.json`.
3. `pip-audit --skip-editable` rejects known vulnerabilities in the environment installed from the
   frozen uv lock; the editable project itself is excluded.
4. `npm audit --audit-level=high` rejects high and critical npm vulnerabilities.
5. `scripts/verify_workflow_pins.py` rejects mutable external action references and missing version
   comments. Every external action must use a full 40-character commit SHA with an exact release
   comment such as `# v7.0.0`.
6. `scripts/dependency_report.py` emits `dependency-license-inventory`, a 30-day CI artifact containing
   Python environment and npm lockfile package names, versions, and declared licenses.

The workflow action revisions were verified against their upstream release tags on 2026-07-15:

| Action | Version comment | Immutable commit |
|---|---|---|
| `actions/checkout` | `v7.0.0` | `9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0` |
| `astral-sh/setup-uv` | `v8.3.2` | `11f9893b081a58869d3b5fccaea48c9e9e46f990` |
| `actions/setup-node` | `v7.0.0` | `820762786026740c76f36085b0efc47a31fe5020` |
| `actions/upload-artifact` | `v7.0.1` | `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` |
| `actions/upload-pages-artifact` | `v5.0.0` | `fc324d3547104276b827a68afc52ff2a11cc49c9` |
| `actions/deploy-pages` | `v5.0.0` | `cd2ce8fcbc39b97be8ca5fce6e763baed58fa128` |
| `actions/setup-python` | `v6.3.0` | `ece7cb06caefa5fff74198d8649806c4678c61a1` |

The report is an inventory for review, not a legal conclusion. A dependency with `UNKNOWN` metadata or
new/incompatible terms requires manual review before merge. Project data/content licensing remains
governed by [`docs/licensing.md`](licensing.md).

## Required GitHub repository settings

These settings cannot be committed as files. A repository administrator must configure them once:

1. **Settings → Security → Code security and analysis**
   - enable Dependency graph;
   - enable Dependabot alerts;
   - enable Dependabot security updates;
   - enable private vulnerability reporting.
2. **Settings → Rules → Rulesets** for the default branch
   - require pull requests before merging;
   - require the `Validate and build Pages artifact` status check;
   - require branches to be up to date before merging;
   - prevent bypass except for documented emergency recovery.
3. Keep Actions permissions at **read repository contents** by default. The deploy job alone receives
   `pages: write` and `id-token: write`.

After enabling the settings, open the Security tab and confirm that the dependency graph recognizes
`uv.lock` and `site/package-lock.json`, the private reporting form opens, and the next Dependabot
schedule creates grouped PRs for all three ecosystems.

## Manual verification

Run the same local checks before changing the workflow or dependency policy:

```bash
uv lock --check
uv sync --frozen --all-extras --all-groups
uv run --frozen python scripts/verify_workflow_pins.py
uv run --frozen pip-audit --skip-editable
npm --prefix site install --package-lock-only --ignore-scripts
git diff --exit-code -- site/package-lock.json
npm --prefix site audit --audit-level=high
uv run --frozen python scripts/dependency_report.py \
  --node-lock site/package-lock.json \
  --output dependency-reports/dependency-licenses.json
```
