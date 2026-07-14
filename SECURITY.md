# Security Policy

## Supported versions

Security fixes are provided for the latest released minor line only.

| Application version | Supported |
|---|---|
| `0.1.x` | Yes |
| `< 0.1.0` | No |

Update this table when a new application minor line is released; only the newest line receives fixes.

## Reporting a vulnerability

Do not disclose vulnerability details in a public Issue. Use GitHub's
[private vulnerability reporting form](https://github.com/mryk814/optimization-compass/security/advisories/new)
instead. Include the affected version or commit, reproduction steps, impact, and any known mitigation.
The maintainer will acknowledge the report within seven days and coordinate validation, remediation,
and disclosure in the private advisory.

If the form is unavailable, report only that the private channel is unavailable in a public Issue;
do not include exploit details. The repository administrator must restore private vulnerability
reporting according to [`docs/dependency-maintenance.md`](docs/dependency-maintenance.md).

## Security boundaries

This project opens its bundled SQLite database read-only. Do not add an API that accepts arbitrary
SQL. Run data maintenance scripts only against trusted files.
