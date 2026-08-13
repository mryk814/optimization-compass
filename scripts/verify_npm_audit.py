"""Reject every high or critical npm audit finding."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--report", required=True, type=Path)
    return result


def high_or_critical(vulnerability: dict[str, Any]) -> bool:
    return vulnerability.get("severity") in {"high", "critical"}


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
    if findings:
        names = ", ".join(sorted(findings))
        raise SystemExit(f"npm audit found high/critical vulnerabilities: {names}")


if __name__ == "__main__":
    main()
