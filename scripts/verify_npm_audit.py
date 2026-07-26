"""Allow only the documented static-site exception among high/critical audit findings."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

EXPECTED_ADVISORY_URL = "https://github.com/advisories/GHSA-qwww-vcr4-c8h2"
EXPECTED_PACKAGES = {"react-router", "react-router-dom"}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--report", required=True, type=Path)
    return result


def high_or_critical(vulnerability: dict[str, Any]) -> bool:
    return vulnerability.get("severity") in {"high", "critical"}


def is_documented_static_site_exception(name: str, vulnerability: dict[str, Any]) -> bool:
    if name not in EXPECTED_PACKAGES:
        return False
    via = vulnerability.get("via", [])
    advisory_urls = {
        item.get("url")
        for item in via
        if isinstance(item, dict) and isinstance(item.get("url"), str)
    }
    return not advisory_urls or advisory_urls == {EXPECTED_ADVISORY_URL}


def main() -> None:
    args = parser().parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8-sig"))
    vulnerabilities = report.get("vulnerabilities")
    if not isinstance(vulnerabilities, dict):
        raise SystemExit("npm audit report has no vulnerabilities object")

    findings = {
        name: finding
        for name, finding in vulnerabilities.items()
        if isinstance(finding, dict) and high_or_critical(finding)
    }
    unexpected = {
        name: finding
        for name, finding in findings.items()
        if not is_documented_static_site_exception(name, finding)
    }
    if unexpected:
        names = ", ".join(sorted(unexpected))
        raise SystemExit(f"npm audit found unapproved high/critical vulnerabilities: {names}")
    if findings and set(findings) != EXPECTED_PACKAGES:
        names = ", ".join(sorted(findings))
        raise SystemExit(
            f"npm audit exception no longer matches the documented package set: {names}"
        )


if __name__ == "__main__":
    main()
